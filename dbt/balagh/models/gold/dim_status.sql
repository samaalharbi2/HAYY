-- Fixed list of status codes used in the fact table.
select * from unnest([
    struct('completed'     as status_code, 'تم التنفيذ' as status_label_ar, 'Completed'     as status_label_en, true  as is_status_published),
    struct('in_progress',                  'جاري العمل',                    'In progress',                      true),
    struct('not_published',                'غير منشورة',                    'Not published',                    false)
])
