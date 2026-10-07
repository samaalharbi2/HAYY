-- Silver must keep every Bronze row, except embedded header rows.
with bronze as (
    {% for q in var('bronze_quarters') %}
    select count(*) as n,
           countif(trim(issue_type_raw) = 'نوع البلاغ') as header_rows
    from {{ source('bronze', 'raw_940_' ~ q) }}
    {% if not loop.last %}union all{% endif %}
    {% endfor %}
),
expected as (select sum(n) - sum(header_rows) as n from bronze),
actual   as (select count(*) as n from {{ ref('silver_service_requests') }})
select e.n as expected_rows, a.n as actual_rows
from expected e cross join actual a
where e.n != a.n
