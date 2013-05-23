""" management command for installing virtuoso extensions, such as store
procedures for dumping/loading graphs
"""
#pylint: disable=R0914,R0915
from django.core.management import BaseCommand

from webui.cnmain.utils import get_virtuoso


class Command(BaseCommand):
    """
    Load development data
    """
    def handle(self, *args, **options):
        """
        entry point
        """
        for instance in ('default', 'master'):
            print "Installing on virtuoso", instance
            virtuoso = get_virtuoso(instance)
            virtuoso.install_extensions()
            print
