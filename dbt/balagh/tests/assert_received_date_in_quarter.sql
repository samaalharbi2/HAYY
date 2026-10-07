-- A request in the 2026Q2 file must be received in 2026 Q2.
select request_sk, source_quarter, received_date
from {{ ref('silver_service_requests') }}
where format('%dQ%d', extract(year from received_date), extract(quarter from received_date))
      != source_quarter
