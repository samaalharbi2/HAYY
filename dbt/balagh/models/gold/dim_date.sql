-- One row per calendar day between the first and last received date.
with bounds as (
    select min(received_date) as d0, max(received_date) as d1
    from {{ ref('silver_service_requests') }}
)
select
    cast(format_date('%Y%m%d', d) as int64) as date_key,
    d                                       as date,
    extract(year from d)                    as year,
    extract(quarter from d)                 as quarter,
    format_date('%Y-Q%Q', d)                as year_quarter,
    extract(month from d)                   as month,
    format_date('%Y-%m', d)                 as year_month,
    format_date('%B', d)                    as month_name_en,
    extract(isoweek from d)                 as iso_week,
    format_date('%A', d)                    as day_name_en
from bounds, unnest(generate_date_array(d0, d1)) as d
