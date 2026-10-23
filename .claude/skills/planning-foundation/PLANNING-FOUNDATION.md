# Planning foundation

**Version:** 1.0.0

Read this before the planning stage of any skill that references it. Planning is an explicit workflow stage; native Plan mode is optional and does not replace user approval.

## Planning stage

1. Inspect relevant files and sources using read-only operations. Identify affected components, constraints and required validation alongside the skill's planning questions.
2. Present the proposed implementation plan, assumptions and unresolved questions in the conversation.
3. End the turn without changing files or external systems. Defer workspace creation, prompt-history writes, downloads, generated files, register updates and automatic remediation until approval.
4. Implement only after the user explicitly approves the proposed plan. Clarifying scope or answering a question is not approval. Resume the approved work without asking for the same approval again.

Use native Plan mode if it is already active or an available control can activate it. If native Plan mode is unavailable, or the agent cannot switch it, follow this workflow anyway. Do not claim to have switched modes or treat writing `/plan` as activating a control. The user may select native Plan mode before invoking the skill; this instruction-based workflow does not change permissions.

If inspection needs an operation that writes files or external state, include that operation and the missing information in the plan and defer it until approval. Keep planning notes in the conversation. This stage takes precedence over automatic post-planning fixes or provenance recording.

## Feature: Portable planning approval

### Scenario: Plan before implementation without mode controls (@rule:process-956)
- Given: A skill requires planning and native Plan mode cannot be activated
- When: The agent prepares its plan using read-only inspection
- Then: It presents affected components, constraints, validation and unresolved questions
- And: It ends the turn without file or external-system changes or a false mode-switch claim

### Scenario: Scope answers do not approve implementation (@rule:process-957)
- Given: The proposed plan has not been explicitly approved
- When: The user answers a planning question
- Then: Implementation remains paused and no workspace or provenance is written

### Scenario: Approval resumes execution (@rule:process-958)
- Given: The user explicitly approves the proposed plan
- When: The agent resumes the skill
- Then: It executes the approved work and validation without requiring native mode controls

### Scenario: Native mode does not replace approval (@rule:process-959)
- Given: Native Plan mode is active but the proposed plan is not approved
- When: The agent finishes planning
- Then: It ends the turn without implementation or external writes
