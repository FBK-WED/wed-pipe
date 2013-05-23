# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'AggregatorArchiveItem.created'
        db.add_column('controller_aggregator_archiveitems', 'created',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True),
                      keep_default=False)

        # Adding field 'AggregatorArchiveItem.modified'
        db.add_column('controller_aggregator_archiveitems', 'modified',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True),
                      keep_default=False)

        # Adding field 'AggregatorArchiveItem.first_workflow_success'
        db.add_column('controller_aggregator_archiveitems', 'first_workflow_success',
                      self.gf('django.db.models.fields.DateTimeField')(null=True),
                      keep_default=False)

        # Adding field 'AggregatorArchiveItem.last_workflow_success'
        db.add_column('controller_aggregator_archiveitems', 'last_workflow_success',
                      self.gf('django.db.models.fields.DateTimeField')(null=True),
                      keep_default=False)

        # Adding field 'AggregatorArchiveItem.deleted'
        db.add_column('controller_aggregator_archiveitems', 'deleted',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'AggregatorArchiveItem.created'
        db.delete_column('controller_aggregator_archiveitems', 'created')

        # Deleting field 'AggregatorArchiveItem.modified'
        db.delete_column('controller_aggregator_archiveitems', 'modified')

        # Deleting field 'AggregatorArchiveItem.first_workflow_success'
        db.delete_column('controller_aggregator_archiveitems', 'first_workflow_success')

        # Deleting field 'AggregatorArchiveItem.last_workflow_success'
        db.delete_column('controller_aggregator_archiveitems', 'last_workflow_success')

        # Deleting field 'AggregatorArchiveItem.deleted'
        db.delete_column('controller_aggregator_archiveitems', 'deleted')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'controller.aggregator': {
            'Meta': {'ordering': "['name']", 'object_name': 'Aggregator'},
            'archiveitems': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'aggregators'", 'to': u"orm['controller.ArchiveItem']", 'through': u"orm['controller.AggregatorArchiveItem']", 'blank': 'True', 'symmetrical': 'False', 'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'entity_type': ('django.db.models.fields.URLField', [], {'default': "u'http://ontologies.venturi.eu/v1#'", 'max_length': '200'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '1024'}),
            'silk_rule': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'vertex_selector': ('django.db.models.fields.TextField', [], {'default': '"g.V(\'type\', \'sd$Something\')%limit.id.fill(m)"'})
        },
        u'controller.aggregatorarchiveitem': {
            'Meta': {'object_name': 'AggregatorArchiveItem', 'db_table': "'controller_aggregator_archiveitems'"},
            'aggregator': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['controller.Aggregator']"}),
            'archiveitem': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['controller.ArchiveItem']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'first_workflow_success': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_workflow_success': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'})
        },
        u'controller.archiveitem': {
            'Meta': {'ordering': "('pk',)", 'object_name': 'ArchiveItem'},
            'dataset': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'archive_items'", 'to': u"orm['controller.Dataset']"}),
            'file_hash': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'file_target': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'refine_projectid': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'refine_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'rule': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['controller.Rule']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'})
        },
        u'controller.dataset': {
            'Meta': {'ordering': "['source', 'name']", 'object_name': 'Dataset'},
            'bounding_box': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'csv_delimiter': ('django.db.models.fields.CharField', [], {'default': "','", 'max_length': '5'}),
            'csv_quotechar': ('django.db.models.fields.CharField', [], {'default': '\'"\'', 'max_length': '5'}),
            'curator': ('django.db.models.fields.CharField', [], {'default': "'Venturi'", 'max_length': '1024'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'download': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'encoding': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'license': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'other_meta': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'projection': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'datasets'", 'to': u"orm['controller.Source']"}),
            'update_rule': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '1024'})
        },
        u'controller.rule': {
            'Meta': {'object_name': 'Rule'},
            'hash': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rule': ('jsonfield.fields.JSONField', [], {'default': '{}'})
        },
        u'controller.source': {
            'Meta': {'ordering': "['name']", 'object_name': 'Source'},
            'description': ('django.db.models.fields.TextField', [], {}),
            'dispatcher': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'dispose_handler': ('django.db.models.fields.TextField', [], {'default': '"\\n    return ( \'2rdf-configuration\', { \'source\' : source.id } )\\n    "', 'blank': 'True'}),
            'hash_handler': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'init_handler': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'is_public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '1024'}),
            'scraper_api_key': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'scraper_name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'scraperwiki_url': ('django.db.models.fields.URLField', [], {'default': "'http://vpn.venturi.eu'", 'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'taggit.tag': {
            'Meta': {'object_name': 'Tag'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'})
        },
        u'taggit.taggeditem': {
            'Meta': {'object_name': 'TaggedItem'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'taggit_taggeditem_tagged_items'", 'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'taggit_taggeditem_items'", 'to': u"orm['taggit.Tag']"})
        }
    }

    complete_apps = ['controller']