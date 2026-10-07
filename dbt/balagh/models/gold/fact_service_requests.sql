-- One row per service request. Keys point to the dimensions.
-- issue_key is the canonical issue_code, so Q1 and Q2 spelling variants match.
select
    s.request_sk,
    cast(format_date('%Y%m%d', s.received_date) as int64) as date_key,
    coalesce(m.issue_code, 'UNMAPPED')                   as issue_key,
    {{ location_key('s.location_ar') }}                  as location_key,
    s.status_code,

    s.source_quarter,
    s.source_layout,
    s.time_band,

    -- measures and flags
    s.is_repeated,
    s.closure_hours,
    s.closure_basis,
    s.is_closure_kpi_eligible,
    s.is_zero_closure,
    s.is_closure_outlier
from {{ ref('silver_service_requests') }} s
left join {{ ref('map_issue_type') }} m
       on m.issue_type_ar = s.issue_type_ar
