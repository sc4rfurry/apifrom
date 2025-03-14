{% if obj.display %}
{% block module_header %}
{{ obj.name }}
{{ "=" * obj.name|length }}

{% endblock %}

{% block module_headline %}
{% if obj.docstring %}
{{ obj.docstring|prepare_docstring|indent(0) }}
{% endif %}
{% endblock %}

{% block module_content %}
{% if obj.all is defined %}

.. py:currentmodule:: {{ obj.name }}

{% if obj.children %}
Overview
--------

{% if obj.classes %}
**Classes**

{% for klass in obj.classes %}
* :py:class:`{{ klass.name }}`
{% endfor %}

{% endif %}

{% if obj.functions %}
**Functions**

{% for function in obj.functions %}
* :py:func:`{{ function.name }}`
{% endfor %}

{% endif %}

{% if obj.attributes %}
**Data**

{% for attribute in obj.attributes %}
* :py:data:`{{ attribute.name }}`
{% endfor %}

{% endif %}
{% endif %}

{% endif %}

{% block submodule_content %}
{% if obj.modules %}
Submodules
----------

{% for submodule in obj.modules %}
* :py:mod:`{{ submodule.name }}`
{% endfor %}

{% endif %}
{% endblock %}

{% block module_classes %}
{% if obj.classes %}
Classes
-------

{% for klass in obj.classes %}
.. py:class:: {{ klass.name }}{% if klass.args %}({{ klass.args }}){% endif %}
{% if klass.bases %}
:bases: {{ klass.bases|join(", ") }}
{% endif %}

{% if klass.docstring %}

{{ klass.docstring|prepare_docstring|indent(3) }}
{% endif %}

{% for attribute in klass.attributes %}
{{ attribute.render()|indent(3) }}

{% endfor %}

{% for method in klass.methods %}
{{ method.render()|indent(3) }}

{% endfor %}

{% endfor %}
{% endif %}
{% endblock %}

{% block module_functions %}
{% if obj.functions %}
Functions
---------

{% for function in obj.functions %}
.. py:function:: {{ function.name }}({{ function.args }})
{% if function.return_annotation %}
:returns: {{ function.return_annotation }}
{% endif %}

{% if function.docstring %}

{{ function.docstring|prepare_docstring|indent(3) }}
{% endif %}

{% endfor %}
{% endif %}
{% endblock %}

{% block module_data %}
{% if obj.attributes %}
Data
----

{% for attribute in obj.attributes %}
.. py:data:: {{ attribute.name }}
{% if attribute.annotation %}
:annotation: {{ attribute.annotation }}
{% endif %}

{% if attribute.docstring %}

{{ attribute.docstring|prepare_docstring|indent(3) }}
{% endif %}

{% endfor %}
{% endif %}
{% endblock %}

{% block module_exceptions %}
{% if obj.exceptions %}
Exceptions
----------

{% for exception in obj.exceptions %}
.. py:exception:: {{ exception.name }}
{% if exception.bases %}
:bases: {{ exception.bases|join(", ") }}
{% endif %}

{% if exception.docstring %}
{{ exception.docstring|prepare_docstring|indent(3) }}
{% endif %}

{% endfor %}
{% endif %}
{% endblock %}

{% endblock %}
{% endif %}
