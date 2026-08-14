from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """ фильтр для использования методо словаря в шаблонах """
    return dictionary.get(key)