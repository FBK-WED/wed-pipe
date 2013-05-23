"""
Views for cnmain
"""

from django.contrib.auth.views import login, logout
from django.views.generic import TemplateView

from util import rreplace
from webui.cnmain.utils import get_virtuoso_endpoint


class IndexView(TemplateView):
    """ the index
    """
    template_name = 'cnmain/index.html'

    def get_context_data(self, **kwargs):
        from django.db.models import F
        from webui.controller.models import ArchiveItem
        from webui.scheduler.models import Scheduler

        context = super(IndexView, self).get_context_data(**kwargs)
        context['unsynced_archiveitems'] = ArchiveItem.objects.exclude(
            file_hash=F('rule__hash')
        ).exclude(file_hash=None)

        context['scheduler_list'] = Scheduler.objects.\
            exclude(status=Scheduler.SUCCESS).\
            exclude(status=Scheduler.RUNNING)[:10]

        context['running_tasks'] = \
            Scheduler.objects.filter(status=Scheduler.RUNNING)

        return context


class SparqlView(TemplateView):
    """ a view for querying the sparql endpoint
    """
    template_name = 'cnmain/sparql.html'
    _sparql_endpoint = get_virtuoso_endpoint()
    _default_query = 'SELECT DISTINCT ?concept WHERE {[] a ?concept} LIMIT 100'

    def _get_sparql_query(self):
        """ get the sparql query and format it adding newlines and tabs
         where needed
        """
        query = self.request.GET.get('query', self._default_query)
        query = query.replace('{', '~{').replace('}', '~}')

        tab = '\t'
        while True:
            new_query = rreplace(query.replace('~{', '{\n' + tab, 1),
                                 '~}', '\n' + tab[:-1] + '}', 1)
            if query == new_query:
                break
            query = new_query
            tab += '\t'
        return query

    def get_context_data(self, **kwargs):
        context = super(SparqlView, self).get_context_data(**kwargs)
        context['sparql_endpoint'] = self._sparql_endpoint
        context['query'] = self._get_sparql_query()
        return context


# pylint: disable=E1120,C0103
index = IndexView.as_view()
login_view = login
logout_view = logout
sparql_view = SparqlView.as_view()
# pylint: enable=E1120,C0103
