# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Slicer.fields'
        db.add_column(u'slice_slicer', 'fields',
                      self.gf('django.db.models.fields.CharField')(default='acheneID, provenance', max_length=2000),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Slicer.fields'
        db.delete_column(u'slice_slicer', 'fields')


    models = {
        u'slice.slicer': {
            'Meta': {'object_name': 'Slicer'},
            'fields': ('django.db.models.fields.CharField', [], {'default': "'acheneID, provenance'", 'max_length': '2000'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '1024'}),
            'query_string': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['slice']