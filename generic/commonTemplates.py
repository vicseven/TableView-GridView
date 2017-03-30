# Common Templates
tool_bar_begin = """
<!-- Start Block Tool Bar -->{% block tool_bar %}<div class="{% if toolbar_html_class %}{{ toolbar_html_class }}{% else %}{{ html_class|add:'tool_bar'}}{% endif %}" {% if not toolbar_html_class %}style="display: table-row"{% endif %}>
"""
tool_bar_end = '</div>{% endblock %}<!-- End Block Tool Bar -->'
