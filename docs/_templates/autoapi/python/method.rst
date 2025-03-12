{% if obj.display %}
{% if obj.method_type == 'staticmethod' %}
.. staticmethod:: {{ obj.name }}({{ obj.args }}){% if obj.name in ['config', 'routes', 'middleware'] and 'APIFromAnything' in obj.parent.name %} :no-index:{% endif %}
{% elif obj.method_type == 'classmethod' %}
.. classmethod:: {{ obj.name }}({{ obj.args }}){% if obj.name in ['config', 'routes', 'middleware'] and 'APIFromAnything' in obj.parent.name %} :no-index:{% endif %}
{% else %}
.. method:: {{ obj.name }}({{ obj.args }}){% if obj.name in ['config', 'routes', 'middleware'] and 'APIFromAnything' in obj.parent.name %} :no-index:{% endif %}
{% endif %}

   {% if obj.properties %}
   {% for property in obj.properties %}
   :{{ property }}:
   {% endfor %}
   {% endif %}

   {% if obj.docstring %}
{{ obj.docstring|prepare_docstring|indent(3) }}
   {% endif %}
{% endif %}
