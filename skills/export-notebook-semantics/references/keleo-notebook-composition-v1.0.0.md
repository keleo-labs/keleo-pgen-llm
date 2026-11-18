# Follow Keleo composition and workflow

Companion guide 1.0.0 · Practice Language schema 5.1.0 · Keleo notebook exporter 1.0.0

Use this guide to interpret dependencies, bindings and workflow in Keleo Markdown. Use the selected method or practice to establish which relationship is actually declared. Use project evidence to establish what ran or completed.

## Read a baseline, practice or method in scope

A **baseline** supplies reusable concepts. A baseline may build on parent baselines. A **practice** provides guidance for a specific concern or way of working. It can extend a baseline and declare dependencies on other practices. A **method** composes practices and their baseline context. Read the method's authored bindings and the member files for connections that cross practice or baseline boundaries.

The **Studio practice view** shows how Studio GAS resolved one practice or baseline from the available documents. For an extension practice, Studio limits inherited content to its documentation scope and retains baseline context such as baseline alphas and activity spaces. For a baseline, Studio can merge its parent chain. Read the authored section plus the changes and omissions shown in the view. Use **Dependencies and gaps** to tell which supporting sources were available. The absence of a dependency element in a focused view tells you little about the full dependency document.

For a same-name redeclaration in a composition, the earliest definition owns the element description. Later layers can add criteria and guidance. Ordinary scalar fields keep the first substantive value. The composed view reflects type-specific rules and any applicable suppression decisions. A surviving sequence can have gaps after an element is removed. Preserve those gaps when citing `seq` values.

## Read the direction and type of a relationship

- `contributesTo` on an alpha points from a supporting concern to the concern it advances. State-level mappings identify which progress transfers. Keep the source and target names in the answer.
- `mapsTo` points from a specialised variant to its more general alpha or work product. Check the scope and mappings before inferring equivalence between particular states or levels.
- `relatesTo` gives a named semantic association. Read the relationship and any declared direction. A contribution or prerequisite needs its own evidence in the model.
- `partOf` on a work product points from a component artifact to its containing artifact. Each may have its own levels of detail.

**Method-level bindings** connect elements from different baseline families. An alpha contribution advances another alpha. A work product contribution establishes containment. A variant binding expresses specialisation. Qualify each endpoint by its baseline and element name. Use explicit `stateContributions` or `lodContributions` for state or level correspondences. When a contribution mapping omits a state or level, the omitted entry supplies no contribution signal. A document dependency establishes composition context. Derive workflow order from the declared workflow.

## Read order, timing and required work

A **pattern** describes a reusable progression. A **pattern view** is a phase or milestone within that pattern. It can name expected states, work product levels, instances and active work. Use the view's sequence and declared loop edges to explain where a phase fits. Expected states describe what the phase aims to achieve.

An **orchestration** places whole patterns or sub-orchestrations into stages. Read each stage's `relationship` together with its host, trigger or recurrence.

- `sequential` places the stage in the progression.
- `concurrent` places work alongside a host.
- `nested` places work within a host.
- `onDemand` provides a response to a recognised trigger.

Use `seq` to order sequential stages. For other stage types, `seq` anchors presentation. Use declared entry conditions, exit criteria and state or work product references to explain when work starts, what happens and what evidence to check. An `onDemand` stage applies when its trigger occurs. A declared loop describes recurring work and identifies a return point. Use project records to say whether a particular run took place.

## Example answer

In this fictional example, the reader asks “Does Escalated Review always come after Initial Review?”

“In this example the orchestration declares Escalated Review as `onDemand` with the trigger ‘decision disputed’. The stage applies when that trigger is recognised. Initial Review would be a prerequisite only if the workflow declared it.”

This guide draws on Keleo Language revision `35f3eefc3756783d0b66c4324e0972ee089e3439`, Semantics §§4.1–4.5, 4.8–4.9, 6.1–6.2, 7.5–7.7 and 9.2–9.5, and Merge §§2–4, 7–8 and 10.
