"""
originally from http://www.djangosnippets.org/snippets/828/ by dnordberg
"""
from optparse import make_option

from django.core.management.base import CommandError, BaseCommand


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-R', '--router', action='store',
                    dest='router', default=None,
                    help='Use this router-database other then defined '
                         'in settings.py'),
    )
    help = "Resets the virtuoso graph for this project."

    def get_graph_settings(self, *args, **options):
        self.router = options.get('router')

        return self.router in ('default', 'master')

    def handle(self, *args, **options):
        """
        Resets the virtuoso graph for this project.
        """
        from webui.cnmain.utils import get_virtuoso

        got_graph_settings = self.get_graph_settings(*args, **options)
        if not got_graph_settings:
            raise CommandError("The --router option is mandatory")
            return

        virtuoso = get_virtuoso(self.router)
        cleared = virtuoso.clear_regex(r'.*')

        print "Cleared {} graphs".format(cleared)
