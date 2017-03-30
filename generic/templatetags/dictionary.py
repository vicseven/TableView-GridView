# -*- coding: utf-8 -*-
from django.template import Library

register = Library()


@register.filter
def get_item(dictionary, key):
    tmp = dictionary.get(key)
    if tmp == None:
        return ''
    else:
        return tmp


@register.filter
def get_value(value):
    if value is None:
        return ''
    else:
        return value
