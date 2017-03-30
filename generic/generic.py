# -*- coding: utf-8 -*-
import operator
from functools import reduce

from django.db.models import Q
from django.views import generic
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from django.contrib import messages
from django.template import engines
from django.template.response import TemplateResponse

from .TableTemplate import common_table_html, child_table_html, \
    common_detail_html, jscript_template, table_show_menu_html, toolbar_table_html, base_head_html
from .images import search_png, delete_png, order_a_png, order_d_png


class GenericTable(generic.ListView):
    """
    Provides a finished view of any model's data exposed as a table.

    Expose data of any model in a table standard view. The user is able to
    order, filter, or search data. Paged is default to 25 rows.
    """

    # Required for base table and child table
    model = ''
    initial_order = ''
    primary_key = 'id'
    columns = []
    search_by = []
    processes = []

    # When each row is linked to an instance of GenericDetail
    link_to_detail = False       # Must be True to show details of each row. A sub class of GenericDetail must exist
    detail_view_name = ''        # Must be the name of the view of the sub class of GenericDetail for the model.

    # Required for any type of table, default to base table.
    paginate_by = 25
    html_class = ''
    base_mode = True # For child table, must be False
    delete_able = False
    reset_able = False
    create_able = False
    filter_able = False # If True model_form can not be empty
    filter_behavior = '__icontains'
    model_form = ''
    search_able = False

    # Required for base table
    extend_html = ''
    base_template_block = '{% block content %}'

    # Required for child table
    extend_as_child = ''
    child_template_block = '{% block child %}'
    parent_model = ''

    # Not public attributes
    _search_list = []
    _app_name = ''
    _app_namespace = ''
    _last_sort = ''
    _last_search = ''
    _to_search = ''
    _column_sort = ''
    _url_data = {}
    _id_delete_list = ''
    _list_of = []
    _identifier = ''
    _actual_page = ''

    def get(self, request, *args, **kwargs):
        self._app_name = request.resolver_match.app_name
        self._app_namespace = request.resolver_match.namespace
        self._url_data = self.request.GET
        self._to_search = '0'
        if self.initial_order == '':
            self.initial_order = '-' + self.primary_key
        sort_by = self.initial_order
        if not self.primary_key:
            self.primary_key = 'id'
        if 'pk' in kwargs:
            self.base_mode = False
            self._identifier =  kwargs['pk']
        if self.base_mode:
            template_code = '{% extends "' + self.extend_html + '" %}' \
                            + self.base_template_block \
                            + base_head_html \
                            + toolbar_table_html \
                            + jscript_template \
                            + table_show_menu_html \
                            + common_table_html
        else:
            template_code = '{% extends "' + self.extend_as_child + '" %}' \
                            + self.child_template_block \
                            + child_table_html \
                            + toolbar_table_html \
                            + jscript_template \
                            + table_show_menu_html \
                            + common_table_html
        if 'page' in self._url_data:
            self._actual_page = self._url_data.get('page')
        else:
            self._actual_page = 1
        if 'sort_by' in self._url_data:
            sort_by = self._url_data.get('sort_by')
            if 'sort_to' in self._url_data:
                self._last_sort = self._url_data.get('sort_to')
                if sort_by == self._last_sort:
                    sort_by = '-' + sort_by
        self._last_sort = sort_by
        self.object_list = self.get_queryset().order_by(sort_by) # A minimal ordered object_list.
        if 'to_search' in self._url_data:
            self._to_search = self._url_data.get('to_search')
            if self._to_search == '0':
                self._last_search = self._url_data.get('search')
                if self._last_search != '':
                    self._search_list = [Q((filter, self._last_search)) for filter, var_data in self.search_by]
                    self.object_list = self.get_queryset().filter(
                        reduce(operator.or_, self._search_list)) # A searched and ordered object_list
                else:
                    self.object_list = self.get_queryset().all()
            if self._to_search == '1':
                qs = self.get_queryset()
                for field,value in self._url_data.items():
                    if (field != 'to_search') and (field != 'page') and (field != 'seach_by') and (field != 'sort_by')\
                        and (field != 'x') and (field != 'y'):
                        if value != '':
                            qs = qs.filter(**{field + self.filter_behavior: value})
                self.object_list = qs
            self.object_list = self.object_list.order_by(sort_by) # A filtered and ordered object_list
        self.search_by = self._url_data
        engine = engines['django']
        template = engine.from_string(template_code)
        return TemplateResponse(request,template,self.get_context_data(**kwargs))

    def post(self, request, *args, **kwargs):
        self._app_name = request.resolver_match.app_name
        self._app_namespace = request.resolver_match.namespace
        return self.generic_delete(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(GenericTable, self).get_context_data(**kwargs)

        # Proces object_list to construct a new set of data to be send to tempalte by context.
        _form_instance = self.model_form(None)
        _table_data = []
        for object in Paginator(self.object_list, self.paginate_by).page(self._actual_page):
            _table_row = {'id': object[self.primary_key],
                    'columns': []
                    }
            for _field_name, _field_title, _has_filter,_filter_code, _html_code in self.columns:
                _value = object[_field_name]
                if _value == '' or _value == None:
                    _table_row['columns'].append('')
                elif _html_code == '':
                    _table_row['columns'].append(_value)
                elif _html_code == '__form__':
                    _form_field = _form_instance.fields[_field_name]
                    _form_field.initial = _value
                    _table_row['columns'].append(_form_field.widget.render(
                            _field_name, _value,attrs={'readonly':'readonly','style':'border: none;'}
                        )
                    )
                else:
                    _table_row['columns'].append(_html_code.format(_value, object[self.primary_key]))
            _table_data.append(_table_row)
        if self.filter_able:
            # If filter are able, the field to be used is recovered from the model's forms
            _form_instance = self.model_form(None)
            _column_filter = {}
            for _column_field, _column_name, _has_filter, _filter_code, _html_code in self.columns:
                if _column_field in self.search_by:
                    _value = self._url_data.get(_column_field)
                else:
                    _value = ''
                if _filter_code == '__form__':
                    _form_field = _form_instance.fields[_column_field]
                    if _value != None:
                        _form_field.initial = _value
                    _column_filter.update({_column_field: _form_field.widget.render(_column_field, _form_field.initial)})
                elif _filter_code == '':
                    # Translators: This message appear as placeholder for filter when using empty string option in virtual table tuple
                    _tmp = """<input class="{{ html_class|add:'genTab'}} {{ html_class|add:'genTabFilterField'}}" type="text" name='""" + _column_field \
                           + """' value='""" + _value + "' placeholder='" + _('Search for ...') + "'>"
                    _column_filter.update({_column_field: _tmp})
                else:
                    _column_filter.update({_column_field: _filter_code})
            context['column_filter'] = _column_filter
        _processes_link = []
        if self.processes:
            for process_name, process_view, html_code in self.processes:
                _processes_link.append((process_name, process_view, html_code, self._app_name + ':' + process_view))
        context['processes'] = _processes_link
        context['detail_url'] = self._app_name + ':' + self.detail_view_name
        context['child_detail_view'] = self._app_name + ':' + self.detail_view_name
        context['link_to_detail'] = self.link_to_detail
        context['base_mode'] = self.base_mode
        context['create_able'] = self.create_able
        context['reset_able'] = self.reset_able
        context['delete_able'] = self.delete_able
        context['filter_able'] = self.filter_able
        context['search_able'] = self.search_able
        context['table_data'] = _table_data
        context['columns'] = self.columns
        context['sort_to'] = self._last_sort
        context['search_for'] = self._last_search
        context['search_by'] = self.search_by
        temp = ''
        for campo,contenido in self.search_by.items():
            if campo != 'page':
                temp += '&'+ campo + '=' + contenido
        context['url_data'] = temp
        context['to_search'] = self._to_search
        context['search_png'] = search_png
        context['delete_png'] = delete_png
        context['order_a_png'] = order_a_png
        context['order_d_png'] = order_d_png
        context['identifier'] = self._identifier
        context['html_class'] = self.html_class
        context['id_field'] = self.primary_key
        context['initial_order'] = self.initial_order
        if not self.base_mode:
            context['parent_model'] = self.parent_model._meta.verbose_name
        return context

    def get_related_query(self, ident=None):
        return self.model.objects.all().values()

    def get_queryset(self):
        if self.base_mode:
            return self.model.objects.all().values()
        else:
            return self.get_related_query(self._identifier)

    def generic_delete(self, request, *args, **kwargs):
        """
        generic_delete is used for deleting rows
        """
        self.object = None
        self._id_delete_list = request.POST.getlist('delete')
        if self._id_delete_list:
            for element_id in self._id_delete_list:
                delete_this = self.model.objects.get(pk=element_id)
                delete_this.delete()
        return HttpResponseRedirect('#')


class GenericDetail(generic.View):
    """
    Provides a finished view of the details of any model's data register (table row)

    The user is able to view, modify and create new data.
    """

    # Required by any implementation
    model = ''
    model_form = ''
    view_namespace = ''

    # Required by any implementation; but with default values to base implementation.
    primary_key = 'id'       # If primary_key is not id.
    primary_grid = []  # It could be empty
    secondary_grid = []  # It could be empty
    base_mode = True       # For child view, must be False
    update_able = False
    secondary_grid_able = False
    show_secondary_grid = False

    # Required when showing a child
    have_child = False     # If detail view show a table of other model (OneToMany) must be True.
    child_model = ''       # Child model. Model that is the Many part in the OneToMany relation Ship.
    child_table_name = ''  # View name of the child model's table class working in child mode.
                           # Also required when base_mode = False
    child_table_width = "700"
    child_table_height = "300"

    # Required by any implementation; but with default values for HTML render
    html_class = ''

    # Base View Implementation attributes
    extend_html = ''
    base_template_block = '{% block content %}'
    back_able = False
    view_name = ''

    # Child View Implementation attributes
    foreign_key_attribute = ''
    extend_as_child = ''
    child_template_bock = '{% block child %}'
    hide_child = False

    # Requiered when redefining generic_update or generic_new
    # used in get_context_data
    form_instance = ''  # Travels with the data

    # No public attributes
    _app_name = ''
    _editing = False
    _new = False
    _identifier = ''
    _new_child = False
    _parent_id = ''
    _parent_model = ''

    def get(self, request, *args, **kwargs):
        self._app_name = request.resolver_match.app_name
        if self.base_mode:
            template_code = '{% extends "' + self.extend_html + '" %}' \
                            + self.base_template_block \
                            + jscript_template \
                            + common_detail_html
        else:
            template_code = '{% extends "' + self.extend_as_child + '" %}' \
                            + self.child_template_bock \
                            + jscript_template \
                            + common_detail_html
        engine = engines['django']
        template = engine.from_string(template_code)
        if 'pk' in kwargs:
            self._identifier = kwargs['pk']
            self.model = get_object_or_404(self.model, pk=kwargs['pk'])
            self.form_instance = self.model_form(instance=self.model)
            if not self.base_mode:
                self._parent_id = getattr(self.model, self.foreign_key_attribute + '_id')
            # Translators: This message goes trough Django's messages framework with messages.success
            messages.success(request, _('Watching registry: ') + kwargs['pk'])
            return TemplateResponse(request,template,self.get_context_data(**kwargs))
        else: # No pk means a new object is beeing created.
            self._new = True
            _parameters = request.GET
            if 'new_child' in _parameters:
                # if 'new_child' is in request.Get means a child object is being created for a parent. The parameters
                # received will be:
                # id_parent, parent_model
                # Also is expected the developer has redefined the attribute foreign_key_attribute.
                self._parent_model = _parameters['parent_model']
                self._parent_id = _parameters['id_parent']
                _tmp_data = {
                    self.foreign_key_attribute: self._parent_id,
                }
                self.form_instance = self.model_form(_tmp_data)
                self._new_child = True
                # Translators: This message goes trough Django's messages framework with messages.success
                messages.success(request, _('Creating new registry for parent register:') + _parameters['id_parent'])
            else:
                self.form_instance = self.model_form()
                # Translators: This message goes trough Django's messages framework with messages.success
                messages.success(request, _('Creating a new registry.'))
            return TemplateResponse(request,template,self.get_context_data(**kwargs))

    def post(self, request, *args, **kwargs):
        self._app_name = request.resolver_match.app_name
        if self.base_mode:
            template_code = '{% extends "' + self.extend_html + '" %}' \
                            + self.base_template_block \
                            + jscript_template \
                            + common_detail_html
        else:
            template_code = '{% extends "' + self.extend_as_child + '" %}' \
                            + self.child_template_bock \
                            + jscript_template \
                            + common_detail_html
        engine = engines['django']
        template = engine.from_string(template_code)
        if 'pk' in kwargs:
            self._identifier = kwargs['pk']
        if 'edit' in request.POST:
            self._editing = True
            self.model = self.model.objects.get(pk=self._identifier)
            if not self.base_mode:
                # If editing a child, and foreign key is not present in primary_fields neither secondary_fields,
                # will be necesary to recover id and put it as hidden in the form.
                self._parent_id = getattr(self.model, self.foreign_key_attribute + '_id')
            self.form_instance = self.model_form(instance=self.model)
            # Translators: This message goes trough Django's messages framework with messages.success
            messages.success(request, _('You are editing registry: ') + kwargs['pk'])
        elif 'new' in request.POST:
            self._new = True
            if 'creating_child' in request.POST:
                self._parent_id = request.POST['parent_id']
            return self.generic_new(template, request, *args, **kwargs)
        elif 'update' in request.POST:
            self.model = self.model.objects.get(pk=self._identifier)
            if not self.base_mode:
                # The parent_id is needed to build "back to table" button.
                self._parent_id = getattr(self.model, self.foreign_key_attribute + '_id')
            return self.generic_update(template, self.model, request, *args, **kwargs)
        return TemplateResponse(request,template,self.get_context_data(**kwargs))

    def get_context_data(self, **kwargs):
        context = {}
        _data_grid_primary = []
        _data_grid_secondary = []
        _is_fk_present = False
        _exist_field = []
        _foreign_key_in_form = True
        _auto_row_primary = 0
        _auto_row_secondary = 0

        if self.primary_grid:
            for _model_attribute, _label, _label_able, _line_number, _is_data in self.primary_grid:
                _template_field = _model_attribute
                _field = next(( item for item in self.form_instance if item.name == _model_attribute), False)
                if _field:
                    _template_field = _field
                    if _label != '':
                        _field.label = _label
                    if _model_attribute == self.foreign_key_attribute:
                        _is_fk_present = True
                    # The field must not be included in an auto generated _data_grid_secodnary
                    _exist_field.append(_model_attribute)
                if _field or not _is_data:
                    # Exist the row in _grid_data? _grid_data = list of dicts
                    _exist_row = next((row for row in _data_grid_primary if row['row'] == _line_number),False)
                    if _exist_row:
                        _exist_row['data'].append((_template_field, _label, _label_able, _is_data))
                    else:
                        _row = dict(row = _line_number, data = [(_template_field, _label, _label_able, _is_data)])
                        _data_grid_primary.append(_row)
            if self.secondary_grid_able:
                if self.secondary_grid:
                    for _model_attribute, _label, _label_able, _line_number, _is_data in self.secondary_grid:
                        _template_field = _model_attribute
                        _field = next((item for item in self.form_instance if item.name == _model_attribute), False)
                        if _field:
                            _template_field = _field
                            if _label != '':
                                _field.label = _label
                            if _model_attribute == self.foreign_key_attribute:
                                _is_fk_present = True
                        if _field or not _is_data:
                            # Exist the row in _grid_data? _grid_data = list of dicts
                            _exist_row = next((row for row in _data_grid_secondary if row['row'] == _line_number), False)
                            if _exist_row:
                                _exist_row['data'].append((_template_field, _label, _label_able, _is_data))
                            else:
                                _row = dict(row = _line_number, data = [
                                    (_template_field, _label, _label_able, _is_data)])
                                _data_grid_secondary.append(_row)
                elif not self.secondary_grid:
                    for _field in self.form_instance:
                        if _field.name not in _exist_field:
                            _row = dict(row = _auto_row_secondary, data = [(_field,_field.label,True,True)])
                            _data_grid_secondary.append(_row)
                            _auto_row_secondary += 1
        else:
            for _field in self.form_instance:
                _row = dict(row=_auto_row_primary, data=[(_field,_field.label,True,True)])
                _data_grid_primary.append(_row)
                _auto_row_primary += 1

        if not self.base_mode:
            # For creating or updating a child the foreign key is mandatory (foreign_key_attribute is a required
            # attribute in child mode) in the form (together with all required attributes of the model). So if it is
            # not present in primary_fields or secondary_fields attributes, it must be incorporated as hidden to the
            # form, or the form will fail when updating or creating a new child. The name of the field is the first
            # element of the tuple: v[0]
            if not _is_fk_present:
                context['foreign_key_attribute'] = self.foreign_key_attribute
                _foreign_key_in_form = False
        # The context data
        context['data_grid_primary'] = _data_grid_primary
        context['secondary_grid'] = self.secondary_grid_able
        if self.secondary_grid_able:
            context['data_grid_secondary'] = _data_grid_secondary
        context['foreign_key_present'] = _foreign_key_in_form
        context['view_namespace'] = self._app_name + ':' + self.view_namespace
        context['child_table_name'] = self._app_name + ':' + self.child_table_name
        context['back_able'] = self.back_able
        context['view_name'] = self._app_name + ':' + self.view_name
        context['parent_id'] = self._parent_id
        context['update_able'] = self.update_able
        context['secondary_show'] = self.show_secondary_grid
        context['hide_child'] = self.hide_child
        context['html_class'] = self.html_class
        context['child_table_width'] = self.child_table_width
        context['child_table_height'] = self.child_table_height
        context['have_child'] = self.have_child
        context['object'] = self.model
        context['base_mode'] = self.base_mode
        context['creating_child'] = self._new_child
        context['identifier'] = self._identifier
        context['edit'] = self._editing
        context['new'] = self._new
        context['form'] = self.form_instance

        return context

    def get_css_class(self, type, state):
        """
        Define an html style class depending on the type of field. State means: Enable or disable.
        """
        if type == "CheckboxInput":
            return {'class' : self.html_class + 'detInputCheckboxInput' + state}
        elif type == "ClearableFileInput":
            return {'class' : self.html_class + 'detInputClearableFileInput' + state}
        elif type == "DateInput":
            return {'class' : self.html_class + 'detInputDateInput' + state}
        elif type == "DateTimeInput":
            return {'class' : self.html_class + 'detInputDateTimeInput' + state}
        elif type == "EmailInput":
            return {'class' : self.html_class + 'detInputEmailInput' + state}
        elif type == "HiddenInput":
            return {'class' : self.html_class + 'detInputHiddenInput' + state}
        elif type == "MultipleHiddenInput":
            return {'class' : self.html_class + 'detInputMultipleHiddenInput' + state}
        elif type == "NullBooleanSelect":
            return {'class' : self.html_class + 'detInputNullBooleanSelect' + state}
        elif type == "NumberInput":
            return {'class' : self.html_class + 'detInputNumberInput' + state}
        elif type == "Select":
            return {'class' : self.html_class + 'detInputSelect' + state}
        elif type == "SelectMultiple":
            return {'class' : self.html_class + 'detInputSelectMultiple' + state}
        elif type == "SplitDateTimeWidget":
            return {'class' : self.html_class + 'detInputSplitDateTimeWidget' + state}
        elif type == "SplitHiddenDateTimeWidget":
            return {'class' : self.html_class + 'detInputSplitHiddenDateTimeWidget' + state}
        elif type == "TextInput":
            return {'class' : self.html_class + 'detInputTextInput' + state}
        elif type == "TimeInput":
            return {'class' : self.html_class + 'detInputTimeInput' + state}
        elif type == "URLInput":
            return {'class' : self.html_class + 'detInputURLInput' + state}

    def generic_new(self, template, request, *args, **kwargs):
        self.form_instance = self.model_form(request.POST or None)
        if self.form_instance.is_valid():
            save_it = self.form_instance.save(commit=False)
            save_it.save()
            tmp_pk = getattr(save_it, self.primary_key)
            # Translators: This message goes trough Django's messages framework with messages.success
            messages.success(request, _('The registry has been created with Primary Key: ' + str(tmp_pk)))
            if 'creating_child' in request.POST:
                return HttpResponseRedirect(
                    reverse(self._app_name + ':' + self.child_table_name, kwargs={'pk': self._parent_id})
                )
            else:
                return HttpResponseRedirect(reverse(self._app_name + ':' + self.view_namespace, kwargs={'pk': tmp_pk}))
        else:
            # Translators: This message goes trough Django's messages framework with messages.error
            messages.error(request, _('The form for the register has fail.'))
            return TemplateResponse(request, template, self.get_context_data(**kwargs))

    def generic_update(self, template, model, request, *args, **kwargs):
        self.form_instance = self.model_form(request.POST or None, instance=model)
        if self.form_instance.is_valid():
            self.form_instance.save()
            # Translators: This message goes trough Django's messages framework with messages.success
            messages.success(request, _('It has been modify the registry: ') + kwargs['pk'])
        else:
            # Translators: This message goes trough Django's messages framework with messages.error
            messages.error(request, _('The form has fail for registry: ') + kwargs['pk'])
        return TemplateResponse(request, template, self.get_context_data(**kwargs))
