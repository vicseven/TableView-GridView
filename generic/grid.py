# -*- coding: utf-8 -*-

from django.views import View
from django.views.generic.edit import ModelFormMixin
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.template import engines
from django.utils.translation import ugettext as _
from django.contrib import messages
from django.template.response import TemplateResponse
from django.shortcuts import get_object_or_404
from .commonTemplates import tool_bar_begin, tool_bar_end
from .GridTemplate import basic_grid_html, grid_load_template, back_html, \
    edit_html, update_html, new_html, child_grid_html
"""
    By Django Design(?) when sub-classing, the "rules" appears to be:



    django.view.generic.base.py
    * ContextMixin(object)                                          Define get_context_data(self, **kwargs) method.
    * TemplateResponseMixin(object)                                 Define 4 attributes and render_to_response,
                                                                    get_templates_names methods.

    django.view.generic.detail.py
    * SingleObjectMixin(ContextMixin)                               Define 5 methods and 7 attributes.
    * SingleObjectTemplateResponseMixin(TemplateResponseMixin)      Define 2 attributes and get_templates_names method.

    django.view.generic.edit.py
    * FormMixin(ContextMixin)                                       Define 9 methods and 4 attributes.
    * ModelFormMixin(FormMixin, SingleObjectMixin)                  Define get_form_class, get_form_kwargs,
                                                                    get_success_url, form_valid
    * ProcessFormView(View)                                         Define simple get and post and put methods
    * BaseFormView(FormMixin, ProcessFormView)                      Do nothing.
    * FormView(TemplateResponseMixin, BaseFormView)                 Do nothing.
    * BaseCreateView(ModelFormMixin, ProcessFormView)               Define simple get and post methods
    * CreateView(SingleObjectTemplateResponseMixin, BaseCreateView) redefine template_name_sufix = '_form'
    * BaseUpdateView(ModelFormMixin, ProcessFormView)               Define simple get and post methods
    * UpdateView(SingleObjectTemplateResponseMixin, BaseUpdateView) redefine template_name_sufix = '_form'
    * DeletionMixin(object)                                         Define method delete, post, and get_success_url
    * BaseDeleteView(DeletionMixin, BaseDetailView)                 Do nothing.
    * DeleteView(SingleObjectTemplateResponseMixin, BaseDeleteView) Do nothing.
    Notes:
        ModelFormMixin is twice a sub-class of ContextMixin
        BaseCreateView and BaseUpdateView are sub-class of ModelFormMixin

    * What came from ModelFormMixin are joined with ProcessFormView and gives BaseAlterView.
    * What came from TemplateResponseMixin(object) is joined with BaseAlterView and gives the View.

    Following 'this logic' the Grid Tree Class should be:
    * BasicGridTemplateResponseMixin(object).                       Define 4 attributes and render_to_response,
                                                                    get_template
    * VariableGridTemplateResponseMixin(GridTemplateResponseMixin)  Define get_template


    * GridProcessView(View)                                         Define get and post. A view for grids.
    * GridBaseViewMixin(GridProcessView)                            Define a simple get.

    * BasicGridMixin(ModelFormMixin).                               Define 19 attributes and 5 method
    * VariableGridBaseViewMixin(BasicGridMixin, GridProcessView)    Define 12 attributes and 5 method

    * BasicGridView(GridTemplateResponseMixin, BasicGridMixin, GridBaseViewMixin)   Do nothing.
    * GridView(VariableGridTemplateResponseMixin, VariableGridBaseViewMixin)        Do nothing.

    * BaseVariableGridView should be sub-class of VariableGridMixin and GridProcessView
    * VariableGridTemplateResponseMixin be sub-class of TemplateResponseMixin; but it is replaced by
    BasicGridTemplateResponseMixin. Read Problems with Template. Important TemplateResponseMixin only knows about
    render_to_response and get_template_names. So Template Mixin knows nothings about context and View. Somthing like:
    'all logic is in Base<thing>View' while <thing>TemplateResponseMixin only knows about render_to_response.
    * The GridView should be sub-class of BaseVariableGridView and VariableGridTemplateResponseMixin

    Problems whit Template:
    * BasicGridTemplateResponse and VariableGridTemplateResponse(BasicGridTemplateResponse) implements get_template_data
    and get_context_data; while BasicGridTemplateResponse implements render_to_response.
    Analysis
    1) BasicGridTemplateResponse should be sub-class of TemplateResponseMixin as SingleObjectTemplateResponseMixin.
    But TemplateResponseMixin is sub-class of Object using TemplateResponse as an attribute: response_class. And it's

    BasicGridTemplateResponse is a try of redefining TemplateResponseMixin.
    Tries to solve problems caused by template be given as a sting:

    * Using as 'template' the result of Engine().from_string(template_code) I get the error:
            'i18n' is not a registered tag library. Must be one of:
            in: django/template/defaulttags.py in find_library
            1022 name, "\n".join(sorted(parser.libraries.keys())),

    * Using django.template.Template(template_code) but it has a render() method with 1 parameter (self, context), while
    FormMixin use self.render_to_response() (BasicGridMixin is sub-class of ModelFormMixn, who is a sub-class of
    FormMixin. So for the Django Template Form System works as response_class in the redefinition of render_to_response
    was necessary to use HttpResponse instead of habitual TemplateResponse. And the code of render_to_response looks
    very different (self.response_class is an HttpResponse class:

    def render_to_response(self, context, **response_kwargs):
        request_context = RequestContext(self.request)
        request_context.push(context)
        return self.response_class(self.get_template().render(request_context))

    And get_template():
        def get_template(self):
        template_code = ......
        self.template_name = Template(template_code)
        return self.template_name

    * Using self.template_engine = entines['django'] and follow Django convention:
     1) GridTemplateResponse sub-class of TemplateResponseMixin, and define __init__:
    def __init__(self):
        template_code = ...
        self.template_name  = engines['django'].from_string(template_code)

    But this try end in error:
    sequence item 0: expected str instance, Template found
    .../lib/python3.5/site-packages/django/template/loader.py in select_template, line 53
    53  raise TemplateDoesNotExist(', '.join(template_name_list), chain=chain)

    2) So, assuming get_template_names of TemplateResponseMixin only accept files name (not template object), is
    TemplateResponseMixin the class to be 'redefined' as GridTemplateResponseMixin
    GridTemplateResponse as sub-class of ContextMixin(Object) (as TemplateResponseMixin(Object)) and redefining
    render_to_response. The only difference is in template assignment:
    TemplateResponseMixin:
        template = self.get_template_names()
    GridTemplateResponseMixin
        template = self.get_template()
    After all there is only one template to render, so there is no need for a list of templates.
"""
# TODO Pendientes
# TODO              * Si model_form no es provisto entonces self.fields = '__all__' en __init__ BasicGridMixin.
# TODO              * Sacar la mayor cantidad de codigo javascript?
# TODO Errores


class GridTemplateResponseMixin(object):
    """
    Provides a Basic Response Grid.

    A Basic Grid Template (the code) needs in the context:
    * html_class: Provided by this class (explained in get_context_data).
    * grid_row_class: Provided by this class (explained in get_context_data).
    * back_able: Provided by this class (explained in get_context_data).
    * back_view: Provided by this class (explained in get_context_data).
    * back_view_id: Provided by this class (explained in get_context_data).
    * data_grid: NOT provided by this class. Refer to BasicGridObjectMixin.
    * app_name: NOT provided by this class. Refer to GridProcessVew.
    """
    template_name = None
    template_engine = None
    response_class = TemplateResponse
    content_type = None
    base_template_block = '{% block content %}'
    extend_html = None
    toolbar_div_attribute = None
    grid_div_attribute = None

    def render_to_response(self, context, **response_kwargs):
        """
        Returns a response, using the `response_class` for this
        view, with a template rendered with the given context.

        If any keyword arguments are provided, they will be
        passed to the constructor of the response class.
        """
        response_kwargs.setdefault('content_type', self.content_type)
        return self.response_class(
            request=self.request,
            template=self.get_template(),
            context=context,
            using=self.template_engine,
            **response_kwargs
        )

    def get_template(self):
        tmp_toolbar_1 = ''
        tmp_toolbar_2 = ''
        tmp_grid_1 = ''
        tmp_grid_2 = ''
        if self.toolbar_div_attribute:
            tmp_toolbar_1 = '<div ' + self.toolbar_div_attribute + '>'
            tmp_toolbar_2 = '</div>'
        if self.grid_div_attribute:
            tmp_grid_1 = '<div ' + self.grid_div_attribute + '>'
            tmp_grid_2 = '</div>'
        template_code = '{% extends "' + self.extend_html + '" %}' \
                        + self.base_template_block \
                        + grid_load_template \
                        + tmp_toolbar_1 + tool_bar_begin + back_html + tool_bar_end + tmp_toolbar_2 \
                        + tmp_grid_1 + basic_grid_html + tmp_grid_2 \
                        + '{% endblock %}'
        self.template_name = engines['django'].from_string(template_code)
        return self.template_name


class VariableGridTemplateResponseMixin(GridTemplateResponseMixin):
    """
    Provides a Basic Response Grid.

    """

    def get_template(self):
        tmp_toolbar_1 = ''
        tmp_toolbar_2 = ''
        tmp_grid_1 = ''
        tmp_grid_2 = ''
        if self.toolbar_div_attribute:
            tmp_toolbar_1 = '<div ' + self.toolbar_div_attribute + '>'
            tmp_toolbar_2 = '</div>'
        if self.grid_div_attribute:
            tmp_grid_1 = '<div ' + self.grid_div_attribute + '>'
            tmp_grid_2 = '</div>'
        template_code = '{% extends "' + self.extend_html + '" %}' \
                        + self.base_template_block \
                        + grid_load_template \
                        + tmp_toolbar_1 + tool_bar_begin \
                        + back_html \
                        + edit_html \
                        + update_html \
                        + new_html \
                        + tool_bar_end + tmp_toolbar_2 \
                        + tmp_grid_1 + basic_grid_html + tmp_grid_2 \
                        + '{% endblock %}'
        self.template_name = engines['django'].from_string(template_code)
        return self.template_name


class ChildGridTemplateResponseMixin(GridTemplateResponseMixin):
    """

    """

    def get_template(self):
        tmp_toolbar_1 = ''
        tmp_toolbar_2 = ''
        tmp_grid_1 = ''
        tmp_grid_2 = ''
        if self.toolbar_div_attribute:
            tmp_toolbar_1 = '<div ' + self.toolbar_div_attribute + '>'
            tmp_toolbar_2 = '</div>'
        if self.grid_div_attribute:
            tmp_grid_1 = '<div ' + self.grid_div_attribute + '>'
            tmp_grid_2 = '</div>'
        template_code = '{% extends "' + self.extend_html + '" %}' \
                        + self.base_template_block \
                        + grid_load_template \
                        + tmp_toolbar_1 + tool_bar_begin \
                        + back_html \
                        + edit_html \
                        + update_html \
                        + new_html \
                        + tool_bar_end + tmp_toolbar_2 \
                        + tmp_grid_1 + basic_grid_html + tmp_grid_2 \
                        + child_grid_html \
                        + '{% endblock %}'
        self.template_name = engines['django'].from_string(template_code)
        return self.template_name


class ParentGridTemplateResponseMixin(VariableGridTemplateResponseMixin):
    """

    """
    child_frame_attributes = None
    child_div_attributes = None

    def get_template(self):
        tmp_toolbar_1 = ''
        tmp_toolbar_2 = ''
        tmp_grid_1 = ''
        tmp_grid_2 = ''
        tmp_frame_1 = ''
        tmp_frame_2 = ''
        tmp_frame_3 = ''
        if self.toolbar_div_attribute:
            tmp_toolbar_1 = '<div ' + self.toolbar_div_attribute + '>'
            tmp_toolbar_2 = '</div>'
        if self.grid_div_attribute:
            tmp_grid_1 = '<div ' + self.grid_div_attribute + '>'
            tmp_grid_2 = '</div>'
        if self.child_div_attributes:
            tmp_frame_1 = '<div ' + self.child_div_attributes + '>'
            tmp_frame_2 = '</div>'
        if self.child_frame_attributes:
            tmp_frame_3 = self.child_frame_attributes
        template_code = '{% extends "' + self.extend_html + '" %}' \
                        + self.base_template_block \
                        + grid_load_template \
                        + tmp_toolbar_1 + tool_bar_begin \
                        + back_html \
                        + edit_html \
                        + update_html \
                        + new_html \
                        + tool_bar_end + tmp_toolbar_2 \
                        + tmp_grid_1 + basic_grid_html + tmp_grid_2 \
                        + "<!-- Start Block Child Data -->{% if not new_able %}" \
                        + tmp_frame_1 \
                        + "<iframe src='{% url child_table_view parent_id %}' " \
                        + tmp_frame_3 + "></iframe>" \
                        + tmp_frame_2 +"{% endif %}<!-- End Block Child Data -->" \
                        + '{% endblock %}'

        self.template_name = engines['django'].from_string(template_code)
        return self.template_name


class GridProcessView(View):
    """
    The problem of constructing the View here is the access to the ModelFormMixin that are required for the logic of the
    GET and POST request.
    """
    app_name = None             # Needed to construct reverse url
    grid_view_name = None   # Needed when creating a new object.

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests and instantiates a blank version of the form.
        """
        self.app_name = request.resolver_match.app_name
        self.grid_view_name = request.resolver_match.view_name
        # Calling for grid redefinition conditions
        self.evaluate_grid()
        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests, instantiating a form instance with the passed
        POST variables and then checked for validity.
        """
        self.app_name = request.resolver_match.app_name
        self.grid_view_name = request.resolver_match.view_name
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def evaluate_grid(self):
        """

        :return:
        """
        return


class GridBaseViewMixin(GridProcessView):
    """

    """

    def get(self, request, *args, **kwargs):
        """

        :param template:
        :param model:
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        self.object = self.get_object()
        self.form_instance = self.get_form()
        return super(GridBaseViewMixin, self).get(request, *args, **kwargs)


class BasicGridMixin(ModelFormMixin):
    """
        The next context variables are added:
        * html_class:
        * grid_row_class:
        * back_class:
        * back_button_class:
        * back_able:            back_able = False (default) will produce a piece of html code without tool bar with.
                                back_able = True will produce a piece of html with a tool bar with a button with label
                                (value in html) back_name. A GET HTML form is introduced to the html code with property
                                id='grid_get_form'. This form as action will have the url formed by Django Template
                                tag: url, and values of back_view and back_view_id.
        * back_name:            The label a user will read in 'back button'. By default it's value is 'Back', when
                                redefining, this attribute could be translated.
        * back_view:            The view name in terms of Django's URLConf. When this attribute is not
                                None in template the action will be:
                                <form ... action="{% url back_view %}" ...>
        * back_view_id:         A back view could need to be done to an url with identifier. When this attribute is not
                                None in template the action will be:
                                <form ... action="{% url back_view back_view_id %}" ...>
    """
    # TODO Arreglar BasicGridMixin para que si no se prove model_form se use field = '__all__' se imite a como Django
    # TODO construye el formulario
    fields = None
    form_instance = None  # Used for instance a Model Form object.
    read_only = True        # Field are read only. If this attribute is True then get_grid_data will use the Model Form
                            # as values for the context instead of just the Model field's values.
    grid = None
    primary_key = None
    primary_key_present = False
    _new_object_flag = False
    success_url = '#'
    context_name = None
    engine_name = None
    html_class = ''
    toolbar_html_class = None
    form_html_class = None   # Gives value to class HTML attribute in <form> grid tag.
    grid_row_class = None
    html_form_class = ''    # Gives value to class HTML attribute in forms fields tags.
    html_label_class = ''   # Gives value to class HTML attribute inf labels fields tags.
    back_able = False
    back_name = 'Back'
    back_view = None
    back_view_id = None
    back_class = ''
    back_button_class = ''

    def __init__(self):
        """

        """
        super(BasicGridMixin, self).__init__()
        if self.model is None:
            raise ImproperlyConfigured("BasicGridMixin require model attribute.")
        if self.primary_key is None:
            self.primary_key = self.model._meta.pk.name
        if self.form_class is None:
            self.fields = '__all__'

    def get_success_url(self):
        if self._new_object_flag:
            # It does not resolve when slug is used.
            id_value = getattr(self.object, self.object._meta.pk.name)
            view = self.grid_view_name
            return reverse(view, args=[str(id_value)])
        else:
            return '#'

    def get_context_data(self, **kwargs):
        """

        :param template:
        :param model:
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        # The context data
        _data_grid = self.get_grid_data(self.grid)
        kwargs['data_grid'] = _data_grid
        if self.back_able:
            if isinstance(self.app_name, object):
                if self.app_name is not None:
                    if self.back_view is not None:
                        kwargs['back_view'] = self.app_name + ':' + self.back_view
                    else:
                        raise TypeError(
                            "BasicGridTemplateResponse back_view attribute can not be None if back_able=True.")
                else:
                    raise TypeError("BasicGridTemplateResponse app_name attribute can not be None if back_able=True.")
            else:
                raise TypeError("BasicGridTemplateResponse need app_name attribute if back_able=True.")
        if self.back_view_id is not None:
            kwargs['back_view_id'] = self.back_view_id
        # primary_key_present, primary_key, and primary_key_value are needed when model has no AutoField Primary Key
        kwargs['primary_key'] = self.primary_key
        kwargs['primary_key_present'] = self.primary_key_present
        if self.object is not None:
            kwargs['primary_key_value'] = getattr(self.object,self.primary_key)
        else:
            kwargs['primary_key_value'] = ''
        kwargs['html_class'] = self.html_class
        kwargs['grid_row_class'] = self.grid_row_class
        kwargs['back_class'] = self.back_class
        kwargs['back_button_class'] = self.back_button_class
        kwargs['back_able'] = self.back_able
        kwargs['back_name'] = self.back_name
        kwargs['form_html_class'] = self.form_html_class
        kwargs['toolgar_html_class'] = self.toolbar_html_class
        return super(BasicGridMixin, self).get_context_data(**kwargs)

    def get_grid_data(self, grid_tuples):
        """
        This method only returns grid data structure with the value of the field. Not de forms fields and it's value.

        The grid could be showing an object: display or update. In these cases It would be necessary to know the object.
        For this it will be used self.object y self.get_object() provided by, for example, SingleObjectMixin.

        :return: A Data Grid Structure prepare for the context
        """
        _data_grid = []
        _auto_row = 1
        form = self.get_form()
        if grid_tuples is not None:
            for _grid_tuple in grid_tuples:
                _model_attribute, _line_number, _label, _html_class, _is_data, _error = self.get_complete_tuple(_grid_tuple)
                _template_field = _model_attribute
                _template_label = _label
                _template_error_msj = ''
                _template_error = ''
                _field = next((item for item in form if item.name == _model_attribute), False)
                if _field:
                    if _field.name == self.primary_key:
                        self.primary_key_present = True
                    if self.read_only:
                        if self.object is not None:
                            _field.field.widget.attrs.update({
                                'form': 'grid_post_form',
                                'readonly': 'True',
                                'class': self.html_form_class,
                            })
                            _template_field = _field
                        else:
                            _template_field = ''
                    else:
                        # The value in data grid structure will be the form field (with it's value or empty)
                        _field.field.widget.attrs.update({
                            'form': 'grid_post_form',
                            'class': self.html_form_class,
                        })
                        _template_field = _field
                    if _label == '':
                        _template_label = _field.label_tag(attrs={'class': self.html_label_class,
                                                                  'for': _field.id_for_label})
                    elif _label == '__empty__':
                        _template_label = ''
                    else:
                        _field.label = _label
                        _template_label = _field.label_tag(attrs={'class': self.html_label_class,
                                                                  'for': _field.id_for_label})
                    if _field.errors.data:
                        _template_error_msj = _field.errors.data[0].messages[0]
                        _template_error = _error
                    else:
                        _template_error_msj = ''
                if _field or not _is_data:
                    if not _is_data:
                        # when _is_data = False _label could have the name of a model field.
                        if self.object is not None:
                            if _label.strip():
                                _template_field = _model_attribute.format(getattr(self.object,self.model._meta.pk.name),
                                                                      getattr(self.object,_label))
                        else:
                            # If there is no self.object mean a new one is being created: no ID and no value.
                            _template_field = _model_attribute.format('','')
                    # Exist the row in _grid_data? _grid_data = list of dicts
                    _exist_row = next((row for row in _data_grid if row['row'] == _line_number), False)
                    if _exist_row:
                        _exist_row['data'].append((_template_field, _template_label,
                                                   _html_class ,_is_data, _template_error, _template_error_msj))
                    else:
                        _row = dict(row=_line_number, data=[(_template_field, _template_label,
                                                             _html_class, _is_data, _template_error,
                                                             _template_error_msj)])
                        _data_grid.append(_row)
        else:
            self.primary_key_present = True
            for _field in form:
                _template_error = ''
                _template_error_msj = ''
                if _field.errors.data:
                    _template_error_msj = _field.errors.data[0].messages[0]
                    _template_error = 'error'
                if self.read_only:
                    if self.object is not None:
                        _field.field.widget.attrs.update({
                            'form': 'grid_post_form',
                            'readonly': 'True',
                            'class': self.html_form_class,
                        })
                        _template_field = _field
                    else:
                        _template_field = ''
                else:
                    # The value in data grid structure will be the form field (with it's value or empty)
                    _field.field.widget.attrs.update({
                        'form': 'grid_post_form',
                        'class': self.html_form_class,
                    })
                    _template_field = _field
                _row = dict(row=_auto_row, data=[(_template_field,
                                                  _field.label_tag(attrs={'class': self.html_label_class,
                                                                          'for': _field.id_for_label}),
                                                  '', True, _template_error,
                                                  _template_error_msj)])
                _data_grid.append(_row)
                _auto_row += 1
        return _data_grid

    def get_complete_tuple(self, grid_tuple):
        """
        Receive a tuple with 2 or more elements. And returns a complete grid tupe

        A complete grid tuple have the next element in the presented order:
        Required:
        * model_attribute (field)
        * row number
        With default value:
        * label
            * ''                Default value. The field.label value will be used
            * '__empty__'       There will be no label and no div html element
            * html_code         Normally will be the string with the label for the field. And should be a text to be
                                translated. But is also possible to inject html_code as label for a field. For the the
                                injection of html code, it is used Python String Syntax with the next parameter:
                                {0} object primary key
        * html_class            Default value an empty string. The CSS html class for the div cell holding all data:
                                label and value. Inside this cell there will be two <div> elements, one for the label
                                (if present), and other for the value. If an empty string is given (default value)
                                generic grid html classes will be used, and 'display: table-cell' style property will
                                be used, so when providing html_class be sure of style the cell to be a cell.
        * is_data
            * True              Default value. Means the first element is a Django Model Field and it's value will be
                                exposed.
            * False             Means that the first element is html code. It could be any thing, just an empty string
                                or any other html code, it will be used Django 'safe' filter. It is used Python String
                                Syntax with the next parameter:
                                {0} object primary key
        * error
            * ''                Default value. Default error messages for the field will be used when creating or
                                updating an object.

        The method will assume that given tuple elements (as least the first two) are given in the correct order. For
        example if complete_table_tuple receive a tuple like (A, B, C) will assume that A is a field of the model; B a
        row number; and C the label element. Then will complete the virtual grid tuple elements with default values

        :return: a complete grid virtual table tuple
        """

        _default_list = [None, None, '', '', True, 'error']  # Default values list (not for field and row).
        _tuple_len = len(grid_tuple)
        if _tuple_len > 6:
            raise TypeError("Virtual grid tuples could have up to 6 elements. More were received")
        elif _tuple_len < 2:
            raise TypeError("Virtual grid tuples could not have less than two element only.")
        for index, element in enumerate(grid_tuple):
            _default_list[index] = element
        return tuple(_default_list)

    def get_css_class(self, type, state):
        """
        Define an html style class depending on the type of field. State means: Enable or disable.
        """
        if type == "CheckboxInput":
            return {'class': self.html_class + 'detInputCheckboxInput' + state}
        elif type == "ClearableFileInput":
            return {'class': self.html_class + 'detInputClearableFileInput' + state}
        elif type == "DateInput":
            return {'class': self.html_class + 'detInputDateInput' + state}
        elif type == "DateTimeInput":
            return {'class': self.html_class + 'detInputDateTimeInput' + state}
        elif type == "EmailInput":
            return {'class': self.html_class + 'detInputEmailInput' + state}
        elif type == "HiddenInput":
            return {'class': self.html_class + 'detInputHiddenInput' + state}
        elif type == "MultipleHiddenInput":
            return {'class': self.html_class + 'detInputMultipleHiddenInput' + state}
        elif type == "NullBooleanSelect":
            return {'class': self.html_class + 'detInputNullBooleanSelect' + state}
        elif type == "NumberInput":
            return {'class': self.html_class + 'detInputNumberInput' + state}
        elif type == "Select":
            return {'class': self.html_class + 'detInputSelect' + state}
        elif type == "SelectMultiple":
            return {'class': self.html_class + 'detInputSelectMultiple' + state}
        elif type == "SplitDateTimeWidget":
            return {'class': self.html_class + 'detInputSplitDateTimeWidget' + state}
        elif type == "SplitHiddenDateTimeWidget":
            return {'class': self.html_class + 'detInputSplitHiddenDateTimeWidget' + state}
        elif type == "TextInput":
            return {'class': self.html_class + 'detInputTextInput' + state}
        elif type == "TimeInput":
            return {'class': self.html_class + 'detInputTimeInput' + state}
        elif type == "URLInput":
            return {'class': self.html_class + 'detInputURLInput' + state}


class VariableGridBaseViewMixin(BasicGridMixin, GridProcessView):
    """

    """
    phase = None
    edit_able = False
    edit_name = 'Edit'
    edit_class = ''         # CSS class for div cell where edit button lives.
    edit_button_class = ''  # CSS class for edit button
    _update_able = None
    update_name = 'Update'
    update_class = ''         # CSS class for div cell where update button lives.
    update_button_class = ''  # CSS class for update button
    _new_able = None
    new_name = 'Save'
    new_class = ''         # CSS class for div cell where new button lives.
    new_button_class = ''  # CSS class for new button

    def get(self, request, *args, **kwargs):
        """

        :param template:
        :param model:
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        self.read_only = True
        # 17:30 hasta 17:34
        #try:
        #    self.object = self.get_object()
        #except:
        #    raise TypeError("VariableGridBaseViewMixin could not found and objecto to expose.")
        try:
            self.object = self.get_object()
        except:
            self.object = None
        if self.object is not None:
            self.form_instance = self.get_form()
            if 'edit' in request.GET:
                self._update_able = True  # Needed by template.
                self.edit_able = False
                self.read_only = False  # get_grid_data will know it must use Model Form for updating object.
                self.phase = 'update'
                # Translators: This message goes trough Django's messages framework with messages.success
                messages.success(request, _('You are editing registry: ') + kwargs['pk'])
            else:
                self.phase = 'expose'
                # Translators: This message goes trough Django's messages framework with messages.success
                messages.success(request, _('Watching registry: ') + kwargs['pk'])
        else:  # No pk means a new object is beeing created.
            self._new_able = True  # Needed by template.
            self.edit_able = False
            self.read_only = False  # get_grid_data will know it must use Model Form for a new object.
            self.object = None
            self.form_instance = self.get_form()
            self.phase = 'new'
            # Translators: This message goes trough Django's messages framework with messages.success
            messages.success(request, _('Creating a new registry.'))
        return super(VariableGridBaseViewMixin, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """

        :param template:
        :param model:
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        self.read_only = False
        if self._update_able is None and 'update' in request.POST:
            # The only way to arrive to this post method is by html form action. In that case self._update_able should
            # be True. If now is None and we are in post means something go wrong with the form.
            self._update_able = True
        elif self._new_able is None and 'new' in request.POST:
            # The only way to arrive to this post method is by html form action. In that case self._update_able should
            # be True. If now is None and we are in post means something go wrong with the form.
            self._new_able = True
        if 'new' in request.POST:
            self._new_object_flag = True
            return self.generic_new(request, *args, **kwargs)
        elif 'update' in request.POST:
            self._new_object_flag = True
            self.object = self.get_object()
            return self.generic_update(request, *args, **kwargs)
        else:
            raise TypeError("Error IN GRID VIEW POST METHOD nothing to do!!!!")

    def get_context_data(self,**kwargs):
        """
        The next context variables are added:
        * edit_able
        * edit_name
        * edit_class            edit_class = '' is default value. Is the CSS class for div cell where edit button lives.
        * edit_button_class     edit_button_class = '' is default value. Is the CSS class for edit button
        * _update_able          For internal use. When is True means the grid is in updating state.
        * update_name           The name for update button.
        * update_class          update_class = '' is default value. Is the CSS class for div cell where update button
                                lives.
        * update_button_class   update_button_class = '' is default value. Is the CSS class for update button.
        * _new_able             For internal use. When is True means a new object is being created.
        * new_name
        * new_class            edit_class = '' is default value. Is the CSS class for div cell where edit button lives.
        * new_button_class     edit_button_class = '' is default value. Is the CSS class for edit button
        """
        #context = super(VariableGridBaseViewMixin, self).get_context_data(**kwargs)
        # Add to context the template context variables
        kwargs['edit_able'] = self.edit_able
        kwargs['edit_name'] = self.edit_name
        kwargs['edit_class'] = self.edit_class
        kwargs['edit_button_class'] = self.edit_button_class
        kwargs['update_able'] = self._update_able
        kwargs['update_name'] = self.update_name
        kwargs['update_class'] = self.update_class
        kwargs['update_button_class'] = self.update_button_class
        kwargs['new_able'] = self._new_able
        kwargs['new_name'] = self.new_name
        kwargs['new_class'] = self.new_class
        kwargs['new_button_class'] = self.new_button_class
        kwargs['request'] = self.request
        return super(VariableGridBaseViewMixin, self).get_context_data(**kwargs)

    def generic_new(self, request, *args, **kwargs):
        """

        :param template:
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        self.object = None
        self.form_instance = self.get_form()
        return super(VariableGridBaseViewMixin, self).post(request, *args, **kwargs)

    def generic_update(self, request, *args, **kwargs):
        """

        :param template:
        :param model:
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        self.form_instance = self.get_form()  # Needed when form is not valid and need errors as feedback.
        return super(VariableGridBaseViewMixin, self).post(request, *args, **kwargs)
        # self.form_instance = self.get_form()
        # template = self.get_template()
        # request_context = RequestContext(request)
        #
        # # self.form_instance = self.model_form(request.POST or None, instance=model)
        # if self.form_instance.is_valid():
        #     self.form_instance.save()
        #     # Translators: This message goes trough Django's messages framework with messages.success
        #     messages.success(request, _('It has been modify the registry: ') + kwargs['pk'])
        #     context = self.get_context_data(**kwargs)
        # else:
        #     # Translators: This message goes trough Django's messages framework with messages.error
        #     messages.error(request, _('The form has fail for registry: ') + kwargs['pk'])
        #     context = super(GridObjectMixin, self).get_context_data(form=self.form_instance)
        #     request_context.push(context)
        #     context = self.get_context_data(**kwargs)
        # request_context.push(context)
        # return HttpResponse(template.render(request_context))


class ParentGridBaseViewMixin(VariableGridBaseViewMixin):
    """

    """
    child_table_view = None

    def get(self, request, *args, **kwargs):
        """

        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        if self.child_table_view is None:
            raise ImproperlyConfigured("ParentGridBaseViewMixin require child_table_view attribute.")
        return super(ParentGridBaseViewMixin, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """

        :param kwargs:
        :return:
        """
        if self.object is not None:
            kwargs['child_table_view'] = self.app_name + ':' + self.child_table_view
            kwargs['parent_id'] = getattr(self.object, self.object._meta.pk.name)
        return super(ParentGridBaseViewMixin, self).get_context_data(**kwargs)


class ChildGridBaseViewMixin(VariableGridBaseViewMixin):
    """

    """
    parent_model = None
    foreign_key = None
    _parent_id = None

    def __init__(self):
        """

        """
        super(ChildGridBaseViewMixin, self).__init__()
        if self.parent_model is None:
            raise ImproperlyConfigured("ChildGridBaseViewMixin require parent_model attribute.")
        if self.foreign_key is None:
            raise ImproperlyConfigured("ChildGridBaseViewMixin require foreign_key attribute.")


    def get(self, request, *args, **kwargs):
        """

        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        _get_data = request.GET
        if 'parent_id' in _get_data:
            self._parent_id = _get_data.get('parent_id')
            self.back_view_id = self._parent_id
        return super(ChildGridBaseViewMixin, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """

        :param kwargs:
        :return:
        """

        # TODO Esta parte del codigo puede ser algo sucia, es para que funcione el boton back: Analizar.
        if self.back_view_id is None:
            # Exposing an object.
            self.back_view_id = getattr(self.object, self.foreign_key + '_id')
            kwargs['back_view_id'] = self.back_view_id
        else:
            kwargs['back_view_id'] = self.back_view_id
        # search if self.foreign_key exist in grid
        _is_present_FKey = False
        if self.grid is not None:
            # A grid has been defined and fields (like foreign_key) could be missing.
            for tuple in self.grid:
                if tuple[0] == self.foreign_key:
                    _is_present_FKey = True
        if not _is_present_FKey and self.grid is not None:
            kwargs['is_present_FKey'] = _is_present_FKey
            kwargs['foreign_key_field'] = self.foreign_key
            if self.object is None:
                # Creating a new element
                kwargs['foreign_key_value'] = self._parent_id
            else:
                # updating a new element
                kwargs['foreign_key_value'] = getattr(self.object, self.foreign_key + '_id')
        return super(ChildGridBaseViewMixin, self).get_context_data(**kwargs)


class BasicGridView(GridTemplateResponseMixin, BasicGridMixin, GridBaseViewMixin):
    """

    """


class GridView(VariableGridTemplateResponseMixin, VariableGridBaseViewMixin):
    """

    """


class ParentGridView(ParentGridTemplateResponseMixin, ParentGridBaseViewMixin):
    """

    """


class ChildGridView(ChildGridTemplateResponseMixin, ChildGridBaseViewMixin):
    """

    """
