"""
Grid templates
"""

grid_load_template = """
{% load i18n %}{% load dictionary %}
"""

# A Block Mixins
edit_html = """
<!-- Start Block edit button -->
{% block tool_bar_edit_button %}
{% if not update_able and not new_able %}
  {% if edit_able %}
    <div class="{% if edit_class %}{{ edit_class }}{% else %}{{ html_class|add:'tool_bar'}} {{html_class|add:'tool_bar_cell'}}{% endif %}" {% if not edit_class %}style="display: table-cell;"{% endif %}>
      <input type='submit' value='{{ edit_name }}' class="{% if edit_button_class %}{{ edit_button_class }}{% else %}{{ html_class|add:'tool_bar'}} {{html_class|add:'tool_bar_edit_button'}}{% endif %}" form='grid_get_form'>
      <input type='hidden' name='edit' value='edit' form='grid_get_form'>
    </div>
  {% endif %}
{% endif %}
{% endblock %}
<!-- Start Block edit button -->
"""

update_html = """
<!-- Start Block update button -->
{% block tool_bar_update_button %}
{% if update_able and not new_able %}
  <div class="{% if update_class %}{{ update_class }}{% else %}{{ html_class|add:'tool_bar'}} {{html_class|add:'tool_bar_cell'}}{% endif %}" {% if not update_class %}style="display: table-cell;"{% endif %}>
    <input type='submit' value='{{ update_name }}' class="{% if update_button_class %}{{ update_button_class }}{% else %}{{ html_class|add:'tool_bar'}} {{html_class|add:'tool_bar_update_button'}}{% endif %}" form='grid_post_form'>
    <input type='hidden' name='update' value='update' form='grid_post_form'>
  </div>
{% endif %}
{% endblock %}
<!-- Start Block update button -->
"""

new_html = """
<!-- Start Block new button -->
{% block tool_bar_new_button %}
{% if new_able and not update_able %}
  <div class="{% if new_class %}{{ new_class }}{% else %}{{ html_class|add:'tool_bar'}} {{html_class|add:'tool_bar_cell'}}{% endif %}" {% if not new_class %}style="display: table-cell;"{% endif %}>
    <input type='submit' value='{{ new_name }}' class="{% if new_button_class %}{{ new_button_class }}{% else %}{{ html_class|add:'tool_bar'}} {{html_class|add:'tool_bar_new_button'}}{% endif %}" form='grid_post_form'>
    <input type='hidden' name='new' value='new' form='grid_post_form'>
  </div>
{% endif %}
{% endblock %}
<!-- Start Block new button -->
"""

back_html = """
<!-- Start Block back button -->
{% block tool_bar_back_button %}
{% if back_able %}
  <div class="{% if back_class %}{{ back_class }}{% else %}{{ html_class|add:'tool_bar'}} {{html_class|add:'tool_bar_cell'}}{% endif %}" {% if not back_class %}style="display: table-cell;"{% endif %}>
    <form action='{% if back_view_id %}{% url back_view back_view_id %}{% else %}{% url back_view %}{% endif %}'>
    <button class="{% if back_button_class %}{{ back_button_class }}{% else %}{{ html_class|add:'tool_bar'}} {{html_class|add:'tool_bar_back_button'}}{% endif %}">
        {{ back_name }}
     </button>
    </form>
  </div>
{% endif %}
{% endblock %}
<!-- Start Block back button -->
"""

basic_grid_html = """
{% if update_able or new_able %}
  <form id='grid_post_form' method='post' action='#'>
  {% csrf_token %}
  </form>
{% else %}
  <form id='grid_get_form' method='get' action='#'></form>
{% endif %}
{% if not primary_key_present %}
  <input form='grid_post_form' type='hidden' name='{{ primary_key }}' value='{{ primary_key_value }}'>
{% endif %}
<!-- Start Block Grid Data -->
{% block data_grid_block %}
  {% for row in data_grid|dictsort:'row' %}
    <div id="row_{{ row|get_item:'row'}}" class="{% if grid_row_class %}{{ grid_row_class }}{% else %}{{ html_class|add:'grid'}} {{html_class|add:'grid_row'}}{% endif %}" {% if not grid_row_class %}style="display: table-row;"{% endif %}>
      {% for value, label, cell_attributes, is_data, error_class, error_msj in row|get_item:'data' %}
        <div {% if cell_attributes %}{{ cell_attributes|safe }}{% else %}id="cel_{{ row|get_item:'row'}}_{{ forloop.counter }}" class="{{ html_class|add:'grid'}} {{html_class|add:'grid_cell'}} {{ error_class }}" style="display: table-cell;"{% endif %}>
          {% if label or error_msj %}
            {% if label and is_data %}
              {{ label|safe }}
            {% endif %}
            {% if error_msj %}
              <span class="{{ html_class|add:'grid'}} {{html_class|add:'gird_error_p'}}">{{ error_msj }}</span>
            {% endif %}
          {% endif %}
            {% if is_data %}{{ value }}{% else %}{{ value|safe }}{% endif %}
        </div>
      {% endfor %}
    </div>
  {% endfor %}
{% endblock %}
<!-- End Block Grid Data -->
  """

child_grid_html = """
<!-- Start Block Child Data -->
{% if not is_present_FKey %}
  {% if not update_able and not new_able %}
    <input form="grid_get_form" type="hidden" name="{{ foreign_key_field }}" value="{{ foreign_key_value }}">
  {% else %}
    <input form="grid_post_form" type="hidden" name="{{ foreign_key_field }}" value="{{ foreign_key_value }}">
  {% endif %}
{% endif %}
<!-- Start Block Child Data -->
"""

