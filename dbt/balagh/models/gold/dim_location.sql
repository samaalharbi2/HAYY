-- One row per location, with English label and location type from the seed.
select distinct
    {{ location_key('s.location_ar') }}                                  as location_key,
    coalesce(s.location_ar, 'غير متوفر في المصدر')                       as location_ar,
    coalesce(m.location_label_ar, s.location_ar, 'غير متوفر في المصدر')  as location_label_ar,
    coalesce(m.location_en, 'Not mapped')                                as location_en,
    coalesce(m.location_type, 'unmapped')                                as location_type,
    m.location_type_ar,
    m.location_type_en,
    coalesce(s.is_municipality_level, false)                             as is_municipality_level,
    s.is_location_missing
from {{ ref('silver_service_requests') }} s
left join {{ ref('map_location') }} m
       on m.location_ar = coalesce(s.location_ar, 'غير متوفر في المصدر')
