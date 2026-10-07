# Data Quality Findings

## Finding 1: Two layouts inside the Q2 2026 file (critical)

The Q2 file keeps the same column names as Q1, but the content changes:

| Header in file | Layout A (Q1 + last 78 rows of Q2) | Layout B (212,718 rows of Q2) |
|---|---|---|
| حالة البلاغ | request status | closure time in hours |
| زمن الإغلاق بالساعات | closure time in hours | 6-hour time band (e.g. "06:00 12:00") |
| تاريخ الاستلام | date + time (Q1) | date only |

Evidence:
- 212,718 rows have a time band; 78 rows do not.
- The 78 rows are contiguous at the end of the file (rows 212,718 to 212,795).
- In Layout B, 99.55% of the "status" column is numeric, with a median of 21.
  This matches the Q1 median closure time (20 hours).
- The transition is visible at row 212,718.

Impact if not handled:
- Completion rate would be 0% for Q2 (no row matches "تم التنفيذ").
- Closure time would fail to parse for 212,718 rows.
- Nothing would crash. The dashboard would silently show wrong numbers.

Decisions:
- Detect the layout per row from the content, not from the header.
- Add a `source_layout` column (A / B) for lineage.
- Status in Layout B = NULL (not published). We do not infer it.
- The time band is stored as `time_band`. Its meaning is inferred, not confirmed.

## Finding 2: Documented schema does not match the files
The portal lists 7 columns, including "رقم البلاغ" (request number).
All files have 6 columns. There is no request ID.

## Finding 3: Inconsistent sheet names and file names
- Sheet: "Sheet1" (Q1) vs "2026" (Q2).
- Location column: "الموقع" (Q1) vs "اسم الموقع" (Q2).
- File names differ in every release.

## Open questions
- Does Q2 cover a wider area (e.g. الخرج، الحريق) than Q1?
- Do the 951 empty closure values in Layout B mean "in progress"?

## Finding 5: Key collision in dim_location (caught by a test)
- The source has 1 request (Q2) with the location written as "غير محدد".
- Our model mapped empty locations to the same text, so two different
  members shared one key. The `unique` test on dim_location failed.
- This test was silently disabled at first: dim_location did not exist
  when the tests were parsed, and dbt partial parsing kept them disabled.
  We noticed because the test count was 32 instead of the expected 35.

Fix:
- Empty locations use a sentinel ('__missing__') for the key,
  and the label "غير متوفر في المصدر".
- The key is built in one macro (location_key) used by both
  dim_location and the fact table, so they can never drift apart.

Lessons:
- Never use a value that can appear in real data as a placeholder.
- A green run is not enough: always check that the expected number of tests ran.

## Finding 6: Issue-type spelling changed between quarters
- Q2 removed hyphens, slashes and parentheses from issue names
  (e.g. "خزان ارضي -بيارة" in Q1 vs "خزان ارضي بيارة" in Q2), and sometimes a space or "أو".
- 272 raw names = 245 real issue types (27 variants).
- Without a fix, the same issue looks "new" in Q2 and Q1-vs-Q2 comparisons are wrong.
- Fix: the seed map_issue_type maps every raw variant to one canonical issue_code.

## Finding 7: Q1 location names are cut to the first word
- Q1 has no multi-word location; Q2 has 87 (e.g. Q1 "الملك" vs Q2 "الملك فهد", "الملك فيصل").
- 8 Q1 values cannot be resolved to one neighborhood. They are typed `truncated_name`.
- Also: one neighborhood spelled two ways (السويدي / السويدى), and one location value "0".
- The official Q1 English file is a 30,000-row extract (Arabic has 34,100), so it could not be
  joined by counts. English labels follow the official wording where it exists (149 of 245).
