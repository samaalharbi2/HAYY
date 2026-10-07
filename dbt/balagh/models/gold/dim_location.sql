-- One row per location.
-- "غير محدد" written in the source and an empty location are kept as two different members.
select distinct
    {{ location_key('location_ar') }}                       as location_key,
    coalesce(location_ar, 'غير متوفر في المصدر')            as location_ar,
    coalesce(is_municipality_level, false)                   as is_municipality_level,
    is_location_missing
from {{ ref('silver_service_requests') }}
