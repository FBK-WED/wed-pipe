# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Source'
        db.create_table('controller_source', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=1024)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('scraperwiki_url', self.gf('django.db.models.fields.URLField')(default='http://vpn.venturi.fbk.eu', max_length=1024, null=True, blank=True)),
            ('scraper_name', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('scraper_api_key', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('dispatcher', self.gf('django.db.models.fields.TextField')(default="\n    if file.mime_by_ext == 'application/archive':\n        return recurse()\n\n    if file.mime_by_ext == 'text/csv' or file.mime_by_origin == 'text/csv':\n        if filerdf.path:\n            return [\n                ('rdf-configuration', { 'data' : filerdf.path, 'graph' : archive_item.datagraph_mapped_name }),\n                ('tab-configuration', { 'schema' : '', 'data' : file.path, 'tablename' : archive_item.tablename })\n            ]\n        else:\n            return ('tab-configuration', { 'schema' : '', 'data' : file.path, 'tablename' : archive_item.tablename })\n    else:\n        raise UnsupportedDatasetException('Unknown MIMEType')\n    ")),
            ('init_handler', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('dispose_handler', self.gf('django.db.models.fields.TextField')(default="\n    return ( '2rdf-configuration', { 'source' : source.id } )\n    ", blank=True)),
            ('hash_handler', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('controller', ['Source'])

        # Adding model 'Dataset'
        db.create_table('controller_dataset', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(related_name='datasets', to=orm['controller.Source'])),
            ('download', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=1024)),
            ('update_rule', self.gf('django.db.models.fields.CharField')(max_length=64, null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('curator', self.gf('django.db.models.fields.CharField')(default='Venturi', max_length=1024)),
            ('license', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True)),
            ('bounding_box', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('other_meta', self.gf('django.db.models.fields.TextField')(null=True)),
        ))
        db.send_create_signal('controller', ['Dataset'])

        # Adding model 'Rule'
        db.create_table('controller_rule', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('hash', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('rule', self.gf('jsonfield.fields.JSONField')(default={})),
        ))
        db.send_create_signal('controller', ['Rule'])

        # Adding model 'ArchiveItem'
        db.create_table('controller_archiveitem', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('dataset', self.gf('django.db.models.fields.related.ForeignKey')(related_name='archive_items', to=orm['controller.Dataset'])),
            ('file_target', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('file_hash', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('rule', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['controller.Rule'], unique=True, null=True, blank=True)),
            ('refine_projectid', self.gf('django.db.models.fields.CharField')(max_length=32, null=True, blank=True)),
            ('refine_url', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
        ))
        db.send_create_signal('controller', ['ArchiveItem'])

        # Adding model 'Aggregator'
        db.create_table('controller_aggregator', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=1024)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('controller', ['Aggregator'])

        # Adding M2M table for field archiveitems on 'Aggregator'
        db.create_table('controller_aggregator_archiveitems', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('aggregator', models.ForeignKey(orm['controller.aggregator'], null=False)),
            ('archiveitem', models.ForeignKey(orm['controller.archiveitem'], null=False))
        ))
        db.create_unique('controller_aggregator_archiveitems', ['aggregator_id', 'archiveitem_id'])


    def backwards(self, orm):
        # Deleting model 'Source'
        db.delete_table('controller_source')

        # Deleting model 'Dataset'
        db.delete_table('controller_dataset')

        # Deleting model 'Rule'
        db.delete_table('controller_rule')

        # Deleting model 'ArchiveItem'
        db.delete_table('controller_archiveitem')

        # Deleting model 'Aggregator'
        db.delete_table('controller_aggregator')

        # Removing M2M table for field archiveitems on 'Aggregator'
        db.delete_table('controller_aggregator_archiveitems')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'controller.aggregator': {
            'Meta': {'object_name': 'Aggregator'},
            'archiveitems': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['controller.ArchiveItem']", 'symmetrical': 'False'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '1024'})
        },
        'controller.archiveitem': {
            'Meta': {'object_name': 'ArchiveItem'},
            'dataset': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'archive_items'", 'to': "orm['controller.Dataset']"}),
            'file_hash': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'file_target': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'refine_projectid': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'refine_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'rule': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['controller.Rule']", 'unique': 'True', 'null': 'True', 'blank': 'True'})
        },
        'controller.dataset': {
            'Meta': {'object_name': 'Dataset'},
            'bounding_box': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'curator': ('django.db.models.fields.CharField', [], {'default': "'Venturi'", 'max_length': '1024'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'download': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'license': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'other_meta': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'datasets'", 'to': "orm['controller.Source']"}),
            'update_rule': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '1024'})
        },
        'controller.rule': {
            'Meta': {'object_name': 'Rule'},
            'hash': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rule': ('jsonfield.fields.JSONField', [], {'default': '{}'})
        },
        'controller.source': {
            'Meta': {'object_name': 'Source'},
            'description': ('django.db.models.fields.TextField', [], {}),
            'dispatcher': ('django.db.models.fields.TextField', [], {'default': '"\\n    if file.mime_by_ext == \'application/archive\':\\n        return recurse()\\n\\n    if file.mime_by_ext == \'text/csv\' or file.mime_by_origin == \'text/csv\':\\n        if filerdf.path:\\n            return [\\n                (\'rdf-configuration\', { \'data\' : filerdf.path, \'graph\' : archive_item.datagraph_mapped_name }),\\n                (\'tab-configuration\', { \'schema\' : \'\', \'data\' : file.path, \'tablename\' : archive_item.tablename })\\n            ]\\n        else:\\n            return (\'tab-configuration\', { \'schema\' : \'\', \'data\' : file.path, \'tablename\' : archive_item.tablename })\\n    else:\\n        raise UnsupportedDatasetException(\'Unknown MIMEType\')\\n    "'}),
            'dispose_handler': ('django.db.models.fields.TextField', [], {'default': '"\\n    return ( \'2rdf-configuration\', { \'source\' : source.id } )\\n    "', 'blank': 'True'}),
            'hash_handler': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'init_handler': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '1024'}),
            'scraper_api_key': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'scraper_name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'scraperwiki_url': ('django.db.models.fields.URLField', [], {'default': "'http://vpn.venturi.fbk.eu'", 'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'taggit.tag': {
            'Meta': {'object_name': 'Tag'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'})
        },
        'taggit.taggeditem': {
            'Meta': {'object_name': 'TaggedItem'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'taggit_taggeditem_tagged_items'", 'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'taggit_taggeditem_items'", 'to': "orm['taggit.Tag']"})
        }
    }

    complete_apps = ['controller']