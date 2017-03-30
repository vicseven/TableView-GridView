# TODO Todavia queda JavaScript en los titulos, la paginacion y en el borrado.

table_tb_reset = """
<!-- Start Block for Reset button -->
{% block table_tb_reset %}
  {% if reset_able %}
    <input class="{{ reset_class }}" form="table_get_reset" type="submit" value="{% trans "Reset" context "Reset button option" %}">
  {% endif %}
{% endblock %}
<!-- End Block for Reset button -->
"""

table_tb_create = """
<!-- Start Block Create Object Button -->
{% block table_tb_create %}
  {% if link_to_detail and create_able %}
    <input class="{{ create_class }}" form="table_create" type="submit" value="{% trans 'Create' context 'Create for delete rows' %} {{ object_name }}">
  {% endif %}
{% endblock %}
<!-- End Block Create Object Button -->
"""

table_tb_delete = """
<!-- Start Blcok Delete Process button -->
{% block table_tb_delete %}
  {% if delete_able %}
    <input class="{{ delete_class }}" form="table_delete" type="submit" value="{% trans 'Delete' context 'Button for delete rows' %}">
  {% endif %}
{% endblock %}
<!-- End Bock Delete Process -->
"""

table_tb_processes1 = """
<!-- Start Block Declared Process Buttons -->
{% block table_tb_processes %}
  {% if processes %}
    {% for process_name, process_view, html_code, link_process_view, form_attribute in processes %}"""

table_tb_processes2 = """
    {% endfor %}
  {% endif %}
{% endblock %}
<!-- End Block Declared Process Buttons -->
"""

table_tb_buttons1 = """
<!-- Start Block Declared Buttons -->
{% block table_tb_buttons %}
  {% if toolbar_buttons %}
    {% for button_name, html_attributes in toolbar_buttons %}"""

table_tb_buttons2 = """
    {% endfor %}
  {% endif %}
{% endblock %}
<!-- End Block Declared Buttons -->
"""

toolbar_table_html = """{% if reset_able %}<td>""" \
                     + table_tb_reset \
                     + """{% endif %}{% if link_to_detail and create_able %}</td><td>""" \
                     + table_tb_create \
                     + """{% endif %}{% if delete_able %}</td><td>""" \
                     + table_tb_delete \
                     + """{% endif %}</td>"""


base_head_html = "{% load i18n %}{% load dictionary %}"

form_table_html = """
<!-- Start Block for FormTemplate's Forms -->
{% block table_template_forms %}
{% if reset_able %}
  <form method='get' id="table_get_reset" action='#'></form>
{% endif %}
{% if delete_able %}
  <form method="post" id="table_delete" action="#" onsubmit="return confirm('{% trans 'Please confirm you want to delete selected items' context 'Delete row confirmation message' %}')">
    {% csrf_token %}
  </form>
{% endif %}
{% if processes %}
  {% for process_name, process_view, html_code, link_process_view, form_attributes in processes %}
    <form method="post" id="id_{{ process_view }}" action="{% url link_process_view %}" {{ form_attributes|safe }} >
      {% csrf_token %}
    </form>
  {% endfor %}
{% endif %}
<form method="get" id="table_get_data" name="table_get_data" action="#"></form>
<input type="hidden" id="last_sort" name='last_sort' value='{{ last_sort }}' form='table_get_data'>
<input type="hidden" id="sort_by" name="sort_by" value="" form="table_get_data">
<input type="hidden" id="doing_search" name="doing_search" value="{{ doing_search }}" form="table_get_data">
{% endblock %}
<!-- End Block for FormTemplate's Forms -->
"""

form_create_table_html = """
<!-- Start Block for FormTemplate's Forms -->
{% block table_create_template_forms %}
{% if link_to_detail and create_able %}
    <form method="get" id="table_create" action="{% url detail_url %}" ></form>
{% endif %}
{% endblock %}
<!-- End Block for FormTemplate's Forms -->
"""

search_table_html = """<!-- Start search block -->
{% block table_search %}
    {% if search_able %}
      <div {% if search_tag_attributes %} {{ search_tag_attributes|safe }} {% endif %} >
        <input class="" form="table_get_data" type="text" name="search"  value="{{ search }}" placeholder="{% trans 'Search for' context 'Search for message' %}...">
        <input class="" form="table_get_data" type="image" src="data:image/png;base64,{{ search_png }}" alt="Submit">
      </div>
    {% endif %}
{% endblock %}
<!-- End search block -->"""

content_table_html = """<!--Start table content block -->
{% block table_data %}
<tbody>
  {% for row in data_table %}
    <tr>
      {% with row|get_item:'columns' as columns_data %}
        {% for data, safe_filter in columns_data %}
          <td>
            {% if link_to_detail %}
              <a class="" href="{% url detail_url row|get_item:'id' %}">{% if safe_filter %}{{ data|safe }}{% else %}{{ data }}{% endif %}</a>
            {% else %}
              {% if safe_filter %}{{ data|safe }}{% else %}{{ data }}{% endif %}
            {% endif %}
          </td>
        {% endfor %}
      {% endwith %}
      {% if delete_able %}
          <td>
            <input form="table_delete" class="{{ html_class|add:'genTab'}} {{ html_class|add:'genTabInputDelete'}}" type="checkbox" name="delete" value="{{ row|get_item:'id' }}">
          </td>
      {% endif %}
      {% if processes %}
          {% for process_name, process_view, html_code, link_process_view, form_attribute in processes %}
            <td>
              <input form="id_{{ process_view }}" class="{{ html_class|add:'genTab'}} {{ 'genTabDataInput'|add:process_view}}" type="checkbox" name="{{ process_view }}" value="{{ row|get_item:'id' }}">
            </td>
          {% endfor %}
      {% endif %}
    </tr>
  {% endfor %}
{% endblock %}
</tbody>
<!-- End table content block -->"""

titles_table_html = """
<!--Start columns titles-->
{% block table_columns_titles %}
<thead>
  <tr>
    {% for title in data_title %}
      <th class="{{ title|get_item:'class' }}">
        <a class="a_title_{{ title|get_item:'name' }}" href="" onclick="document.getElementById('sort_by').value='{{ title|get_item:'name' }}';document.getElementById('table_get_data').submit(); return false;">
         {{ title|get_item:'title' }}
        </a>
          {% with title|get_item:'name' as sort_name %}
            {% with '-'|add:sort_name as nfield %}
              {% if last_sort == sort_name %}
                <img alt="{% trans 'Sort desceden' context 'alt attribute in <img> html tag' %}" class="{{ html_class|add:'genTab'}} {{ html_class|add:'genTabSortD'}}" src="data:image/png;base64,{{ order_d_png }}">
              {% endif %}
              {% if last_sort == nfield %}
                <img alt="{% trans 'Sort ascendt' context 'alt attribute in <img> html tag' %}" class="{{ html_class|add:'genTab'}} {{ html_class|add:'genTabSortA'}}" src="data:image/png;base64,{{ order_a_png }}">
              {% endif %}
            {% endwith %}
          {% endwith %}
      </th>
    {% endfor %}
    {% if delete_able %}
      <th>
        {% if delete_title_attributes %}
          <span {{ delete_title_attributes|safe }} ></span>
        {% else %}
          <img alt="{% trans 'Delete column' context 'alt attribute in <img> html tag' %}" class="{{ html_class|add:'genTab'}} {{ html_class|add:'genTabHeadCellDeleteImg'}}" src="data:image/png;base64,{{ delete_png }}">
        {% endif %}
      </th>
    {% endif %}
    {% if processes %}
      {% for process_name, process_view, html_code, link_process_view, form_attribute in processes %}
        <th>
          {{ html_code|safe }}
        </th>
      {% endfor %}
    {% endif %}
  </tr>
</thead>
{% endblock %}
<!--End Columns titles block -->
"""

filter_table_html = """<!-- Start filter block -->
{% block table_filters %}
{% if filter_able %}
  <tr {% if filter_tag_attributes %} {{ filter_tag_attributes|safe }} {% endif %}>
    {% for filter in data_filter %}
      {% if filter|get_item:'filter' %}
          <td class="{{ filter|get_item:'class' }}">
            {{ filter|get_item:'filter'|safe }}
            <input class="" form="table_get_data" type="image" src="data:image/png;base64,{{ search_png }}" alt="Submit">
          </td>
      {% else %}
        <td></td>
      {% endif %}
    {% endfor %}
    {% if delete_able %}
      <td></td>
    {% endif %}
    {% if processes %}
      {% for process_name, process_view, html_code, link_process_view, form_attribute in processes %}
        <td></td>
      {% endfor %}
    {% endif %}
  </tr>
{% endif %}
{% endblock %}
<!-- End filter block -->"""

page_table_html = """
<!--Start pagination footer-->
{% block pagination %}
<table>
  <tr>
    <td>
      {% if page_obj.has_previous %}
        <a class="" href="#" onclick="document.getElementById('page').value='{{ page_obj.previous_page_number }}';document.getElementById('table_get_data').submit(); return false;">
          {% trans "Previous" context "Previous page" %}
        </a>
      {% endif %}
    </td>
    <td>
      {% trans "Page" context "PAGE x of y" %} {{ page_obj.number }} {% trans "of" context "Page x OF y" %} {{ page_obj.paginator.num_pages }}
    </td>
    <td>
      <input class="" type="text" size="4" id="page" name="page" value="{{ page }}" form="table_get_data">
      <input class="" type="submit" value="{% trans 'Go' context 'Go page button' %}" form="table_get_data">
    </td>
    <td>
      {% if page_obj.has_next %}
        <a class="" href="#" onclick="document.getElementById('page').value='{{ page_obj.next_page_number }}';document.getElementById('table_get_data').submit(); return false;">
          {% trans "Next" context "Next page" %}
        </a>
      {% endif %}
    </td>
  </tr>
</table>
{% endblock %}
<!-- End block pagination -->
"""

child_table_tb_create = """
<!-- Start Block Create Object Button -->
{% block table_tb_create %}
  {% if link_to_detail and create_able %}
  <form method="get" id="table_create_child" action="{% url detail_url %}" >
    <input form="table_create_child" type="hidden" name="parent_model" value="{{ parent_model }}">
    <input form="table_create_child" type="hidden" name="parent_id" value="{{ parent_id }}">
    <input form="table_create_child" type="hidden" name="foreign_key" value="{{ foreign_key }}">
    <input form="table_create_child" type="hidden" name="new_child" value="True">
    <input class="{{ create_class }}" form="table_create_child"  type="submit" value="{% trans 'Create' context 'Create new child element' %} {{ object_name }}">
  </form>
  {% endif %}
{% endblock %}
<!-- End Block Create Object Button -->

"""

form_create_child_table_html = """
<!-- Start Block for ChildFormTemplate's Forms -->
{% block child_table_template_forms %}
{% endblock %}
<!-- End Block for ChildFormTemplate's Forms -->
"""

toolbar_child_table_html = """{% if reset_able %}<td>""" \
                           + table_tb_reset \
                           + """{% endif %}{% if link_to_detail and create_able %}</td><td>""" \
                           + child_table_tb_create \
                           + """{% endif %}{% if delete_able %}</td><td>""" \
                           + table_tb_delete \
                           + """{% endif %}</td>"""
