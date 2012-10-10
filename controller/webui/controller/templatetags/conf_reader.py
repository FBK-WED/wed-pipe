"""
Specific tag to access Django settings from templates.
"""

from django.conf import settings
from django import template

register = template.Library()

@register.tag
def value_from_settings(parser, token):
	try:
		# split_contents() knows not to split quoted strings.
		tag_name, var = token.split_contents()
	except ValueError:
		raise template.TemplateSyntaxError, "%r tag requires a single argument" % token.contents.split()[0]
	return ValueFromSettings(var)

class ValueFromSettings(template.Node):
	def __init__(self, var):
		self.arg = template.Variable(var)
	def render(self, context):
		return settings.__getattr__(str(self.arg.literal))