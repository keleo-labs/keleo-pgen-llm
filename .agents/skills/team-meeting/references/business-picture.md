# Business picture

Recipe version: 3.0.0. Use only when selected by the series configuration.

## Quota view and product detail

Apply the available product-quota-attainment skill when
`review.metrics.quotaAttainment` is configured. Its geography, metric, currency
and named quota views define the requested comparison. Retrieve locked/final
targets separately from booked actuals; verify the target revision and all
dimensions before calculating attainment or the remaining gap.

Use only the quota views named in the series configuration. If views overlap,
do not sum them into a team quota or average their attainment. Verify product
credit mapping and organisational grain from the target source.

Lead with one quota/actual/attainment/gap row per configured view. If a target,
mapping or dimension is unavailable, label the comparison unavailable and explain
why. Keep the verified finer business breakdown below it; missing quotas do not
erase useful bookings and forecast context. Store numbers and dated source
captures in the instance, rather than the standing configuration or skill.

## Source workflow and period

For every Dataverse business query, including follow-ups, use
`identify_dataproducts` → `shortlist_tables` → `get_sql` → `execute_sql`.
Use discovered schema-qualified tables; do not bypass discovery or treat a query
template as user-provided SQL. Respect permission errors and row-level access.
Follow product-quota-attainment's authorized dashboard/export fallback rules.

`review-quarter` is the business-review period: normally the quarter containing
the meeting, or the completed quarter at a quarter-opening review. Resolve fiscal
labels and boundaries from source guidance. Retain the source key and disclose
unverified boundaries; do not assume calendar dates or equate CY and FY labels.
Quarter-opening reviews retain the previous quarter's booked result and show
current-quarter priorities separately, as the quarter-review recipe requires.

## Retained breakdown

Use the configured source, measure and product selectors for the finer breakdown.
Confirm current metadata, scope and any parent-child overlap before calculating.
Keep source precision in evidence. Match the measure's definition to any target
rather than substituting a similarly named measure.

Show configured forecast categories for each detail scope when supported.
Only the matched booked actual enters attainment. Any weighted forecast remains
planning context; neither it nor unweighted pipeline is booked attainment.
Do not add parent and child rows or overlapping quota views.

When quota access is denied, retain the verified breakdown and disclose the exact
gap. A dashboard that ignores product filters cannot supply product-specific
denominators. Official target exports or verified access can close that gap;
do not create a ticket, send messages or broaden permissions automatically.

Fixtures replace their live sources. Read the local focus and quarter-review
recipes before connecting these measures to roles or review priorities.

## Migration from version 1

Version 2 adds the configured quota view above the retained product detail and
uses full source discovery. It removes assumed fiscal dates and direct execution
of a hardcoded query. Standing configuration stores scope, not target amounts;
existing captures and evidence links remain historical records.
