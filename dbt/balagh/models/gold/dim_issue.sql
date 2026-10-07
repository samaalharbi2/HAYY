-- One row per canonical issue (245), built from the translation seed.
-- 'UNMAPPED' catches any future issue type that is not in the seed yet.
select distinct
    issue_code as issue_key,
    issue_code,
    issue_ar,
    issue_en,
    department_ar,
    department_en,
    domain_ar,
    domain_en,
    translation_source
from {{ ref('map_issue_type') }}

union all

select 'UNMAPPED', 'UNMAPPED', 'غير مصنف', 'Unmapped', 'غير مصنف', 'Unmapped', 'غير مصنف', 'Unmapped', 'none'
