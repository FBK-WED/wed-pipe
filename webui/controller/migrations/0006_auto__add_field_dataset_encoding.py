# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Dataset.encoding'
        db.add_column(u'controller_dataset', 'encoding',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=32, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Dataset.encoding'
        db.delete_column(u'controller_dataset', 'encoding')


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
            'Meta': {'object_name': 'Aggregator'},
            'archiveitems': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'aggregators'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['controller.ArchiveItem']"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'entity_type': ('django.db.models.fields.URLField', [], {'default': "u'http://ontologies.venturi.eu/v1#'", 'max_length': '200'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '1024'}),
            'silk_rule': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        u'controller.archiveitem': {
            'Meta': {'object_name': 'ArchiveItem'},
            'dataset': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'archive_items'", 'to': u"orm['controller.Dataset']"}),
            'file_hash': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'file_target': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'refine_projectid': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'refine_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'rule': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['controller.Rule']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'})
        },
        u'controller.dataset': {
            'Meta': {'object_name': 'Dataset'},
            'bounding_box': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'curator': ('django.db.models.fields.CharField', [], {'default': "'Venturi'", 'max_length': '1024'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'download': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'encoding': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'license': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'other_meta': ('django.db.models.fields.TextField', [], {'null': 'True'}),
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
            'Meta': {'object_name': 'Source'},
            'description': ('django.db.models.fields.TextField', [], {}),
            'dispatcher': ('django.db.models.fields.TextField', [], {'default': '\'\\n    if file.mime_by_ext == \\\'application/archive\\\':\\n        return recurse()\\n\\n    actions = []\\n\\n    shp = file.path.endswith(".shp")\\n    csv = (file.mime_by_ext == \\\'text/csv\\\' or file.mime_by_origin == \\\'text/csv\\\')\\n\\n    if shp:\\n        actions.append(\\n            (\\\'geo-configuration\\\', {\\n             \\\'data\\\': file.path,\\n             \\\'output\\\': file.path + ".converted.csv",\\n             \\\'encoding\\\': archive_item.dataset.encoding})\\n        )\\n\\n    if shp or csv:\\n        actions.append(\\n            (\\\'tab-configuration\\\', {\\n             \\\'schema\\\' : \\\'\\\',\\n             \\\'data\\\' : file.path,\\n             \\\'tablename\\\' : archive_item.tablename,\\n             \\\'encoding\\\': archive_item.dataset.encoding })\\n        )\\n\\n        if archive_item.rule:\\n            actions.append(\\n                (\\\'refine-configuration\\\', {\\n                 \\\'archiveitem_id\\\' : str(archive_item.pk),\\n                 \\\'out_file\\\': file.path + \\\'.turtle\\\'})\\n            )\\n\\n            actions.append(\\n                (\\\'rdf-configuration\\\', {\\n                 \\\'data\\\' : file.path + \\\'.turtle\\\',\\n                 \\\'graph\\\' : archive_item.datagraph_mapped_name })\\n            )\\n\\n        return actions\\n    else:\\n        raise UnsupportedDatasetException(\\\'Unknown MIMEType\\\')\\n    \''}),
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