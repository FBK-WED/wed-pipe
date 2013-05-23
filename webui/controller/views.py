# pylint: disable=E1120,C0103,R0904
"""
Custom views and Platform API definition.
"""

import logging
from urllib2 import URLError

import simplejson as json

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, \
    HttpResponseBadRequest, HttpResponseNotFound, HttpResponseNotAllowed
from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.views.generic.detail import SingleObjectMixin
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, UpdateView, CreateView, \
    DetailView, View, RedirectView, TemplateView
from django.views.generic.edit import FormMixin, ProcessFormView
from django.shortcuts import render

from webui.cnmain.utils import get_virtuoso_endpoint
from webui.controller.models import Source, Dataset, \
    ArchiveItem, Aggregator, AggregatorArchiveItem
from webui.scheduler.tasks import process_source, process_dataset, \
    process_aggregator
from webui.importer.importer import MetadataImporter
from webui.controller.forms import SourceForm, \
    DatasetForm, ArchiveItemRuleForm, AggregatorForm, \
    ArchiveItemAggregatorForm, AggregatorImportForm, SilkRuleFakeForm


logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


class PostRedirectView(RedirectView):
    def get(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(request.method)

    def post(self, request, *args, **kwargs):
        return super(PostRedirectView, self).get(request, *args, **kwargs)


class XMLViewMixin(object):
    """ a mixin for returning XML instead of HTML
    """
    xml_filename = None
    xml_download = True

    def dispatch(self, request, *args, **kwargs):
        """ handle and dispatch any request to this view
        """
        response = super(XMLViewMixin, self).dispatch(request, *args, **kwargs)
        response['Content-Type'] = response['Content-type']\
            .replace('text/html', 'text/xml')

        if self.xml_filename and \
                (self.xml_download is True
                 or self.xml_download in self.request.GET):
            filename = self.xml_filename
            if callable(filename):
                filename = filename()
            elif not isinstance(filename, basestring):
                raise Exception('wrong xml_filename type')
            response['Content-Disposition'] = 'attachment; filename="{}"' \
                                              ''.format(filename)

        return response


class SourceCreateView(CreateView):
    """ view for creating a Source
    """
    model = Source
    form_class = SourceForm
    template_name = 'controller/source/create.html'

    def get_initial(self):
        initial = super(SourceCreateView, self).get_initial()
        initial['user'] = self.request.user
        return initial

    def form_valid(self, form):
        messages.success(self.request, 'Source created correctly')
        return super(SourceCreateView, self).form_valid(form)


class SourceUpdateView(UpdateView):
    """ view for updating a Source
    """
    model = Source
    form_class = SourceForm
    template_name = 'controller/source/update.html'

    def form_valid(self, form):
        messages.success(self.request, 'Source updated correctly')
        return super(SourceUpdateView, self).form_valid(form)


class SourceDetailView(DetailView):
    """ detail view for a Source
    """
    model = Source
    template_name = 'controller/source/detail.html'


class SourceListView(ListView):
    """ list view for Sources
    """
    model = Source
    template_name = 'controller/source/list.html'
source_list = SourceListView.as_view()


class DatasetCreateView(CreateView):
    """ view for creating a dataset manually
    """
    model = Dataset
    form_class = DatasetForm
    template_name = 'controller/dataset/create.html'
    initial = {'other_meta': '{}'}

    # pylint: disable=E1003
    def form_valid(self, form):
        messages.success(self.request, 'Dataset created correctly')
        self.object = form.save(commit=False)
        self.object.source_id = self.kwargs['pk']
        self.object.save()
        # call the grandfather form_valid, instead of the father's one.
        return super(CreateView, self).form_valid(form)


class DatasetUpdateView(UpdateView):
    """ view for updating a dataset manually
    """
    model = Dataset
    form_class = DatasetForm
    template_name = 'controller/dataset/update.html'

    def form_valid(self, form):
        messages.success(self.request, 'Dataset updated correctly')
        return super(DatasetUpdateView, self).form_valid(form)


class DatasetDetailView(DetailView):
    """ the main view of a dataset
    """
    model = Dataset
    template_name = 'controller/dataset/detail.html'


@require_POST
def source_fetch_metadata(request, pk):
    """
    Update metadata action.
    Imports metadata from the configured source scraper.
    """
    source = Source.objects.get(pk=pk)

    source.datasets.all().delete()

    try:
        if not source.scraper_name:
            raise Exception('A scraper name must be specified.')
        report = MetadataImporter.read_metadata(source)
    except URLError:
        logger.exception('Timeout while accessing scraper data')
        messages.error(request, "Timeout while accessing scraper data")
    except Exception:
        logger.exception('Error while updating metadata')
        messages.error(request, "Error while updating metadata")
    else:
        messages.info(
            request,
            "{} metadata imported, {} errors".format(
                report['total'], report['errors']
            )
        )

    return redirect(source)


@require_POST
def source_upload_metadata(request, pk):
    """ allow to import datasets metadatada from a csv file
    """
    if not 'upload_csv_file' in request.FILES:
        return HttpResponseBadRequest()

    source = get_object_or_404(Source, pk=pk)
    filedata = request.FILES['upload_csv_file']
    if not filedata.name.endswith('.csv'):
        messages.error(request, 'The uploaded file is of the wrong type')
        return redirect(source)

    report = MetadataImporter.read_csv(source, filedata)

    if report['errors'] != 0:
        messages.error(
            request, "Created {0} out of {1} datasets, some errors "
                     "occurred: {2}".format(report['total'] - report['errors'],
                                            report['total'],
                                            report['report'])
        )
    else:
        messages.success(
            request, "Succesfully added {0} datasets".format(report['total'])
        )

    return redirect(source)


class GenericWorkflow(SingleObjectMixin, View):
    """ generic view for executing the workflow on an object (could be
    either a Source or a Dataset
    """
    task = None
    last_executed_required = False

    # pylint: disable=W0613
    def post(self, request, *args, **kwargs):
        """ handle http POST requests
        """
        import time
        from webui.scheduler.log import get_redis_key
        from webui.cnmain.utils import get_redis

        obj = self.get_object()
        args = [obj]
        if self.last_executed_required:
            args.append(int(request.POST.get('last_executed', 0)))
        task_kwargs = {}
        if request.POST.get('force') == 'true':
            task_kwargs['force'] = True
        task_id = str(self.task.delay(*args, **task_kwargs))
        redis_key = get_redis_key(task_id)
        red = get_redis()

        for _ in range(10):
            if red.exists(redis_key):
                return HttpResponseRedirect(
                    "{url}?{class_}={pk}".format(
                        url=reverse(
                            'scheduler_result_detail_view',
                            args=[task_id]
                        ),
                        class_=self.model.__name__.lower(),
                        pk=obj.pk
                    )
                )
            time.sleep(1)

        messages.error(
            request,
            'Something went wrong, ask Sentry (task id {} )..'.format(task_id)
        )
        return redirect(obj)


class ArchiveItemDetailView(DetailView, ProcessFormView, FormMixin):
    """
    Detail view for the ArchiveItem. If the ArchiveItem has a rule
    associated with it a form for editing the rule is displayed
    """
    model = ArchiveItem
    template_name = 'controller/archiveitem/detail.html'
    form_class = ArchiveItemRuleForm

    def get_context_data(self, *args, **kwargs):
        from refine.refine import IllegalRuleCheckSum

        obj = self.get_object()
        self.object = obj
        context_data = super(ArchiveItemDetailView, self)\
            .get_context_data(*args, **kwargs)
        context_data['form'] = self.get_form(self.form_class)
        context_data['object'] = obj
        context_data['aggregator_form'] = ArchiveItemAggregatorForm(obj)
        try:
            obj.get_refine_rule()
        except IllegalRuleCheckSum:
            context_data['out_of_sync'] = True
        else:
            context_data['out_of_sync'] = False

        return context_data

    def get_initial(self):
        obj = self.get_object()
        if obj.rule:
            return {
                "rule": json.dumps(obj.rule.rule, indent=2)
            }
        else:
            return {}

    def form_valid(self, form):
        obj = self.get_object()
        rule = obj.rule
        rule.rule = form.cleaned_data["rule"]
        rule.save(force_update=True)

        messages.success(self.request, 'Rule saved!')

        return redirect(obj)


class ArchiveItemCSVView(SingleObjectMixin, View):
    """
    View that returns a CSV with the ArchiveItem data
    """
    model = ArchiveItem

    # pylint: disable=W0613
    def get(self, request, *args, **kwargs):
        """ handle http GET requests
        """
        obj = self.get_object()
        csv_data = obj.data_csv()
        if not csv_data:
            return HttpResponseNotFound()

        filename = "{}.csv".format(obj.tablename)

        response = HttpResponse(csv_data, content_type='text/csv')
        response["Content-Disposition"] = \
            'attachment; filename="{}"'.format(filename)

        return response


class ArchiveItemRefineCreateView(SingleObjectMixin, PostRedirectView):
    """
    Creates a new project in Google Refine
    """
    model = ArchiveItem
    permanent = False

    def get_redirect_url(self, **kwargs):
        obj = self.get_object()
        obj.delete_refine_project()

        limit = self.request.POST.get("refine_limit")
        obj.create_refine_project(limit=limit)

        return obj.get_absolute_url()


class ArchiveItemRefineFetchView(SingleObjectMixin, PostRedirectView):
    """
    Updates the the ArchiveItem rule with data from Refine
    """

    model = ArchiveItem
    permanent = False

    def get_redirect_url(self, **kwargs):
        obj = self.get_object()
        obj.fetch_refine_rule()
        messages.success(self.request, 'Rule fetched from refine.')
        return obj.get_absolute_url()


class ArchiveItemRefineSyncView(SingleObjectMixin, PostRedirectView):
    """
    Sets the hash of the rule to the ArchiveItem file_hash
    This is useful if the ArchiveItem data changes but the rule is
    still valid
    """

    model = ArchiveItem
    permanent = False

    def get_redirect_url(self, **kwargs):
        obj = self.get_object()
        obj.sync_refine_rule()
        messages.success(self.request, 'Rule synced')
        return obj.get_absolute_url()


class ArchiveItemRefinePushView(SingleObjectMixin, PostRedirectView):
    """
    Pushes the ArchiveItem rule to Refine
    """

    model = ArchiveItem
    permanent = False

    def get_redirect_url(self, **kwargs):
        obj = self.get_object()
        obj.push_refine_rule()
        messages.success(self.request, 'Rule pushed')
        return obj.get_absolute_url()


class ArchiveItemMappedStatsView(SingleObjectMixin, TemplateView):
    """ a view for getting some stats about the data in the archiveitem
        mapped graph
    """
    model = ArchiveItem
    template_name = 'controller/archiveitem/mapped_stats.html'

    def get_context_data(self, **kwargs):
        from webui.cnmain.utils import get_virtuoso

        # pylint: disable=W0201
        self.object = archive_item = self.get_object()

        context = super(ArchiveItemMappedStatsView, self).get_context_data(
            **kwargs
        )
        context['archiveitems'] = []
        context['object'] = archive_item

        graph = archive_item.datagraph_mapped_name
        queries = []

        virtuoso = get_virtuoso()
        queries.append(('no_type', """
            SELECT (count(distinct ?resource) as ?count)
            WHERE
            {
                GRAPH <%s> {
                    ?resource ?b ?c .
                    OPTIONAL { ?resource rdf:type ?d . } .
                    FILTER (!BOUND(?d)) .
                }
            }
        """ % graph))

        queries.append(('poi_no_achene', """
            PREFIX sd:<http://ontologies.venturi.eu/v1#>

            SELECT (count(distinct ?resource) as ?count)
            WHERE
            {
                GRAPH <%s> {
                    ?resource rdf:type sd:POI .
                    OPTIONAL { ?resource sd:acheneID ?achene . } .
                    FILTER (!BOUND(?achene)) .
                }
            }
        """ % graph))

        queries.append(('poi_no_category', """
            PREFIX sd:<http://ontologies.venturi.eu/v1#>

            SELECT (count(distinct ?resource) as ?count)
            WHERE
            {
                GRAPH <%s> {
                    ?resource rdf:type sd:POI .
                    OPTIONAL { ?resource sd:category ?cat . } .
                    FILTER (!BOUND(?cat)) .
                }
            }
        """ % graph))

        queries.append(('poi_no_category', """
            PREFIX sd:<http://ontologies.venturi.eu/v1#>

            SELECT (count(distinct ?resource) as ?count)
            WHERE
            {
                GRAPH <%s> {
                    ?resource rdf:type sd:POI .
                    OPTIONAL { ?resource sd:category ?cat . } .
                    FILTER (!BOUND(?cat)) .
                }
            }
        """ % graph))

        queries.append(('poi_old_style_category', """
            PREFIX sd:<http://ontologies.venturi.eu/v1#>

            SELECT (count(distinct ?resource) as ?count)
            WHERE
            {
                GRAPH <%s> {
                    ?resource sd:category ?cat .
                    FILTER (0 = regex(?cat, "%s[0-9a-f]{40}")) .
                }
            }
        """ % (graph, settings.TRIPLE_DATABASE['PREFIXES']['sdres'])))

        queries.append(('poi_latlon_and_geom', """
            PREFIX sd:<http://ontologies.venturi.eu/v1#>

            SELECT (count(distinct ?resource) as ?count)
            WHERE
            {
                GRAPH <%s> {
                    { ?resource sd:latitude ?b }
                    UNION
                    { ?resource sd:longitude ?b }
                    UNION
                    { ?resource sd:geometry ?b }
                }
            }
        """ % graph))

        queries.append(('poi_without_any_geometry', """
            PREFIX sd:<http://ontologies.venturi.eu/v1#>

            SELECT (count(distinct ?resource) as ?count)
            WHERE
            {
                GRAPH <%s> {
                    ?resource a sd:POI .
                    OPTIONAL {?resource sd:geomPoint ?g1} .
                    OPTIONAL {?resource sd:geomComplex ?g2} .
                    FILTER (!BOUND(?g1))
                    FILTER (!BOUND(?g2))
                }
            }
        """ % graph))

        queries.append(('poi_point_without_extra_info', """
            PREFIX sd:<http://ontologies.venturi.eu/v1#>

            SELECT (count(distinct ?resource) as ?count)
            WHERE
            {
                GRAPH <%s> {
                    ?resource sd:geomPoint ?b .
                    OPTIONAL {?resource sd:geomPointProvenance ?prov} .
                    OPTIONAL {?resource sd:geomPointAccuracy ?acc} .
                    FILTER (!BOUND(?prov))
                    FILTER (!BOUND(?acc))
                }
            }
        """ % graph))

        queries.append(('poi_complex_without_extra_info', """
            PREFIX sd:<http://ontologies.venturi.eu/v1#>

            SELECT (count(distinct ?resource) as ?count)
            WHERE
            {
                GRAPH <%s> {
                    ?resource sd:geomComplex ?b .
                    OPTIONAL {?resource sd:geomComplexProvenance ?prov} .
                    OPTIONAL {?resource sd:geomComplexAccuracy ?acc} .
                    FILTER (!BOUND(?prov))
                    FILTER (!BOUND(?acc))
                }
            }
        """ % graph))

        queries.append(('poi_no_label', """
            SELECT (count(distinct ?resource) as ?count)
            WHERE
            {
                GRAPH <%s> {
                    ?resource rdf:type sd:POI .
                    OPTIONAL { ?resource rdfs:label ?label . } .
                    FILTER (!BOUND(?label)) .
                }
            }
        """ % graph))

        queries.append(('poi_no_name', """
            PREFIX sd:<http://ontologies.venturi.eu/v1#>

            SELECT (count(distinct ?resource) as ?count)
            WHERE
            {
                GRAPH <%s> {
                    ?resource rdf:type sd:POI .
                    OPTIONAL { ?resource sd:name ?name . } .
                    FILTER (!BOUND(?name)) .
                }
            }
        """ % graph))

        queries.append(('poi_no_isinnuts', """
            PREFIX sd:<http://ontologies.venturi.eu/v1#>

            SELECT (count(distinct ?resource) as ?count)
            WHERE
            {
                GRAPH <%s> {
                    ?resource rdf:type sd:POI .
                    OPTIONAL { ?resource sd:isInNUTS ?nuts . } .
                    FILTER (!BOUND(?nuts)) .
                }
            }
        """ % graph))

        queries.append(('poi_isinnuts_type', """
            PREFIX sd:<http://ontologies.venturi.eu/v1#>

            SELECT ?nutsType (count(distinct ?resource) AS ?cnt) WHERE {
                GRAPH <%s> { ?resource a sd:POI } .
                ?resource sd:isInNUTS ?nuts .
                OPTIONAL {?nuts a ?nutsType}
            } GROUP BY ?nutsType
        """ % graph))

        results = {
            key: virtuoso.client_query(query).fetchall()
            for key, query in queries
        }

        context.update(results)

        return context


class ArchiveItemAggregatorAddView(SingleObjectMixin, ProcessFormView,
                                   FormMixin):
    """
    View for adding an Aggregator to an ArchiveItem
    """

    model = ArchiveItem
    form_class = ArchiveItemAggregatorForm

    def get_form_kwargs(self):
        kwargs = super(ArchiveItemAggregatorAddView, self).get_form_kwargs()
        kwargs['archiveitem'] = self.get_object()
        return kwargs

    def form_valid(self, form):
        obj = self.get_object()
        aggregator = form.cleaned_data["aggregator"]
        AggregatorArchiveItem.objects.create(
            aggregator=aggregator,
            archiveitem=obj,
        )

        messages.success(self.request, 'Aggregator added!')

        return redirect(obj)

    def form_invalid(self, form):
        obj = self.get_object()
        messages.error(self.request, 'Invalid aggregator!')
        return redirect(obj)


class ArchiveItemAggregatorDelView(SingleObjectMixin, ProcessFormView,
                                   FormMixin):
    """
    View for deleting an Aggregator from an ArchiveItem
    """
    model = ArchiveItem
    form_class = ArchiveItemAggregatorForm

    def get_form_kwargs(self):
        kwargs = super(ArchiveItemAggregatorDelView, self).get_form_kwargs()
        kwargs['archiveitem'] = self.get_object()
        return kwargs

    def form_valid(self, form):
        obj = self.get_object()
        aggregator = form.cleaned_data["aggregator"]
        aggregator.aggregatorarchiveitem_set.filter(archiveitem=obj).delete()

        messages.success(self.request, 'Aggregator removed!')

        return redirect(obj)

    def form_invalid(self, form):
        obj = self.get_object()
        messages.error(self.request, 'Invalid aggregator!')
        return redirect(obj)


class AggregatorDetailView(DetailView):
    """
    Detail view for an Aggregator
    """
    model = Aggregator
    template_name = 'controller/aggregator/detail.html'

    def get_context_data(self, **kwargs):
        context = super(AggregatorDetailView, self).get_context_data(**kwargs)
        context['silk_rule_fake_form'] = SilkRuleFakeForm(instance=self.object)
        return context


class AggregatorCreateView(CreateView):
    """ view for creating a Source
    """
    model = Aggregator
    form_class = AggregatorForm
    template_name = 'controller/aggregator/create.html'

    def form_valid(self, form):
        messages.success(self.request, 'Aggregator created correctly')
        return super(AggregatorCreateView, self).form_valid(form)
aggregator_create = login_required(AggregatorCreateView.as_view())


class AggregatorUpdateView(UpdateView):
    """ view for updating an Aggregator
    """
    model = Aggregator
    form_class = AggregatorForm
    template_name = 'controller/aggregator/update.html'

    def form_valid(self, form):
        messages.success(self.request, 'Aggregator updated correctly')
        return super(AggregatorUpdateView, self).form_valid(form)
aggregator_update = login_required(AggregatorUpdateView.as_view())


class AggregatorListView(ListView):
    """ view for listing all Aggregators
    """
    model = Aggregator
    template_name = 'controller/aggregator/list.html'


class AggregatorExportView(XMLViewMixin, DetailView):
    """ view for exporting an XML file for creating a silk project about
    this aggregator
    """
    model = Aggregator
    template_name = 'controller/aggregator/silk_project.xml'
    xml_download = 'download'

    def get_context_data(self, **kwargs):
        context = super(AggregatorExportView, self).get_context_data(**kwargs)
        context.update({
            'sd_prefix': settings.TRIPLE_DATABASE['PREFIXES']['sdv1'],
            'sparql_endpoint': get_virtuoso_endpoint(),
            'mastergraph_host': settings.TRIPLE_DATABASE_MASTER['HOST'],
            'mastergraph_port':
            settings.TRIPLE_DATABASE_MASTER['KWARGS']['rexpro_port'],
            'mastergraph_graphname':
            settings.TRIPLE_DATABASE_MASTER['KWARGS']['graph'],
            'resource_namespace':
            settings.TRIPLE_DATABASE_MASTER['PREFIXES']['sdres'],
        })
        return context

    def xml_filename(self):
        return '{}-silk-project.xml'.format(
            self.object.name.lower().replace(' ', '-')
        )
aggregator_export = login_required(AggregatorExportView.as_view())


class AggregatorImportView(UpdateView):
    model = Aggregator
    form_class = AggregatorImportForm
    template_name = 'controller/aggregator/update.html'

    def form_valid(self, form):
        messages.success(self.request, 'Silk rule uploaded correctly')
        return super(AggregatorImportView, self).form_valid(form)
aggregator_import = login_required(AggregatorImportView.as_view())


@login_required
def refine_batch_edit(request):
    from .forms import RefineBatchEditForm

    filter_ = request.GET.get('filter')

    _globals = {}
    _locals = {}

    out_rules = []
    if filter_:
        code = """
def f(rule, instance, archiveitem):
    {}
        """.format('\n    '.join(filter_.split('\n')))
        code_obj = compile(code, '<string>', 'exec')
        exec(code_obj, _globals, _locals)

        for archiveitem in ArchiveItem.objects.all():
            instance = archiveitem.rule
            if not instance:
                continue
            rules = instance.rule
            for idx, rule in enumerate(rules):
                if _locals['f'](rule, instance, archiveitem):
                    out_rules.append({
                        'archiveitem': archiveitem,
                        'doc': json.dumps(rule, indent=4),
                        'index': idx
                    })
    form_data = {
        'filter': filter_
    }

    form = RefineBatchEditForm(initial=form_data)

    return render(request, 'controller/refine_batch_edit.html', {
        'form': form,
        'rules': out_rules
    })


source_workflow = GenericWorkflow.as_view(model=Source, task=process_source,
                                          last_executed_required=True)
dataset_workflow = GenericWorkflow.as_view(model=Dataset, task=process_dataset)
aggregator_workflow = GenericWorkflow.as_view(
    model=Aggregator, task=process_aggregator
)
source_create = login_required(SourceCreateView.as_view())
source_detail = SourceDetailView.as_view()
source_update = login_required(SourceUpdateView.as_view())
dataset_create = login_required(DatasetCreateView.as_view())
dataset_detail = DatasetDetailView.as_view()
dataset_update = login_required(DatasetUpdateView.as_view())
archiveitem_detail = ArchiveItemDetailView.as_view()
archiveitem_csv = ArchiveItemCSVView.as_view()
archiveitem_refine_create = ArchiveItemRefineCreateView.as_view()
archiveitem_refine_fetch = ArchiveItemRefineFetchView.as_view()
archiveitem_refine_sync = ArchiveItemRefineSyncView.as_view()
archiveitem_refine_push = ArchiveItemRefinePushView.as_view()
archiveitem_mapped_stats = ArchiveItemMappedStatsView.as_view()
archiveitem_aggregator_add = ArchiveItemAggregatorAddView.as_view()
archiveitem_aggregator_del = ArchiveItemAggregatorDelView.as_view()
aggregator_detail = AggregatorDetailView.as_view()
aggregator_list = AggregatorListView.as_view()
