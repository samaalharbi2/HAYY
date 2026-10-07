{{ config(severity='warn') }}
-- A new issue type in a future file must be added to the seed.
select distinct s.issue_type_ar
from {{ ref('silver_service_requests') }} s
left join {{ ref('map_issue_type') }} m using (issue_type_ar)
where m.issue_type_ar is null
