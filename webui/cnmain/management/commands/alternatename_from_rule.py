import csv
from operator import itemgetter
import sys
import json

from django.conf import settings
from django.core.management import BaseCommand
from optparse import make_option
from webui.controller.models import ArchiveItem


class Command(BaseCommand):
    """
    Extract alternate names from Refine rules
    """
    option_list = BaseCommand.option_list + (
        make_option(
            '-a', '--archiveitem',
            action='store',
            dest='archiveitem',
            default=False,
            help='Extract alternate names from the archiveitem with the given '
                 'pk'
        ),
    )

    def handle(self, *args, **options):
        """
        entry point
        """
        results = set()
        item_pk = options.get('archiveitem')
        if item_pk:
            items = [ArchiveItem.objects.get(pk=item_pk)]
        else:
            items = ArchiveItem.objects.all()
        for archiveitem in items:
            if not archiveitem.rule:
                continue
            for op in archiveitem.rule.rule:
                try:
                    op = op['operation']
                except KeyError:
                    continue
                if 'match' in op:
                    original_name = op['similarValue']
                    matched_id = op['match']['id']
                    matched_name = op['match']['name']

                    if not matched_id.startswith(settings.URI_BASE_PREFIX):
                        continue

                    results.add(
                        json.dumps([original_name, matched_id, matched_name])
                    )
        csv_writer = csv.writer(sys.stdout)
        results = [
            [v.encode('utf-8') for v in json.loads(row)]
            for row in results
        ]
        for row in sorted(results, key=itemgetter(0)):
            csv_writer.writerow(row)
