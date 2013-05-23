# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Scheduler.dataset'
        db.delete_column('scheduler_scheduler', 'dataset_id')

        # Adding field 'Scheduler.content_type'
        db.add_column('scheduler_scheduler', 'content_type',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['contenttypes.ContentType']),
                      keep_default=False)

        # Adding field 'Scheduler.object_id'
        db.add_column('scheduler_scheduler', 'object_id',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=1),
                      keep_default=False)


    def backwards(self, orm):
        # Adding field 'Scheduler.dataset'
        db.add_column('scheduler_scheduler', 'dataset',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['controller.Dataset']),
                      keep_default=False)

        # Deleting field 'Scheduler.content_type'
        db.delete_column('scheduler_scheduler', 'content_type_id')

        # Deleting field 'Scheduler.object_id'
        db.delete_column('scheduler_scheduler', 'object_id')


    models = {
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'scheduler.scheduler': {
            'Meta': {'ordering': "('-modified', '-created')", 'object_name': 'Scheduler'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'error': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_params': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'logger_name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'out_params': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        }
    }

    complete_apps = ['scheduler']
