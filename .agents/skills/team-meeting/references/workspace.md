## Series workspace

Series configuration format version: 1.1.0; version 1.0.0 series remain valid.
Project signal configuration stays 1.0.0. Resolve a series before collecting evidence:

```bash
python3 utils/team-meeting.py resolve reports/<series-slug>/series.json
python3 utils/team-meeting.py prepare reports/<series-slug>/series.json --at 2026-10-26T09:00:00+00:00
python3 utils/team-meeting.py prepare reports/<series-slug>/series.json --at 2026-10-26T09:00:00+00:00 --fix
```

`prepare` is dry-run unless `--fix` is supplied. It creates a new dated instance
once, with `effective-config.json`, context snapshots and `evidence/`. Write
`<instance>/report.md` and initialise/finalise provenance in that same instance.
All eight sections, supporting assets and verification findings belong there.
Revisions use that workspace and preserve user edits; do not rerun preparation
to overwrite its original snapshots. Reschedule before preparation or choose the
new meeting time; starts in a daylight-saving fold must have an explicit offset.

The series holds `series.json`, `context/merged-practice.json` (one per compatible
baseline group), `signals/state.json`, `signals/journal.json` and source recipes.
An instance's effective configuration records the origin of every inherited and
series-specific signal. Relative file paths resolve against the declaring JSON
file, including global signal paths. URLs are not interpreted as filesystem paths.
The schemas beside this guide define the interface; credentials are never fields.

### Signals

Project signals live in `config/team-meeting/signals.json`, initially an empty
list. A signal has a stable `id`, a `recipe` and optional `settings`, `fixturePath`,
`statePath`, `mappingPath` or `recipePath`. Settings contain connector selectors,
not file paths or credentials. File inputs use explicit path fields.
Series signals can only add IDs. Duplicate IDs, including identical definitions,
are errors: put a shared signal in one place instead of maintaining two copies.
Neither layer accepts `enabled`, removal or override controls. A missing global
file is a configuration error, not an empty fallback. No implicit global sources.

Local fixtures replace live sources. Each series owns independent journals even
when it inherits identical collection definitions. Reuse raw immutable evidence
when appropriate but record separate series coverage and collection windows.
Snapshots record what was actually resolved; later configuration edits affect
future instances only. Do not copy credentials or private raw evidence into a
shared report or export directory.

### Setup and migration

Version 1.1 adds optional `review.metrics.quotaAttainment`, a version 1.0.0 block
with source skill, geography, named quota views, metric, currency/basis and
`period: "review-quarter"`. Set `viewsAreAdditive: false` and
`retainProductBreakdown: true`. Source-verified targets stay in dated captures,
not configuration. Use the existing business-review quarter, including the
completed quarter at an opener; do not assume fiscal dates from labels.

For an explicitly requested revision after configuration changes, preserve the
original effective-config.json and save a separately named resolved snapshot with
provenance. Do not rerun preparation to overwrite the original instance.

Start from `example-series.json`, replace its roles, objectives, calendar, history
and practice groups, resolve practice dependencies using `resolve-context.py`,
then confirm the standing selection. Do not merge unrelated root baselines.
Store actual dependency versions and provenance with the merged context.

```bash
python3 utils/team-meeting.py migrate --workspace /path/to/old-workspace
python3 utils/team-meeting.py migrate --workspace /path/to/old-workspace --fix
```

Migration reads the old skill-config, roster, team-news state/mapping/journal and
team-call analysis references. It creates one folder per exact configured calendar
title, copies independent journals and preserves historical local links as
absolute paths. Original evidence, configuration and historical reports are
retained. It refuses to replace existing series folders; reruns validate the
existing configuration instead. Migration seeds history, not new collection runs.
Objectives remain null until the team confirms them. Imported standing practice
selection is already agreed; narrative choices remain unconfirmed at first use.

Update meeting-prep's routing to the series configuration paths. Replace old
team-call calls; no new output goes to the historical team-meetings folder.
After migration, source settings and focus live in the series, rather than the
old skill-config. The initial roster is dated evidence, not a live roster refresh.

### Optional recipes

Generic teams can use only local transcripts and signals. Source skills such as
gws, Slack, Smartsheet and sales-assistant remain connector dependencies only when
configured. Read `signals.md` for the migrated signal workflow,
`business-picture.md` for configured commercial measures and `review.md`
for quarter reviews, requests and recognition. These recipes are copied into
series folders during migration, so their local rules can evolve without
changing the generic skill. The migration also copies focus and facilitation
evidence; consult actual referenced publications before citing them.
