-- One row per 940 service request.
-- Resolves the two source layouts (A and B) documented in docs/data_quality_findings.md.

with unioned as (
    {% for q in var('bronze_quarters') %}
    select * from {{ source('bronze', 'raw_940_' ~ q) }}
    {% if not loop.last %}union all{% endif %}
    {% endfor %}
),

cleaned as (
    select
        source_row_number,
        source_file,
        source_quarter,
        file_sha256,
        batch_id,
        ingested_at,
        regexp_replace(trim(issue_type_raw), r'\s+', ' ') as issue_type_ar,
        regexp_replace(trim(location_raw), r'\s+', ' ')   as location_ar,
        trim(status_slot_raw)                              as status_slot,
        trim(closure_slot_raw)                             as closure_slot,
        trim(received_raw)                                 as received_raw,
        trim(repeat_flag_raw)                              as repeat_flag_ar
    from unioned
),

with_layout as (
    select
        *,
        case
            when regexp_contains(closure_slot, r'^\d{2}:\d{2} \d{2}:\d{2}$') then 'B'
            else 'A'
        end as source_layout
    from cleaned
    where coalesce(issue_type_ar, '') != 'نوع البلاغ'   -- drop embedded header rows
),

resolved as (
    select
        *,
        case when source_layout = 'A' then status_slot end as status_ar,
        safe_cast(
            case when source_layout = 'A' then closure_slot else status_slot end
        as float64)                                          as closure_hours,
        case when source_layout = 'B' then closure_slot end as time_band,
        safe_cast(received_raw as datetime)                  as received_at
    from with_layout
)

select
    -- key: same file + same row -> same key, even after a reload
    to_hex(md5(concat(file_sha256, '-', cast(source_row_number as string)))) as request_sk,

    source_quarter,
    source_layout,

    -- issue and location (Arabic is the source of truth)
    issue_type_ar,
    location_ar,
    (location_ar = 'بلدية' or starts_with(location_ar, 'بلدية ')) as is_municipality_level,

    -- status
    status_ar,
    case
        when status_ar = 'تم التنفيذ' then 'completed'
        when status_ar = 'جاري العمل' then 'in_progress'
        when source_layout = 'B'      then 'not_published'
        else 'unknown'
    end as status_code,

    -- time
    received_at,
    date(received_at)                      as received_date,
    time(received_at) != time '00:00:00'   as has_received_time,
    time_band,

    -- recurrence (source flag, not proof of the same complaint)
    repeat_flag_ar,
    repeat_flag_ar = 'مكرر' as is_repeated,

    -- closure + quality flags
    closure_hours,
    case
        when status_ar = 'تم التنفيذ' and closure_hours is not null then 'status_confirmed'
        when source_layout = 'B'      and closure_hours is not null then 'closure_value_only'
    end as closure_basis,
    (closure_hours is not null and closure_hours >= 0
        and (status_ar = 'تم التنفيذ' or source_layout = 'B')) as is_closure_kpi_eligible,
    coalesce(closure_hours = 0, false)   as is_zero_closure,
    coalesce(closure_hours > 720, false) as is_closure_outlier,

    -- lineage back to the exact row in the source file
    source_file,
    source_row_number,
    file_sha256,
    batch_id,
    ingested_at
from resolved
