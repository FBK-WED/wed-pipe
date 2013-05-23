# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Slicer'
        db.create_table('slice_slicer', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=1024)),
            ('query_string', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('slice', ['Slicer'])


    def backwards(self, orm):
        # Deleting model 'Slicer'
        db.delete_table('slice_slicer')


    models = {
        'slice.slicer': {
            'Meta': {'object_name': 'Slicer'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '1024'}),
            'query_string': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['slice']