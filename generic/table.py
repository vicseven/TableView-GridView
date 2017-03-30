import operator
from functools import reduce
from django.core.exceptions import ImproperlyConfigured
from django.forms import models as model_forms
from django.core.paginator import PageNotAnInteger, EmptyPage
from django.db.models import Q
from django.views.generic.base import View, ContextMixin
from django.views.generic.list import MultipleObjectMixin
from django.views.generic.detail import SingleObjectMixin
from django.template import engines
from django.template import Template, RequestContext, Context
from django.template.response import TemplateResponse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _


from .TableTemplate import toolbar_table_html, \
    table_tb_processes1, table_tb_processes2, table_tb_buttons1, table_tb_buttons2, \
    base_head_html, \
    form_table_html, \
    form_create_table_html, \
    search_table_html, \
    titles_table_html, \
    filter_table_html, \
    content_table_html, \
    page_table_html, \
    toolbar_child_table_html, \
    form_create_child_table_html
from .images import search_png, delete_png, order_a_png, order_d_png


class SortMixin(ContextMixin):
    """
    SortMixin returns a field name to sort by or None:
        * None: No sort at all is given or have exist in previous sessions.
        * field: No sort is given; but exist last_sort meaning that in a previous session a sort exist, so the same sort
        is returned.
        * field: A sort is given by sort_by; but there is no last_sort. This means is the first time a sort is asked
        for.
        * field: Is given values for sort_by and last_sort. This means in previous session a sort exist. If last_sort is
        the same than sort_by, the order will be revers with minus ('-').

    SortMixin expect the next parameter be deliver by GET request:
    * request.GET
    * sort_by
    * last_sort
????Also expect the attribute initial_order be set to the name of a model field.

    If empty string is received as GET parameter (no sort_by parameter) initial_order will be used. If no
    initia_order is supplied SortMixin will raise an "No initial order" error.
    """
    sort_by = None
    last_sort = None

    def get_sort_by(self, request):
        try:
            sort_data = request.GET
        except Exception as err:
            print('SortMixin error receiving sort data: ', err)

        self.sort_by = sort_data.get('sort_by')
        self.last_sort = sort_data.get('last_sort')
        if self.sort_by is None or self.sort_by == '':
            # Case: when no sort is given.
            if self.last_sort is None or self.last_sort == '':
                # Case: No sort at all.
                return None
            else:
                # Case: No sort is given; but exist last_sort
                self.sort_by = self.last_sort
                return self.sort_by
        elif self.last_sort is not None or self.last_sort != '':
            # Case: when sort_by and last_sort are given
            if self.sort_by == self.last_sort:
                self.sort_by = '-' + self.last_sort
        # Case: when sort_by is given but not last_sort: first sort is being required.
        # But if a sort is given (with or without last_sort) the required sort became in the last one.
        self.last_sort = self.sort_by
        return self.sort_by

    def get_context_data(self, **kwargs):
        """

        """
        if self.last_sort is None:
            self.last_sort = ''
        kwargs['last_sort'] = self.last_sort
        kwargs['order_a_png'] = order_a_png
        kwargs['order_d_png'] = order_d_png
        return super(SortMixin, self).get_context_data(**kwargs)


class SearchMixin(MultipleObjectMixin):
    """
    Search and/or filter over self.queryset.

    If self.queryset not exist, or if it is None, SearchMixin will call self.get_queryset()
    Values and fields for Filter must be supplied through GET parameters.
    Fields and criteria for Search must be declared in search_by list. Search values must be supplied
    through GET 'search' parameter.
    """
    search_by = []
    filter_behavior = '__icontains'
    search_data = None
    search_for = None
    filter_able = False
    search_able = False
    search_default = True # When True will show by default search field and not filters fields
    _doing_search = None  # Internal attribute for knowing when the user is doing a filter or a search.
                          # takes precedence the search.

    def get_search_result(self, request):
        """
        Is used a context variable of name doing_search that is recover from request.GET. When both filter and search
        are able, this internal attribute helps to determine if web user is doing a search or a filter.
        Process search data suminstrated by web user
        """
        if self.queryset is None or not self.queryset.exist():
            self.queryset = self.get_queryset()

        if self.search_able and not self.search_by:
            raise TypeError("SearchMixin says: search_by can not be empty if search_able is True.")
        try:
            self.search_data = request.GET
        except Exception as err:
            print('Error processing search options: ', err)
        self.search_for = self.search_data.get('search')
        if self.search_for is None:
            self.search_for = ''
        self._doing_search = self.search_data.get('doing_search')
        if self._doing_search != 'False':
            fields = self.model._meta.get_fields()
            for field in fields:
                if field.name in self.search_data:
                    search_value = self.search_data[field.name]
                    if search_value != '':
                        # Each time user do a search the filters are cleaned. So if the user was doing a search, that is
                        # self._doing_search, but a value in filter field is not clean, means user start doing a filter.
                        self._doing_search = 'False'
                        self.search_for = ''

        if self.search_for != '' and self.search_able:
            if self.search_able:
                self._doing_search = 'True'
                search_list = [Q((search_field + search_criteria, self.search_for)) for search_field, search_criteria in self.search_by]
                self.queryset = self.get_queryset().filter(reduce(operator.or_, search_list))
        elif self.filter_able:
            if self._doing_search == 'False':
                fields = self.model._meta.get_fields()
                for field in fields:
                    if field.name in self.search_data:
                        search_value = self.search_data[field.name]
                        if search_value != '':
                            self.queryset = self.queryset.filter(**{field.name + self.filter_behavior: search_value})
        return self.queryset

    def get_context_data(self, **kwargs):
        """

        """
        if self.search_for is None:
            self.search_for = ''
        kwargs['search_able'] = self.search_able
        kwargs['search'] = self.search_for
        kwargs['search_by'] = self.search_by
        kwargs['doing_search'] = self._doing_search
        kwargs['filter_able'] = self.filter_able
        kwargs['search_png'] = search_png
        return super(SearchMixin, self).get_context_data(**kwargs)


class TableBaseMixin(SearchMixin, SortMixin):
    """
    Implement the logic and prepare a context with data structures for building a data table from a set of object
    belonging to a model. MultipleObjectMixin (parent of SearchMixin) give access to multiple paged object. SearchMixin
    and SortMixin provides search and sort (columns click) capabilities to the data table.

    Implements the logic for virtual table tuples, their definition are used to build context data structures.
    A virtual table tuple is a 7 element tuple:
    (field, title, data_html_class='', title_html_class='', filter=False, filter_html_class='', data=True)
    filter could be:   * False (deault)     = No filter for the column
                       * True               = filter field will be justa an <input type="textarea" ...
                       * '__form__'         = model form will be used to build the filter for the field.
                       * html_code          = the element is injected as html_code using Djando safe filter.
                                            html_code works with Python Format Sting Syntax,
                                            this means that html_code will be formatted receiving as first argument
                                            ({0}) the searched value if any.
    data could be:     * True (default)     = The data shown in each row is the one provided by the field element
                                            of the tuple (1st one), been it an attribute of the model.
                       * '__form__'         = The data shown in each row is the one provided by the model form, were
                                            field tuple element will be used to select the appropriate field form.
                       * html_code          = data tuple element content is injected as HTML code with the use of
                                            Django safe filter. html_code works with Python Format Sting Syntax,
                                            this means that html_code will be formatted receiving as first argument
                                            ({0}) the field value, and as second argument ({1}) object's id.
    And the _html_class is the name of the CSS Style class or classes, for example a <td> element with a value of
    data_html_class = 'MyStyleClass' will be <td class="MyStyleClass">
        * title_html_class  = Will be used for the cells holding columns titles (<th> or a cell if using <div>)
        * filter_html_class = Will be used for the cells holding the filters HTML fields for user to filter with them.
        * data_html_class   = Will be used fo the cells holding columns data (<td> or a cell if using <div>)
    Keep in main that _html_class are for cells, together will implement the Style for the entire column (from the Title
    to the data cells) defined by the virtual table tuple.
    """
    model_form = None
    primary_key = None  # Needed to implement processes, link to detail, and initial order.
    columns = None      # A list of virtual table tuples in the order in which they will be exposed as columns.
    processes = None    # A list of tuples: (process_name, process_view, html_title_code)
    processes_class = None
    link_to_detail = False  # Must be True to show details of each row. A sub class of GridView's classes must exist
    detail_view_name = ''   # Must be the name of the view of the sub class of GridView's classes for the model.
    delete_able = False
    delete_class = ''
    delete_title_attributes = None
    reset_able = False
    reset_class = ''
    create_able = False
    create_class = ''
    paginate_by = 25

    # Template attributes
    toolbar_buttons = None  # List of tuples: (button_name, html_attributes)
    toolbar_html_class = None
    html_class = ''
    filter_tag_attributes = None # 'id="table_filter_tr"'
    search_tag_attributes = None #'id="genTabSearch_form"'
    # Not public attributes
    _app_name = ''
    _actual_page = 1

    def __init__(self):
        """
        When creating an instance of the view it will be checked for the definition of two attributes:
        * model: A model must by supplied. Is the model to be exposed as a table.
        * model_form: Can be supplied or the init will create one for the given model. The form in TableView classes
        is used when in a virtual tuple is used the '__form__' value.
        """
        if self.model is None:
            raise ImproperlyConfigured("TableBaseMixin: model attribute must be provided.")
        if self.model_form is None:
            self.model_form = model_forms.modelform_factory(self.model, fields='__all__')
        if self.primary_key is None:
            self.primary_key = self.model._meta.pk.name

    def get_context_data(self, **kwargs):
        """
        Actions made by get_context_data
        * Create the processes context variable (empty or not)
        * Call get_table_data to obtain the data structure needed by the template to draw an 'html data table'
        * Provide the context variables needed by table template.

        Create the process context variable
        Manipulate the 'processes' attribute an generate a Python List (_processes_link) of tuples with 4 elements:
        (process_name, process_view, title_html_code, and a Django URL element: app_name:process_view that can be
        used, for example: {% url 4th_tuple_element %} to create a link to the view implementing the process. The list
        is then passed to context as 'processes'

        :returns a context
        """
        _processes_link = []
        if self.processes is not None:
            for process_name, process_view, html_code, form_attribute in self.processes:
                _processes_link.append((process_name, process_view, html_code,
                                        self._app_name + ':' + process_view, form_attribute))
                kwargs['processes'] = _processes_link
        kwargs['processes_class'] = self.processes_class
        # If create_able = True found the name to use in the button
        if self.model._meta.verbose_name is None:
            kwargs['object_name'] = self.model._meta.verbose_name

        # Construct data structures to build a data table
        data_title, data_filter, data_table = self.get_table_data()
        kwargs['data_table'] = data_table
        kwargs['data_filter'] = data_filter
        kwargs['data_title'] = data_title

        kwargs['detail_url'] = self._app_name + ':' + self.detail_view_name
        kwargs['link_to_detail'] = self.link_to_detail
        kwargs['create_able'] = self.create_able
        kwargs['create_class'] = self.create_class
        kwargs['delete_title_attributes'] = self.delete_title_attributes
        kwargs['reset_able'] = self.reset_able
        kwargs['reset_class'] = self.reset_class
        kwargs['delete_able'] = self.delete_able
        kwargs['delete_class'] = self.delete_class
        kwargs['page'] = self._actual_page

        kwargs['delete_png'] = delete_png
        kwargs['html_class'] = self.html_class
        kwargs['toolbar_html_class'] = self.toolbar_html_class
        kwargs['toolbar_buttons'] = self.toolbar_buttons
        kwargs['filter_tag_attributes'] = self.filter_tag_attributes
        kwargs['search_tag_attributes'] = self.search_tag_attributes
        kwargs['id_field'] = self.primary_key
        return super(TableBaseMixin, self).get_context_data(**kwargs)

    def get_complete_tuple(self, _tuple):
        """
        Receive a tuple with 7 or less elements. And complete the virtual table tuple with default values.

        The method will assume that given tuple element (as least the 1st one) are given in the correct order. For
        example if complete_table_tuple receive a tuple like (A, B, C) will assume that A is a field of the model; B a
        column title; and C the filter element. Then will complete the virtual table tuple elements with default values

        :return: a complete 7 element virtual table tuple
        """
        _tuple_len = len(_tuple)
        if _tuple_len > 7:
            raise TypeError("Virtual table tuples could have up to 7 elements. More were received")
        elif _tuple_len > 6:
            # virtual table tuple is complete
            return _tuple
        elif _tuple_len > 5:
            # virtual table tuple have 6 elements, missing data
            return _tuple + (True,)
        elif _tuple_len > 4:
            # virtual table tuple have 5 elements, missing filter_html_class, and data
            return _tuple + ('', True)
        elif _tuple_len > 3:
            # virtual table tuple have 4 elements, missing filter, filter_html_class, and data
            return _tuple + (False, '', True)
        elif _tuple_len > 2:
            # virtual table tuple have 3 elements, missing title_html_class, filter, filter_html_class, and data
            return _tuple + ('', False, '', True)
        elif _tuple_len > 1:
            # virtual table tuple have 2 elements, missing data_html_class, title_html_class, filter, ...
            return _tuple + ('', '', False, '', True)
        else:
           raise TypeError("Virtual table tuples could not have 1 element only.")

    def get_table_data(self):
        """
        Prepare the 3 data structures needed for building a data table

        :return: A tuple of 3 elements with data structures needed for building a table
        (_data_title, _data_filter, _data_table)
         _data_title: Is a Python List of dictionaries. Each dictionary have 3 elements: 'name', 'title', and 'class'.
         'name' is the field name, is used for implementing sort when user cilcks on a title. 'title' is the
         title of the column; 'class' is the HTML class for title's cells
         _data_filter: Is a Python List of dictionaries. Each dictionary have two elements: 'filter' and 'class'.
         'filter' is for being injected as html_code with Django template's safe filter; 'class' is the HTML class for
         filter cells.
         _data_table: Is a Python List of dictionaries. Each tuple have two elements 'id' and 'columns'. 'id' is the
         primary key value of the object been exposed in a row. 'columns' is a python list with 2 values: first element
         is the value of the object for each column; second element is True o False indicating if Django template
         safe filter must be used or not.
        """
        _data_table = []
        _data_title = []
        _data_filter = []
        _data_filter_complete = False   # Used for not rebuilding this data for each object.
        _data_title_complete = False    # Used for not rebuilding this data for each object.

        if self.columns is None:
            for field in self.model._meta.get_fields():
                # Also incorporate the ManyToOne fields
                self.columns.append((field.name,field.name))
        try:
            _objects = self.get_paginator(self.object_list, self.paginate_by).page(self._actual_page)
        except PageNotAnInteger:
            raise TypeError("The page number is not an integer.")
        except EmptyPage:
            raise TypeError("The table is empty. Try defining allow_empty = True.")
        except Exception as err:
            raise TypeError("Unknown error: " + err.__cause__ + " doc:" + str(err.__doc__))

        for object in _objects:
            _table_row = {'id': getattr(object,self.primary_key),
                          'columns': []
                          }
            for tuple in self.columns:
                field, title,\
                    data_html_class, title_html_class,\
                    _filter, filter_html_class, data = self.get_complete_tuple(tuple)
                # As this is the main algorithm were tuple are analysed and data structures for context are build,
                # are 3 data structures: for titles rows(_data_title), for filter rows(_data_filter), and for
                # data rows(_data_table).

                # Building _data_table
                _value = getattr(object,field)
                if data == True:
                    if _value == '' or _value == None:
                        _table_row['columns'].append(('', False))
                    else:
                        _table_row['columns'].append((_value, False))
                elif data == '__form__':
                    _form_field = self.model_form(None).fields[field]
                    _form_field.initial = _value
                    _table_row['columns'].append((
                        _form_field.widget.render(field, _value, attrs={'readonly': 'readonly',
                                                                        'style': 'border: none;'}),
                        False))
                else:
                    _table_row['columns'].append((data.format(_value, getattr(object,self.primary_key)), True))
                # Building _data_title
                if not _data_title_complete:
                    _data_title.append({
                        'name': field,
                        'title': title,
                        'class': title_html_class,
                    })
                # Building _data_filter
                if self.filter_able:
                    if not _data_filter_complete:
                        _value = self.search_data.get(field)
                        if _value is None or self._doing_search == 'True':
                            # The next condition empty any filter field if a search is in process.
                            _value = ''
                        if _filter == True:
                            _data_filter.append({
                                'filter': '<input type="text" form="table_get_data" name="'
                                          + field
                                          + '" onkeypress="if (event.keyCode==13) document.getElementById(\'search_flag\').value=1" value="'
                                          + _value
                                          + '" placeholder="'
                                          + _('Search for ...') + '"/>',
                                'class': filter_html_class
                            })
                        elif _filter == False:
                            _data_filter.append({
                                'filter': '',
                                'class': filter_html_class
                            })
                        else:
                            if _filter == '':
                                raise ImproperlyConfigured(
                                    "In virtual table tuple a value for filter element can not be an empty string.")
                            elif _filter == '__form__':
                                _form_field = self.model_form(None).fields[field]
                                if _value is not None:
                                    _form_field.initial = _value
                                _data_filter.append({
                                    'filter': _form_field.widget.render(field, _form_field.initial,
                                                                        attrs={
                                                                            'form': 'table_get_data',
                                                                        }),
                                    'class': filter_html_class
                                })
                            else:
                                # when _filter have html code.
                                _data_filter.append({
                                    'filter': _filter.format(_value),
                                    'class': filter_html_class
                                })
            _data_table.append(_table_row)
            _data_filter_complete = True
            _data_title_complete = True

        return (_data_title, _data_filter, _data_table)

    def get_queryset(self):
        return self.model.objects.all()


class ChildTableBaseMixin(TableBaseMixin):
    """

    """

    foreign_key = None

    def __init__(self):
        """

        """
        super(ChildTableBaseMixin, self).__init__()
        if self.model is None:
            raise ImproperlyConfigured("ChildTableBaseMixin require model attribute.")
        if self.foreign_key is None:
            raise ImproperlyConfigured("ChildTableBaseMixin require foreign key attribute.")

    def get_context_data(self, **kwargs):
        """

        """
        kwargs['parent_model'] = self.parent_model
        kwargs['parent_id'] = self.parent_id
        kwargs['foreign_key'] = self.foreign_key
        return super(ChildTableBaseMixin, self).get_context_data(**kwargs)

    def get_queryset(self):
        _foreign_search = '' + self.foreign_key + '__pk'
        return self.model.objects.filter(**{_foreign_search: self.parent_id})


class TableTemplateResponseMixin(object):

    template_name = None
    template_engine = None
    response_class = TemplateResponse
    content_type = None
    base_template_block = '{% block content %}'
    extend_html = None

    # Template attributes
    table_attribute = ''        # Used to add attributes to main HTML <table> tag
    toolbar_attribute = ''      # Used to add attributes to tool bar HTML <table> tag
    process_html_tag_open = '<td>'
    process_html_tag_close = '</td>'
    buttons_html_tag_open = '<td>'
    buttons_html_tag_close = '</td>'

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
        template_code = '{% extends "' + self.extend_html + '" %}' \
                        + self.base_template_block \
                        + base_head_html \
                        + '<!-- Start Table Tool Bar Block -->{% block table_tool_bar %}<table ' \
                        + self.toolbar_attribute + ' ><tr>' \
                        + toolbar_table_html \
                        + table_tb_processes1 \
                        + self.process_html_tag_open \
                        + '<input class="{{ processes_class }}" form="id_{{ process_view }}" type="submit" value="{{ process_name }}">' \
                        + self.process_html_tag_close \
                        + table_tb_processes2 \
                        + table_tb_buttons1 \
                        + self.buttons_html_tag_open \
                        + '<button {{ html_attributes|safe }} >{{ button_name }}</button>' \
                        + self.buttons_html_tag_close \
                        + table_tb_buttons2 \
                        + '</tr></table>{% endblock %}<!-- End Table Tool Bar Block -->' \
                        + form_table_html \
                        + form_create_table_html \
                        + search_table_html \
                        + '<table ' + self.table_attribute + ' >' \
                        + titles_table_html \
                        + filter_table_html \
                        + content_table_html \
                        + '</table><hr>'  \
                        + page_table_html \
                        + '{% endblock %}'
        self.template_name = engines['django'].from_string(template_code)
        return self.template_name


class ChildTableTemplateResponseMixin(TableTemplateResponseMixin):
    """
    Get a child table template code.
    Attributes
    * parent_model: REQUIRED!! It is the 'One' Django Model in ManyToOne relation ship. ChildTableView show a data
    table of the 'Many' Djando Model in ManyToOne relation ship.
    """
    parent_model = None # Required.

    def get_template(self):
        template_code = '{% extends "' + self.extend_html + '" %}' \
                        + self.base_template_block \
                        + base_head_html \
                        + '<!-- Start Table Tool Bar Block -->{% block table_tool_bar %}<table ' \
                        + self.toolbar_attribute + "><tr>" \
                        + toolbar_child_table_html \
                        + table_tb_processes1 \
                        + self.process_html_tag_open \
                        + '<input class="{{ processes_class }}" form="id_{{ process_view }}" type="submit" value="{{ process_name }}">' \
                        + self.process_html_tag_close \
                        + table_tb_processes2 \
                        + table_tb_buttons1 \
                        + self.buttons_html_tag_open \
                        + '<button {{ html_attributes|safe }} >{{ button_name }}</button>' \
                        + self.buttons_html_tag_close \
                        + table_tb_buttons2 \
                        + '</tr></table>{% endblock %}<!-- End Table Tool Bar Block -->' \
                        + form_table_html \
                        + form_create_child_table_html \
                        + search_table_html \
                        + '<table ' + self.table_attribute + '>' \
                        + titles_table_html \
                        + filter_table_html \
                        + content_table_html \
                        + '</table><hr>'  \
                        + page_table_html \
                        + '{% endblock %}'
        self.template_name = engines['django'].from_string(template_code)
        return self.template_name


class BaseTableView(View):
    """
    Provides Base Table View functions.

    """
    table_order = None
    _url_data = None

    def get(self, request, *args, **kwargs):
        self._app_name = request.resolver_match.app_name
        self._app_namespace = request.resolver_match.namespace
        self._url_data = self.request.GET
        if 'page' in self._url_data:
            self._actual_page = self._url_data.get('page')
        else:
            self._actual_page = 1
        self.table_order = self.get_sort_by(request)
        if self.table_order is None:
            self.table_order = '-' + self.primary_key
        self.object_list = self.get_search_result(request).order_by(self.table_order)
        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        self._app_name = request.resolver_match.app_name
        self._app_namespace = request.resolver_match.namespace
        return self.generic_delete(request, *args, **kwargs)

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


class BaseCommonTableView(TableTemplateResponseMixin, BaseTableView):
    """

    """


class BaseChildTableView(ChildTableTemplateResponseMixin, BaseTableView, SingleObjectMixin):
    """

    """
    # Review this
    parent_id = None

    def get(self, request, *args, **kwargs):
        """

        """
        self.object = self.get_object(self.parent_model.objects.all())
        if self.object is None:
            raise TypeError("Child Table cant find a parent object.")
        self.parent_id = getattr(self.object, self.parent_model._meta.pk.name)
        return super(BaseChildTableView, self).get(request, *args, **kwargs)


class TableView(TableBaseMixin, BaseCommonTableView):
    """
    Provides a finished view of any model's data exposed as a table.

    Expose data of any model in a table standard view. The user is able to
    order, filter, or search data. Paged is default to 25 rows.
    """


class ChildTableView(ChildTableBaseMixin, BaseChildTableView):
    """

    """

