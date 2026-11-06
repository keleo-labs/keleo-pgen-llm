Feature: Manage independent content repositories
  As a practice or report author
  I want selected workspaces versioned outside the code repository
  So that each collection has its own history and access boundary

  Background:
    Given this project provides utils/content-repos.py
    And selected items use practices/, baselines/, or reports/ paths

  Scenario: Create a local content repository
    Given the user requests a new content repository
    When the skill creates it
    Then the git repository is outside this code repository
    And it has the documented generated-file ignore rules
    And the versioned local configuration names its path
    And no remote is created unless the user requested one

  Scenario: Explain a content repository to readers
    Given a new or existing content repository is being set up
    When the skill prepares its root README
    Then the README briefly explains Keleo and identifies the repository's authored content
    And it links to the keleo-language and keleo-pgen-llm GitHub projects
    And any existing repository description is preserved

  Scenario: Expose only selected items from an existing repository
    Given a content repository contains selected and unselected items
    When the skill registers it and mounts the selected items
    Then only selected items appear at the project paths
    And the mount health check passes

  Scenario: Import an existing local item
    Given the user chooses a repository for a local practice, baseline, or report
    When the skill runs the utility's add command with --fix
    Then the content is copied and verified in that repository
    And the original is retained under content-import-backups/
    And the project path becomes a link to the repository item

  Scenario: Report a collision without overwriting
    Given the selected item path is occupied by different content
    When the skill previews or checks the mount
    Then it reports the collision and stops that item
    And neither directory is overwritten

  Scenario: Inspect or detach a repository item
    Given a selected item is mounted
    When the user asks for status or to unmount it
    Then the skill uses git status for the owning repository or the utility's unmount command
    And unmount leaves the repository content intact
