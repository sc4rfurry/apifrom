{{ obj.name }}
{{ "=" * obj.name|length }}

.. py:{{ obj.type }}:: {{ obj.name }}
{% if obj.display %}
{{ obj.display|indent(4) }}
{% endif %}

{% if obj.bases %}
Bases: {% for base in obj.bases %}:class:{{ base }}{% if not loop.last %}, {% endif %}{% endfor %}
{% endif %}

{% if obj.docstring %}
{{ obj.docstring|indent(0) }}
{% endif %}

{% if obj.attributes %}
{% for attribute in obj.attributes %}
.. py:attribute:: {{ attribute.name }}
  {% if attribute.docstring %}
  {{ attribute.docstring|indent(4) }}
  {% endif %}

{% endfor %}
{% endif %}

{% if obj.methods %}
{% for method in obj.methods %}
.. py:method:: {{ method.short_name }}({{ method.args }})
{% if method.docstring %}
{{ method.docstring|indent(4) }}
{% endif %}

{% endfor %}
{% endif %}
