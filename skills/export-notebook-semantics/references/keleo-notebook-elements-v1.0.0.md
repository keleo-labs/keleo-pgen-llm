# Understand Keleo practice elements and evidence

Companion guide 1.0.0 · Practice Language schema 5.1.0

Use this guide to read the meaning of fields in a Keleo practice, baseline or method. For a real methodology or project, take the element names, criteria and results from its own sources.

## Concerns, states and criteria

An **alpha** represents a concern to understand or progress over time. Its **states** describe conditions of that concern. The state's checklist describes the observations or evidence that support an assessment. Use the alpha and state names together when citing a criterion. Where a state uses `seq`, use it to read the model's ordering. A declared `loopsBackTo` identifies a recurring path. A later assessment can also report a setback in a non-cyclical model.

Checklist priority defaults to `must`. A `must` item is essential within the methodology. A `should` item is expected and can be excluded with a reason. A `could` item is supplementary. An actual project can scope items through its threshold and recorded checklist requirements. Use the project's scoping decisions if the question asks what that team must complete.

A **background** supplies shared prerequisites. A structured test may give conditions, a triggering action and outcomes to check. The test and its example values describe how to assess something. Recorded results require a project or other evidence source.

## Artifacts and evidence

A **work product** describes an artifact such as a review record, design or test report. A **level of detail** describes the content or quality of the artifact at a named level. The level's checklist describes what the artifact must exhibit.

Follow an `evidencedBy` reference to the named work product and, where specified, its level of detail. Read that level's checklist for the evidence expected. A work product level can also declare which alpha states it contributes to. Evidence about the artifact and an assessment about the alpha answer different questions.

An **alpha instance** names a particular occurrence of an alpha. A **work product instance** names a specific artifact. Practice and pattern files may use instances to provide guidance or examples. For an actual project, look for the instance under `current` and check its completion records, evidence links and notes. The `target` section describes intended achievement and scope.

## Work, roles and measurement

An **activity space** groups an area of work. An **activity** describes a specific action. Follow `worksOn` to the artifacts the activity works on. `involves` names persona groups that participate. `ledBy`, when present, names the persona accountable for leading the work. Persona and competency descriptions describe roles and capabilities. A project source identifies the people or teams filling those roles.

An **outcome** describes intended value and how to measure it. A metric contribution follows evidence to a numerical measure. An objective contribution bases progress on completion against a pattern or orchestration. An outcome definition supplies the measurement rule. Use a recorded outcome instance to report a target, forecast or actual value, identifying which value you cite.

## Rationale, references and examples

Use narratives for rationale, guidance and examples. Use citations to identify sources and assets to find templates or illustrations. When prose and a structured relationship appear to disagree, show the difference and identify the source of each. A valid structure alone establishes neither factual accuracy nor sufficient evidence.

In a fictional access review, `Access Risk / Reviewed` is an alpha state. `Access Review Record / Decision recorded` is an artifact level that can evidence it. The work product example explains what a record should contain. A project's decision and assessment establish what happened in that project.

This guide draws on Keleo Language revision `35f3eefc3756783d0b66c4324e0972ee089e3439`, Semantics §§5.2–5.3, 6.2–6.5, 6.8, 7.1–7.4, 8.1–8.2, 9.4, 10–11, 12.4–12.5, 12.8 and 16.7.
