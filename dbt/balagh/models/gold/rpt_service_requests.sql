-- Dashboard table: the fact joined to all dimensions, one row per request.
-- KPI rules live here (in dbt), so the dashboard only displays them.
select
    f.request_sk,
    f.source_quarter,
    d.date            as received_date,
    d.year_month,

    i.issue_code,
    i.issue_ar,
    i.issue_en,
    i.domain_ar,
    i.domain_en,

    l.location_label_ar,
    l.location_en,
    l.location_type,

    s.status_code,
    f.time_band,
    f.closure_basis,

    -- ready-made KPI columns
    cast(f.is_repeated as int64)                                       as is_repeated_int,
    if(f.status_code = 'completed', 1, 0)                              as is_completed_int,
    if(f.status_code in ('completed', 'in_progress'), 1, 0)            as has_published_status,
    if(f.is_closure_kpi_eligible, f.closure_hours, null)               as closure_hours_kpi,
    f.is_closure_outlier
from {{ ref('fact_service_requests') }} f
join {{ ref('dim_date') }}     d using (date_key)
join {{ ref('dim_issue') }}    i using (issue_key)
join {{ ref('dim_location') }} l using (location_key)
join {{ ref('dim_status') }}   s using (status_code)
