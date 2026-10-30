# Entity-relationship diagram

Route C, `erDiagram`.

## When

Agreeing entities and cardinality before a schema exists, or documenting one
that does. Audience is data architects, DBAs and the developers who will
write the migrations.

Three tiers, and saying which you are at prevents most arguments:

| Tier | Carries | Leaves out | For |
|---|---|---|---|
| Conceptual | Entities and relationships | Attributes, keys, types | Agreeing vocabulary with the business |
| Logical | Attributes, candidate keys, exact cardinality, 3NF | Any specific engine | Design review |
| Physical | Concrete types, FKs, indexes, partitions, deliberate denormalisation | Nothing | Migration and performance work |

A conceptual model with column types in it is a logical model that has
confused its audience.

## Notation

Crow's foot cardinality, which Mermaid writes as a pair of markers:

| Mermaid | Means |
|---|---|
| `\|\|--o{` | one to zero-or-many |
| `\|\|--\|{` | one to one-or-many |
| `}o--o{` | many to many |
| `\|\|--\|\|` | one to one |

Every relationship takes a verb phrase read from left to right: `CUSTOMER
\|\|--o{ ORDER : places`. "has" is almost never the right verb and usually
means the relationship has not been thought about.

Mark keys with `PK`, `FK` and `UK` at logical and physical tiers.

## Spec

```
---
method: erd
title: Order schema
description: Logical model for the ordering domain.
render: picture
---
erDiagram
    CUSTOMER ||--o{ ORDER : places
    ORDER ||--|{ ORDER_LINE : contains
    PRODUCT ||--o{ ORDER_LINE : "appears in"
    CUSTOMER {
        uuid id PK
        string email UK
        string name
    }
    ORDER {
        uuid id PK
        uuid customer_id FK
        date placed_on
    }
```

## Mistakes this invites

- **Not saying which tier.** The commonest cause of a review talking past
  itself.
- **Optionality guessed rather than decided.** `o{` versus `|{` is a real
  business rule: can an order exist with no lines?
- **"has" as every verb.** Says nothing and hides unconsidered relationships.
- **Many-to-many left unresolved at physical tier.** It needs a join table.

## Why this one is a picture

Route C. Mermaid draws it and the engine themes the result; it does not
become editable Google Slides shapes. Lifelines, activation bars and
attribute compartments have no Slides equivalent, so reading the geometry
back would produce a heap of loose rectangles that is worse than the picture.
Set `render: picture` explicitly — it is the default for this method anyway.
