from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        val = dictionary.get(key, '')
        if val is None:
            return ''
        return str(val)[:80]
    return ''
