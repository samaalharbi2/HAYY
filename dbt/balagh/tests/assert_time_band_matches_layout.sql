-- Layout B always has a time band. Layout A never has one.
select request_sk, source_layout, time_band
from {{ ref('silver_service_requests') }}
where (source_layout = 'B' and time_band is null)
   or (source_layout = 'A' and time_band is not null)
