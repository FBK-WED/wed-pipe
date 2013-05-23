import os
import sys

webuidir = os.path.join(os.path.dirname(__file__), '../..')
sys.path.insert(0, webuidir)
os.environ['DJANGO_SETTINGS_MODULE'] = 'webui.settings'

from refine.refine import apply_refine_on_file

from webui.controller.models import ArchiveItem


def main(args):
    archiveitem_id = args.archiveitem_id
    archiveitem = ArchiveItem.objects.get(pk=archiveitem_id)
    if archiveitem.rule:
        print 'Found rule for archiveitem [{!r}].'.format(
            archiveitem.file_target
        )

        out_file_turtle = args.out_file
        apply_refine_on_file(
            out_file_turtle,
            archiveitem,
        )
        print 'Refines rule applied correctly'
    else:
        print 'No rule found for archiveitem [{}].'.format(
            archiveitem.file_target
        )
