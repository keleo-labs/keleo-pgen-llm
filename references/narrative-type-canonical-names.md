## Canonical narrative names

Version: **2.0.0**. This is the behavioural version of
`narrative-type-canonical-names.json`; its list format is unchanged. Version 2.0.0
changes the verification result for `Essay`, which previously passed as an identity
pin and now requires migration to `Essay Narrative`.

Migrate with `utils/retype-narratives.py` using a context that defines the target
type. Map `Introduction` to `Introduction`, `Body` to `Presenting Evidence` and
`Conclusion` to `Conclusion`. Keep the existing prose; do not invent content for
`Defining Key Concepts`.

```json
[
  {
    "fromType": "Essay",
    "toType": "Essay Narrative",
    "elementMap": {
      "Introduction": "Introduction",
      "Body": "Presenting Evidence",
      "Conclusion": "Conclusion"
    }
  }
]
```

Run a dry run with `--spec-file`, review its changes, then use `--fix`. Patterns
and orchestrations require an explicit map because context sequence numbers are
local to each view or stage. Re-run the canonical-name gate with `--verify` after
retyping; a name-only replacement does not migrate narrative element references.

`Hero's Journey` and `Three-Act Structure` remain identity pins. Their defining
elements determine the appropriate target and mapping, as the JSON notes explain.

```gherkin
Feature: Canonical narrative name verification
  Scenario: Legacy essay requires migration
    Given a narrative is typed as Essay
    When canonical names are verified
    Then verification reports the legacy type

  Scenario: Essay migration preserves content
    Given a context defines Essay Narrative
    When the explicit essay element map is applied
    Then each context names an element of Essay Narrative
    And the context prose is unchanged

  Scenario: Ambiguous names require a deliberate mapping
    Given a narrative is typed as Hero's Journey or Three-Act Structure
    When canonical names are verified
    Then its type remains unchanged
```
