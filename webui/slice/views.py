# pylint: disable=R0904
"""
Views for slice app
"""

from django.http import HttpResponseBadRequest, StreamingHttpResponse
from django.views.generic import ListView, UpdateView, CreateView, View
from django.views.generic.base import TemplateResponseMixin
from django.views.generic.detail import BaseDetailView

from webui.slice.forms import SlicerForm
from webui.slice.models import Slicer


class SlicerListView(ListView):
    """
    ListView for a Slicer
    """
    model = Slicer

    template_name = 'slice/slicer/list.html'


class SlicerCreateView(CreateView):
    """
    CreateView for a Slicer
    """
    model = Slicer
    form_class = SlicerForm

    template_name = 'slice/slicer/create.html'

    def get_initial(self):
        initial = super(SlicerCreateView, self).get_initial()
        query_string = """
            PREFIX sd: <http://ontologies.venturi.eu/v1#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

            SELECT DISTINCT
            sd_group_all(?acheneID)
            sd_group_all(?provenance)
            sd_group_one(?name)
            sd_group_one(?description)
            sd_from()
            WHERE {
                GRAPH ?provenance {
                    ?resource rdf:type sd:Something .
                    ?resource sd:acheneID ?acheneID .
                    OPTIONAL { ?resource sd:name ?name } .
                    OPTIONAL { ?resource sd:description ?description } .
                }
            } GROUP BY ?resource
        """
        # This is to remove left spaces, pay attention if changing indent
        initial['query_string'] = "\n".join(
            line[12:] for line in query_string.split("\n")[1:]
        )
        return initial


class SlicerUpdateView(UpdateView):
    """
    UpdateView for a Slicer
    """
    model = Slicer
    form_class = SlicerForm

    template_name = 'slice/slicer/update.html'


class SlicerQueryView(View, TemplateResponseMixin):
    """
    View that accepts a SPARQL query in POST and returns an HTML table
    with the query result
    """
    template_name = 'slice/slicer/query.html'

    def post(self, request):
        """
        Gets a query and runs it
        """
        from webui.slice.utils import get_cleaned_sliced_data

        query = request.POST.get('query')
        fields = request.POST.get('fields')
        if not query or not fields:
            return HttpResponseBadRequest('Missing query or fields')

        try:
            results = get_cleaned_sliced_data(query, fields, with_header=True)
            header = next(results)
            results = list(results)
        except Exception, e:
            return HttpResponseBadRequest(str(e))

        context = {
            'header': header,
            'results': results,
        }
        return self.render_to_response(context)


class SlicerDumpView(BaseDetailView):
    """
    Returns a geojson from the slicer sparql query
    """
    model = Slicer

    def render_to_response(self, context):  # pylint: disable=R0201
        """
        Called by GET, returns a streaming response.
        """
        from .utils import dicts2geojson, get_cleaned_sliced_data

        obj = context['object']
        data = get_cleaned_sliced_data(obj.query_string, obj.fields)
        data = ({k: v for k, v in row.iteritems() if v is not None}
                for row in data)
        response = StreamingHttpResponse(
            dicts2geojson(data),
            content_type='application/x-download',
            # content_type='application/json',
        )
        response['Content-Disposition'] = 'attachment;filename=slice.geojson'

        return response


# pylint: disable=E1120,C0103
slicer_list = SlicerListView.as_view()
slicer_create = SlicerCreateView.as_view()
slicer_update = SlicerUpdateView.as_view()
slicer_query = SlicerQueryView.as_view()
slicer_dump = SlicerDumpView.as_view()
# pylint: enable=E1120,C0103
