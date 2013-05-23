"""
Load development data
"""
#pylint: disable=R0914,R0915
from django.conf import settings
from django.core.management import BaseCommand
from util import get_test_file
from webui.cnmain.models.factories import AdminFactory
from webui.controller.models.factories import SourceFactory, DatasetFactory, \
    ArchiveItemFactory, RuleFactory, AggregatorFactory
from webui.controller.models import AggregatorArchiveItem


class Command(BaseCommand):
    """
    Load development data
    """
    def handle(self, *args, **options):
        """
        entry point
        """
        from django.contrib.sites.models import Site

        site = Site.objects.get()
        site.name = 'controller'
        site.domain = 'localhost:8001'
        site.save()

        AdminFactory()

        trentinocultura = SourceFactory(
            name='trentinocultura',
            description='description description',
            scraper_name='trentinocultura',
            scraper_api_key='',
        )

        DatasetFactory(
            source=trentinocultura,
            name='Trentinocultura agenda',
            url='http://www.trentinocultura.net/asp_cat/main.asp?IDProspettiva'
                '=35&SearchType=AGENDA_SEARCH&Pag=%d&TipoVista=AGENDA&cmd=new',
            description='Eventi in Trentino',
            download='scraper:trentinocultura:trentinocultura',
            curator='Federico Scrinzi',
            license='All rights reserved',
            other_meta='{}',
            bounding_box='10.3817591116112,45.6730626059259,'
                         '12.4775685651704,47.0917759206089',
        )

        ingiro_local = SourceFactory(
            name='in-giro (locale)',
            description='i dati dello scraper di in-giro, ma in locale (file '
                        'webui.scheduler.tests.data/in-giro.zip) utile per'
                        'test, ma anche per boh, altro? =)',
        )

        DatasetFactory(
            source=ingiro_local,
            name='eventi-e-poi-ingiro',
            url='http://in-giro.net',
            description='Eventi e POI presi da in-giro',
            download='http://testserver/in-giro.zip',
            curator='Ciccio Pasticcio',
            license='All rights reserved',
            other_meta='{}',
        )

        bgg_source = SourceFactory(
            name='BoardGameGeek (test)',
            description='pochi dati per testare il matching su silk'
        )

        bgt_source = SourceFactory(
            name='BoardGameTournament (test)',
            description='pochi dati per testare il matching su silk',
        )

        bgg_dataset = DatasetFactory(
            source=bgg_source,
            name='boardgamegeek-games',
            url='http://boardgamegeek.com',
            description='Lista di boardgames presi da boardgamegeek',
            download='https://dl.dropbox.com/u/3435878/boardgamegeek.csv',
            curator='Stefano Parmesan',
            license='All rights reserved',
            other_meta='{}',
        )

        bgt_dataset = DatasetFactory(
            source=bgt_source,
            name='boardgametournament-games',
            url='http://boardgametournament.com',
            description='Lista di boardgames presi da boardgametournament',
            download='https://dl.dropbox.com/u/3435878/'
                     'boardgametournament.csv',
            curator='Stefano Parmesan',
            license='All rights reserved',
            other_meta='{}',
        )

        DatasetFactory(
            source=bgt_source,
            name='boardgametournament-games-xls',
            url='http://boardgametournament.com',
            description='Lista di boardgames presi da boardgametournament',
            download='https://dl.dropbox.com/u/3435878/'
                     'boardgametournament.xls',
            curator='Stefano Parmesan',
            license='All rights reserved',
            encoding="utf8",
            other_meta='{}',
        )

        DatasetFactory(
            source=bgt_source,
            name='boardgametournament-games-xlsx',
            url='http://boardgametournament.com',
            description='Lista di boardgames presi da boardgametournament',
            download='https://dl.dropbox.com/u/3435878/'
                     'boardgametournament.xlsx',
            curator='Stefano Parmesan',
            license='All rights reserved',
            encoding="utf8",
            other_meta='{}',
        )

        with open(get_test_file('boardgamegeek_refine_rules.json')) as fin:
            rule = ''.join(fin.readlines())
        bgg_archiveitem = ArchiveItemFactory(
            dataset=bgg_dataset,
            file_target='boardgamegeek.csv',
            file_hash='ea6ee15e9b052171db4f96743aa11425',
            rule=RuleFactory(
                hash="ea6ee15e9b052171db4f96743aa11425",
                rule=rule,
            )
        )

        with open(get_test_file('boardgametournament_refine_rules.json')) \
                as fin:
            rule = ''.join(fin.readlines())

        bgt_archiveitem = ArchiveItemFactory(
            dataset=bgt_dataset,
            file_target='boardgametournament.csv',
            file_hash='be864f716b6a7716f3b1c2254f4f5eea',
            rule=RuleFactory(
                hash="be864f716b6a7716f3b1c2254f4f5eea",
                rule=rule,
            )
        )

        with open(get_test_file('boardgames_aggregator_silk_rules.xml')) \
                as fin:
            rule = ''.join(fin.readlines())
        aggregator = AggregatorFactory(
            name='BoardGames',
            description='Un dataset di giochi da tavolo',
            silk_rule=rule,
            entity_type='{}BoardGame'.format(
                settings.TRIPLE_DATABASE['PREFIXES']['sdv1']
            ),
            vertex_selector="g.V('type', 'sd$BoardGame')%limit.id.fill(m)",
        )

        for archiveitem in (bgg_archiveitem, bgt_archiveitem):
            AggregatorArchiveItem.objects.create(
                aggregator=aggregator,
                archiveitem=archiveitem,
            )

        osm_source = SourceFactory(
            name='OSM (test)',
            description='pochi dati per testare lo slicer'
        )

        osm_dataset = DatasetFactory(
            source=osm_source,
            name='osm-dataset',
            url='http://openstreetmap.org',
            download='https://dl.dropbox.com/u/781790/osm-10nodes.csv',
            curator='Davide setti',
            license='CC PUCCI',
        )

        with open(get_test_file('osm-refine-rules.json')) as fin:
            rule = ''.join(fin.readlines())
        osm_archiveitem = ArchiveItemFactory(
            dataset=osm_dataset,
            file_target='osm-10nodes.csv',
            file_hash='e6f4a5c5f5fe12765f7b3ca04ab7a82d',
            rule=RuleFactory(
                hash="e6f4a5c5f5fe12765f7b3ca04ab7a82d",
                rule=rule,
            )
        )

        poi_aggregator = AggregatorFactory(
            name='POI',
            description='POI aggregator',
            entity_type=settings.TRIPLE_DATABASE['PREFIXES']['sdv1'] + 'POI',
            vertex_selector="g.V('type', 'sd$POI')%limit.id.fill(m)"
        )
        AggregatorArchiveItem.objects.create(
            aggregator=poi_aggregator,
            archiveitem=osm_archiveitem,
        )

        DatasetFactory(
            source=osm_source,
            name='Aeroporti',
            url='http://dati.trentino.it',
            description='Aeroporti del trentino, file SHP',
            download='http://testserver/aeroporti_tn.zip',
            curator='Federico Scrinzi',
            license='Open Data',
            other_meta='{}',
        )

        strange_source = SourceFactory(
            name='Strange or malformed (test)',
            description='pochi dati con valori strani tipo None',
        )

        DatasetFactory(
            source=strange_source,
            name='strange symbols',
            url='http://testserver/',
            description='Some strange symbols',
            download='http://testserver/strangesymbols.csv',
            curator='Federico Scrinzi',
            license='Open Data',
            other_meta='{}',
        )

        DatasetFactory(
            source=strange_source,
            name='looks like ascii',
            url='http://testserver/',
            description="file that looks like ascii but it's UTF8",
            download='http://testserver/lookslikeascii.csv',
            curator='Federico Scrinzi',
            license='Open Data',
            other_meta='{}',
        )
