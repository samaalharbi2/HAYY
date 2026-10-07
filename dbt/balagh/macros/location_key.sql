{# One place to build the location key, so dim_location and the fact always match.
   A NULL location uses a sentinel that cannot appear in the source data. #}
{% macro location_key(column) -%}
    to_hex(md5(coalesce({{ column }}, '__missing__')))
{%- endmacro %}
