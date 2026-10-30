# Class diagram

Route C, `classDiagram`.

## When

Domain logic is intricate enough that inheritance, composition and
cardinality need stating. Domain-driven design entity modelling, or an
interface contract someone has to implement against.

Draw the part that is hard. A class diagram of an entire codebase is
generated output nobody reads; a class diagram of the one aggregate with
subtle invariants earns its place.

## Notation

- Visibility: `+` public, `-` private, `#` protected, `~` package.
- Relationships, and the distinction matters:

| Mermaid | Means |
|---|---|
| `<\|--` | inheritance |
| `*--` | composition — the part dies with the whole |
| `o--` | aggregation — the part outlives the whole |
| `-->` | association |
| `..>` | dependency |
| `..\|>` | realises an interface |

- Cardinality goes in quotes on each end: `Order "1" *-- "1..*" OrderLine`.
- `<<interface>>` and `<<abstract>>` annotations.
- Show the methods that carry the invariants, not every accessor.

## Spec

```
---
method: class
title: Order aggregate
description: Entities inside the order consistency boundary.
render: picture
---
classDiagram
    class Order {
        +OrderId id
        +CustomerId customer
        -Money total
        +place() void
        +cancel(reason) void
        -recalculate() void
    }
    class OrderLine {
        +ProductId product
        +int quantity
        +Money lineTotal()
    }
    class PricingPolicy {
        <<interface>>
        +priceFor(ProductId, int) Money
    }
    class VolumePricing
    Order "1" *-- "1..*" OrderLine : contains
    Order ..> PricingPolicy : prices with
    PricingPolicy <|.. VolumePricing
```

## Mistakes this invites

- **Composition where aggregation is meant.** `*--` says the part cannot
  exist without the whole. It is a real claim about lifetime, and getting it
  backwards misleads the implementer.
- **Every getter and setter listed.** Noise. Show the behaviour that enforces
  an invariant.
- **No cardinality**, which leaves the most useful information out.
- **Diagramming the whole codebase** rather than the part that is hard.

## Why this one is a picture

Route C. Mermaid draws it and the engine themes the result; it does not
become editable Google Slides shapes. Lifelines, activation bars and
attribute compartments have no Slides equivalent, so reading the geometry
back would produce a heap of loose rectangles that is worse than the picture.
Set `render: picture` explicitly — it is the default for this method anyway.
