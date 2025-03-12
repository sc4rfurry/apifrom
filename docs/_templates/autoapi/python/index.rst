{% if obj is defined and obj.display %}
{{ obj.name }}
{{ "=" * obj.name|length }}

{% if obj.docstring %}
{{ obj.docstring|indent(0) }}
{% endif %}

{% if obj is defined and (obj.subpackages or obj.submodules) %}
{% set subpkg_indent = " " %}

Subpackages
-----------

{% if obj is defined and obj.subpackages %}
.. toctree::
    :maxdepth: 1
    :titlesonly:

{% for subpackage in obj.subpackages %}
    {{ subpackage }}
{% endfor %}

{% endif %}

{% if obj is defined and obj.submodules %}
Submodules
----------

.. toctree::
    :maxdepth: 1
    :titlesonly:

{% for submodule in obj.submodules %}
    {{ submodule }}
{% endfor %}

{% endif %}
{% endif %}

{% if obj is defined and obj.children %}
{{ obj.type|title }} Contents
{{ "-" * (obj.type|title + " Contents")|length }}

{% for child in obj.children|sort %}
.. autoapi-nested-parse::

{{ child.docstring|indent(3) }}

{% if child.methods or child.attributes or child.args %}

.. py:{{ child.type }}:: {{ child.name }}
    :module: {{ child.module }}
    {% if child.annotation %}
    :annotation: {{ child.annotation }}
    {% endif %}

{% endif %}

{% endfor %}
{% endif %}

{% endif %}

