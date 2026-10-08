Feature: Diagram
  As someone who needs a picture of a system, a strategy, a process or a schema
  I want the right diagramming method chosen and then produced in the house style
  So that the diagram answers the question its audience actually has

  Background:
    Given the diagram-foundation engine is available
    And the method catalogue lists each method with its audience and route

  Rule: The method is chosen deliberately, and the choice is stated

    Scenario: The method is named before anything is drawn
      Given a user asks for a diagram of their payment system
      When the skill runs
      Then it states which method it chose and why in one line
      And it does so before authoring any spec

    Scenario: Audience drives formality over notation preference
      Given the audience is a board reviewing investment
      And the subject is a microservices estate
      When the skill chooses a method
      Then it chooses a strategy or context-level method
      And it does not choose a container, component or UML-level method

    Scenario: A request with no decision behind it is challenged
      Given a user asks for "a diagram of the system" with no stated purpose
      When the skill runs
      Then it asks what decision the diagram supports
      Or it proposes a method and names the decision it assumed

  Rule: A standard is never approximated

    Scenario Outline: A method this repository cannot produce is handed off
      Given a user asks for a <method> diagram
      When the skill runs
      Then it confirms <method> is the right method for their need
      And it names <tool> as the tool to use
      And it does not produce an approximation of <method>

      Examples:
        | method          | tool            |
        | ArchiMate       | Archi           |
        | executable BPMN | Camunda Modeler |
        | isometric       | Figma           |

  Rule: Every diagram is produced from a spec that outlives it

    Scenario: The spec is kept beside the output
      Given the skill has produced a diagram
      Then a .json or .mmd spec exists alongside the rendered SVG
      And the spec carries a title and a description

    Scenario: A Mermaid spec is diagram-as-code
      Given a method whose route is Mermaid
      When the skill authors the spec
      Then the spec is a .mmd file with YAML frontmatter and Mermaid source
      And the file is committable and renderable without the skill

  Rule: Output is in the house visual language

    Scenario: A native spec renders in the house style
      Given a spec using a native layout
      When it is rendered
      Then every colour comes from the active palette
      And the spec itself names no colour

    Scenario: An imported flowchart keeps none of Mermaid's styling
      Given a .mmd flowchart spec with render mode scene
      When it is rendered
      Then the geometry comes from Mermaid's layout
      And every fill, stroke and type size comes from house tokens

    Scenario: The palette follows the destination
      Given the same spec rendered for a report and for a deck
      When each is rendered with its own palette
      Then only the colour family differs between them
      And the geometry is identical

  Rule: Editability is reported, never assumed

    Scenario: A flowchart becomes editable slide shapes
      Given a .mmd flowchart spec with render mode scene
      When it is emitted for Google Slides
      Then it produces shape and line requests
      And the shapes are native Slides types, not a picture

    Scenario: A sequence diagram stays a picture and says so
      Given a .mmd spec whose method is sequence
      When it is emitted for Google Slides
      Then the skill reports that the diagram has no shapes to emit
      And it does not emit an empty request list

    Scenario: An unreadable import degrades rather than breaking
      Given a .mmd spec with render mode scene that cannot be imported
      When it is rendered
      Then a themed picture is produced instead
      And the reason the import was abandoned is reported

  Rule: The rendered image is inspected before the work is reported done

    Scenario: The diagram is looked at
      Given the skill has rendered a diagram
      When it prepares to report completion
      Then it has rasterised the SVG and read the image
      And it has checked for overflowing text, collisions and crossed edges

    Scenario: A diagram that will not fit its frame is reported, not reshaped
      Given a diagram far taller than the 16:9 slide it is bound for
      When it is fitted to that frame
      Then the skill reports how much of the frame it fills
      And it proposes splitting the diagram or raising its abstraction
      And it does not distort the diagram to force a fit

  Rule: A spec that will not validate fails readably

    Scenario Outline: A malformed spec yields a problem list
      Given a spec with <defect>
      When it is rendered
      Then the skill reports a human-readable problem
      And no traceback reaches the user

      Examples:
        | defect                                  |
        | an edge referencing an undeclared node  |
        | an unknown shape name                   |
        | an unknown colour role                  |
        | a wardley component with no visibility  |
        | a .mmd file with no frontmatter         |
