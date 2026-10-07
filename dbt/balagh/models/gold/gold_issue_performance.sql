-- One row per (quarter, issue type).
-- Resolution Insights: compares closure speed and repeat rate within each quarter.
-- Descriptive only: groups show where to look, not why it happens.

with base as (
    select
        f.source_quarter,
        f.issue_key,
        i.issue_type_ar,
        f.status_code,
        f.is_repeated,
        f.closure_hours,
        f.is_closure_kpi_eligible
    from {{ ref('fact_service_requests') }} f
    join {{ ref('dim_issue') }} i using (issue_key)
),

medians as (
    select distinct
        source_quarter,
        issue_key,
        percentile_cont(closure_hours, 0.5)
            over (partition by source_quarter, issue_key) as median_closure_hours
    from base
    where is_closure_kpi_eligible
),

per_issue as (
    select
        source_quarter,
        issue_key,
        any_value(issue_type_ar)                                    as issue_type_ar,
        count(*)                                                    as total_requests,
        countif(is_repeated)                                        as repeated_requests,
        safe_divide(countif(is_repeated), count(*))                 as repeat_rate,
        countif(status_code in ('completed', 'in_progress'))        as requests_with_status,
        safe_divide(countif(status_code = 'completed'),
                    countif(status_code in ('completed', 'in_progress'))) as completion_rate,
        countif(is_closure_kpi_eligible)                            as closure_kpi_requests
    from base
    group by source_quarter, issue_key
),

joined as (
    select p.*, m.median_closure_hours
    from per_issue p
    left join medians m using (source_quarter, issue_key)
),

closure_threshold as (
    select distinct
        source_quarter,
        percentile_cont(median_closure_hours, 0.5)
            over (partition by source_quarter) as closure_threshold_hours
    from joined
    where total_requests >= {{ var('min_requests_for_matrix') }}
      and median_closure_hours is not null
),

repeat_threshold as (
    select source_quarter, avg(cast(is_repeated as int64)) as repeat_threshold
    from base
    group by source_quarter
)

select
    concat(j.source_quarter, '-', j.issue_key) as issue_quarter_key,
    j.*,
    c.closure_threshold_hours,
    r.repeat_threshold,
    case
        when j.total_requests < {{ var('min_requests_for_matrix') }}
          or j.median_closure_hours is null                     then 'Insufficient data'
        when j.median_closure_hours <= c.closure_threshold_hours
         and j.repeat_rate          <= r.repeat_threshold        then 'Effective'
        when j.median_closure_hours <= c.closure_threshold_hours
         and j.repeat_rate          >  r.repeat_threshold        then 'Root-Cause Attention'
        when j.median_closure_hours >  c.closure_threshold_hours
         and j.repeat_rate          <= r.repeat_threshold        then 'Operational Delay'
        else 'Priority Issue'
    end as resolution_group
from joined j
left join closure_threshold c using (source_quarter)
left join repeat_threshold  r using (source_quarter)
