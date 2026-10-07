-- One row per service request. Keys point to the dimensions.
select
    request_sk,
    cast(format_date('%Y%m%d', received_date) as int64) as date_key,
    to_hex(md5(issue_type_ar))                          as issue_key,
    {{ location_key('location_ar') }}                   as location_key,
    status_code,

    source_quarter,
    source_layout,
    time_band,

    -- measures and flags
    is_repeated,
    closure_hours,
    closure_basis,
    is_closure_kpi_eligible,
    is_zero_closure,
    is_closure_outlier
from {{ ref('silver_service_requests') }}
