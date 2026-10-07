-- Every request in the fact table is counted exactly once in the mart.
with mart as (select sum(total_requests) as n from {{ ref('gold_issue_performance') }}),
     fact as (select count(*) as n from {{ ref('fact_service_requests') }})
select mart.n as mart_requests, fact.n as fact_requests
from mart cross join fact
where mart.n != fact.n
