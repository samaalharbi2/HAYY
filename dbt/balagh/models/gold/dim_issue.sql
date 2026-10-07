-- One row per issue type. English labels will be added later from a seed.
select distinct
    to_hex(md5(issue_type_ar)) as issue_key,
    issue_type_ar
from {{ ref('silver_service_requests') }}
