select request_sk, closure_hours
from {{ ref('silver_service_requests') }}
where closure_hours < 0
