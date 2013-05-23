"""
Forms for slice app
"""

from django import forms
from django.utils.translation import ugettext as _

from django_ace import AceWidget
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Div, Field, HTML, Submit

from webui.slice.models import Slicer


class SlicerForm(forms.ModelForm):
    """ the modelform for a Slicer
    """

    class Meta:
        model = Slicer

        widgets = {
            'query_string': AceWidget(mode='groovy', theme='chrome')
        }

    # pylint: disable=E1002
    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()

        self.helper.html5_required = True
        self.helper.form_class = 'form-vertical'

        self.helper.layout = Layout(
            Fieldset(
                _('Slicer information'),
                Div(
                    Field('name', placeholder='Name'),
                    Field('query_string', placeholder='Query'),
                    Field('fields', placeholder='acheneID, provenance, ...',
                          css_class='span12'),
                    css_class='row-fluid span12'
                ),
                css_class='row-fluid create-form'
            ),
            Div(
                Div(
                    HTML('<span class="btn btn-success hide" id="run_query">'
                         'Run Query</span>'),
                    HTML('<a class="btn btn-success hide" href="./dump/">'
                         'Export</a>'),
                    HTML('<span class="btn" onClick="window.history.back()">'
                         'Cancel</span>'),
                    Submit('submit', 'Save'),
                    css_class='pull-right',
                    id="form-buttons"
                ),
                css_class='row-fluid',
            ),
        )
        super(SlicerForm, self).__init__(*args, **kwargs)
