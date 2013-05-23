from textwrap import dedent

from django import forms
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.forms import ModelForm, TextInput
from django.utils.translation import ugettext as _

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset, Layout, Submit, Div, Field, HTML
from coffin.template.loader import render_to_string
from django_ace import AceWidget
from jsonfield.fields import JSONFormField

from webui.controller.models import Source, Dataset, Aggregator, \
    AggregatorArchiveItem


class ScraperCompleter(TextInput):
    def __init__(self, attrs=None, scraperwiki_field='scraperwiki_url'):
        self.scraperwiki_field = scraperwiki_field
        super(ScraperCompleter, self).__init__(attrs)

    def render(self, name, value, attrs=None):
        if value is None:
            value = ''

        return render_to_string(
            'controller/forms/widgets/scraper_completer.html',
            {
                'name': name,
                'value': value,
                'scraperwiki_field': self.scraperwiki_field,
            }
        )


class SourceForm(ModelForm):
    """ the modelform for a Source
    """
    class Meta:
        model = Source

        widgets = {
            'description': forms.Textarea(attrs={'rows': '3'}),
            'scraper_name': ScraperCompleter(),
            'dispatcher': AceWidget(mode='python', theme='chrome'),
            'init_handler': AceWidget(mode='python', theme='chrome'),
            'dispose_handler': AceWidget(mode='python', theme='chrome'),
            'hash_handler': AceWidget(mode='javascript', theme='chrome'),
        }

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()

        self.helper.html5_required = True
        self.helper.form_class = 'form-horizontal'

        self.helper.layout = Layout(
            Fieldset(
                _('Source information'),
                Div(
                    Field('name', placeholder='Name'),
                    Field('is_public', placeholder='Public?'),
                    Field('description', placeholder='Description'),
                    Field(
                        'tags',
                        placeholder='A comma-separated list of tags',
                    ),
                    'user',
                    css_class='span10 offset1'
                ),
                css_class='row-fluid create-form'
            ),
            Fieldset(
                _('Dataset(s) configuration'),
                Div(
                    Field(
                        'scraperwiki_url',
                        placeholder='http://vpn.venturi.fbk.eu'
                    ),
                    Field(
                        'scraper_name',
                        placeholder='Scraper name'
                    ),
                    Field(
                        'scraper_api_key',
                        placeholder='mettere un esempio di key'
                    ),
                    css_class='span10 offset1',
                ),
                css_class='row-fluid create-form'
            ),
            Fieldset(
                _('Dispatcher and handlers'),
                'dispatcher',
                'init_handler',
                'dispose_handler',
                'hash_handler',
                css_id='dispatcher-handlers',
            ),
            Div(
                HTML('<hr>'),
                Div(
                    HTML('<span class="btn" onClick="window.history.back()">'
                         'Cancel</span>'),
                    Submit('submit', 'Save'),
                    css_class='pull-right'
                ),
                css_class='row-fluid',
            ),
        )

        super(SourceForm, self).__init__(*args, **kwargs)


class DatasetForm(forms.ModelForm):
    """ the modelform for a Dataset
    """
    class Meta:
        model = Dataset
        exclude = ['source', ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': '3'}),
            'other_meta': AceWidget(mode='python', theme='chrome'),
        }

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()

        self.helper.html5_required = True
        self.helper.help_text_inline = True
        self.helper.form_class = 'form-horizontal'

        self.helper.layout = Layout(
            Fieldset(
                _('Dataset information'),
                Div(
                    Field('name', placeholder='Name'),
                    Field('url', placeholder='http://example.com'),
                    Field('description', placeholder='Description'),
                    Field('download', placeholder='http://example.com'),
                    Field('curator', placeholder='Bar Foo'),
                    Field('license', placeholder='GPL'),
                    Field('encoding',
                          placeholder='e.g.: utf-8 - autodetect if omitted'),
                    Field('projection', placeholder='e.g.: epsg:23032'),
                    Field('csv_delimiter', placeholder='CSV delimiter'),
                    Field('csv_quotechar', placeholder='CSV quote character'),
                    Field('tags', placeholder='tag1, tag2, tag3'),
                    Field('update_rule', placeholder='updata rule'),
                    'other_meta',
                    css_class='span10 offset1',
                ),
                css_class='row-fluid create-form',
            ),
            Fieldset(
                _('Geographic metadata'),
                Div(
                    Field('bounding_box',
                          placeholder='<minlon,minlat,maxlon,maxlat> expressed'
                                      ' in EPSG 900913'),
                    css_class='span10 offset1',
                ),
                css_class='row-fluid create-form',
            ),
            Div(
                HTML('<hr>'),
                Div(
                    Submit('submit', 'Save'),
                    css_class='pull-right'
                ),
                css_class='row-fluid',
            ),
        )
        self.helper.form_class = 'form-horizontal'

        super(DatasetForm, self).__init__(*args, **kwargs)


def _get_source_choices():
    """Returns a list of all available Sources."""
    return [(source.name, ) * 2 for source in Source.objects.all()]


class ArchiveItemRuleForm(forms.Form):
    """
    Form for editing an ArchiveItem rule
    """
    rule = JSONFormField(widget=AceWidget(mode='json', theme='chrome'))

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.html5_required = True

        self.helper.layout = Layout(
            Fieldset(
                _('Rule'),
                Div(
                    Field('rule'),
                    css_class='span12'
                ),
                css_class='row-fluid create-form'
            ),
            Div(
                Div(
                    HTML('<span class="btn" onClick="window.history.back()">'
                         'Cancel</span>'),
                    Submit('submit', 'Save'),
                    css_class='pull-right'
                ),
                css_class='row-fluid',
            ),
        )
        super(ArchiveItemRuleForm, self).__init__(*args, **kwargs)
        self.fields['rule'].label = ''  # this is to remove the label


class ArchiveItemAggregatorForm(forms.Form):
    """
    Form for selecting an aggregator from the ArchiveItem view
    """
    aggregator = forms.ModelChoiceField(queryset=Aggregator.objects.all())

    def __init__(self, archiveitem, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.html5_required = True
        self.helper.form_class = 'form-inline'

        self.helper.form_action = reverse(
            'archiveitem_aggregator_add', args=(archiveitem.pk, )
        )

        self.helper.layout = Layout(
            Fieldset(
                _('Aggregator'),
                Div(
                    Field('aggregator', css_class='input-xlarge'),
                    css_class='span9 offset1',
                ),
                Div(
                    Submit('submit', 'Add'),
                    css_class='span1',
                ),
                css_class='row-fluid',
            ),
        )
        super(ArchiveItemAggregatorForm, self).__init__(*args, **kwargs)
        self.fields['aggregator'].label = ''  # this is to remove the label


class AggregatorForm(forms.ModelForm):
    """ the modelform for an Aggregator
    """

    class Meta:
        model = Aggregator

        widgets = {
            'description': forms.Textarea(attrs={'rows': '3'}),
            'silk_rule': AceWidget(mode='xml', theme='chrome'),
            'vertex_selector': AceWidget(
                mode='groovy', theme='chrome',
            ),
        }

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()

        self.helper.html5_required = True
        self.helper.form_class = 'form-horizontal'

        self.helper.layout = Layout(
            Fieldset(
                _('Aggregator information'),
                Div(
                    Field('name', placeholder='Name'),
                    Field('description', placeholder='Description'),
                    Field('entity_type', placeholder='EntityType'),
                    Div(
                        HTML(dedent(
                            """Use this field to filter vertices on the titan
                             graph. You must fill the array 'm' with the ids
                             you want to handle. Please notice that multiple
                             lines *may* corrupt the script.<br/>
                             Utils:
                             <ul>
                             <li><i>%limit</i>: will be translated with
                             '[1..N]' when it is necessary to limit the number
                             of inspected vertices for data analysis;</li>
                             <li><i>namespaces</i> will need special handling:
                             please use 'sd$POI' for 'sd:POI';</li>
                             </ul>
                            """)),
                        css_class="controls muted"
                    ),
                    Field('vertex_selector', placeholder='Vertex Selector'),
                    Field('silk_rule', placeholder='SilkRule'),
                    css_class='span10 offset1'
                ),
                css_class='row-fluid create-form'
            ),
            Fieldset(
                _('ArchiveItems'),
                Div(
                    Field(
                        'archiveitems',
                    ),
                ),
                css_class='row-fluid create-form'
            ),
            Div(
                HTML('<hr>'),
                Div(
                    HTML('<span class="btn" onClick="window.history.back()">'
                         'Cancel</span>'),
                    Submit('submit', 'Save'),
                    css_class='pull-right'
                ),
                css_class='row-fluid',
            ),
        )

        super(AggregatorForm, self).__init__(*args, **kwargs)

    # pylint: disable=E1101,E1002
    def save(self, commit=None):
        """
        save with a fix for explicit m2m
        """
        out = super(AggregatorForm, self).save(commit=False)

        aggregator = self.instance
        aggregator.save()

        already_present_pks = [
            ai.pk for ai in aggregator.archiveitems.all()]
        new_archiveitems = self.cleaned_data['archiveitems']

        for archiveitem in new_archiveitems:
            pk = archiveitem.pk
            if pk not in already_present_pks:
                AggregatorArchiveItem.objects.create(
                    aggregator=aggregator,
                    archiveitem=archiveitem,
                )
            else:
                already_present_pks.remove(pk)

        for pk in already_present_pks:
            aggregator.aggregatorarchiveitem_set.get(archiveitem_id=pk)\
                .delete()

        return out
    # pylint: enable=E1101,E1002


class AggregatorImportForm(forms.ModelForm):
    """ the modelform for an Aggregator
    """
    silk_rule_file = forms.FileField()

    # pylint: disable=E1101,E1002
    def save(self, commit=True):
        silk_rule_file_content = self.cleaned_data['silk_rule_file'].read()
        import xml.etree.ElementTree as ET
        try:
            root = ET.fromstring(silk_rule_file_content)
            interlink = root.find('.//LinkageRule')
            if not interlink:
                raise Exception('Invalid silk file')
        except Exception as e:
            raise ValidationError('Error while parsing file', e)
        self.instance.silk_rule = ET.tostring(interlink)

        return super(AggregatorImportForm, self).save(commit)
    # pylint: enable=E1101,E1002


class SilkRuleFakeForm(forms.ModelForm):
    """ a fake form for showing the silk rule of an Aggregator with ACE
    """
    silk_rule = forms.CharField(widget=AceWidget(mode='xml', theme='chrome'))

    class Meta:
        model = Aggregator


class RefineBatchEditForm(forms.Form):
    """
    Used in Refine batch edit tools
    """
    filter = forms.CharField(
        required=True,
        widget=AceWidget(mode='python', theme='chrome'),
    )

    # pylint: disable=E1002
    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()

        self.helper.html5_required = True
        self.helper.form_class = 'form-horizontal'

        self.helper.layout = Layout(
            Field('filter', placeholder='Filter'),
            Div(
                HTML('<hr>'),
                Div(
                    Submit('submit', 'Filter'),
                    css_class='pull-right'
                ),
                css_class='row-fluid',
            ),
        )

        super(RefineBatchEditForm, self).__init__(*args, **kwargs)
    # pylint: enable=E1002
