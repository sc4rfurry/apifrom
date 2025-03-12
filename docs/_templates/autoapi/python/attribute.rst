{% if obj.display %}
{% if obj.annotation %}
.. {{ obj.role }}:: {{ obj.name }}
:annotation: {{ obj.annotation }}
{% if obj.name in ['config', 'routes', 'middleware'] %}:no-index:{% endif %}
{% else %}
.. {{ obj.role }}:: {{ obj.name }}
{% if obj.name in ['config', 'routes', 'middleware'] %}:no-index:{% endif %}
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
