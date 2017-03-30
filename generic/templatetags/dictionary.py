# -*- coding: utf-8 -*-
from django.template import Library

register = Library()


# Este filtro sirve para obtener de un diccionario el valor dada una llave en una plantilla
# la forma de uso es {{ diccionario|get_item:llave }}
# utilizado en plantilla tabla
@register.filter
def get_item(dictionary, key):
    tmp = dictionary.get(key)
    if tmp == None:
        return ''
    else:
        return tmp

# Filtro que devuelve una cadena vacia en el caso que el valor sea None
@register.filter
def get_value(value):
    if value is None:
        return ''
    else:
        return value

# Documentar utilizado en plantilla detalle
# @register.filter
# def get_lista(lista):
#     return lista.pop(0)
#
# @register.filter
# def lista_no_vacia(lista):
#     if len(lista) > 0:
#         return True
#     else:
#         return False
#
# @register.filter
# def get_tupla(tupla, elemento):
#         return tupla[elemento]
#
# @register.filter
# def get_len(elemento):
#         return len(elemento)
# Los siguientes dos filtros sirven para obtener el nombre "verbose" del modelo
# con el cual se esté trabajando en la plantilla. Los modos de uso son:
#   1) Si en la plantilla se tiene acceso al objeto\modelo:
#       {{ object|get_name_model }}
#   2) Si en la plantilla se tiene acceso al QuerySet:
#       { object_list.model|get_names_model }}
# @register.filter
# def get_name_model(object):
#     return object._meta.verbose_name
#
# @register.filter
# def get_names_model(object):
#     return object._meta.verbose_name_plural
