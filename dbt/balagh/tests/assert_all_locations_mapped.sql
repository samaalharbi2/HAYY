{{ config(severity='warn') }}
select distinct s.location_ar
from {{ ref('silver_service_requests') }} s
left join {{ ref('map_location') }} m using (location_ar)
where s.location_ar is not null and m.location_ar is null
