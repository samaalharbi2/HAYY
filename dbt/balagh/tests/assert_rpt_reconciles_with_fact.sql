-- The joins must not drop or duplicate any request.
with rpt  as (select count(*) as n from {{ ref('rpt_service_requests') }}),
     fact as (select count(*) as n from {{ ref('fact_service_requests') }})
select rpt.n as rpt_rows, fact.n as fact_rows
from rpt cross join fact
where rpt.n != fact.n
