# Sequence diagram

Route C, `sequenceDiagram`.

## When

Time and ordering are the subject. Tracing a distributed call, an
authorisation flow, a retry path, or a race condition. Audience is engineers
and QA.

A sequence diagram answers "in what order, and who waits for whom". If the
question is "what are the parts", that is a C4 container diagram. Drawing one
per interesting interaction is right; drawing one per endpoint is waste.

## Notation

- `participant X as Label` fixes the order along the top. Declare them in the
  order you want, or Mermaid orders them by first appearance.
- `->>` is a call, `-->>` a return. Use returns sparingly — only where the
  response content or its timing matters. Every call getting a return line
  doubles the height and halves the readability.
- `activate` / `deactivate`, or the `+`/`-` shorthand, show how long a
  participant is busy. This is what makes a blocking call visible.
- `alt` / `else`, `opt`, `loop`, `par` and `critical` carry the branching.
  Use them rather than drawing three near-identical diagrams.
- `Note over A,B: …` for a constraint or a timeout that is not a message.
- `autonumber` when you want to refer to steps in prose.

## Spec

```
---
method: sequence
title: Authorisation code grant
description: Client, gateway and token service during sign-in.
render: picture
---
sequenceDiagram
    autonumber
    participant C as Client
    participant G as API gateway
    participant S as Token service
    C->>+G: GET /authorise
    G->>+S: exchange grant
    alt grant valid
        S-->>-G: access token (5 min TTL)
        G-->>-C: 302 with session cookie
    else grant expired
        S-->>G: 400 invalid_grant
        G-->>C: 302 to sign-in
    end
    Note over G,S: gateway caches the token for its TTL
```

## Mistakes this invites

- **A return arrow for every call.** Shows nothing and doubles the height.
- **No activation bars** on a diagram whose point is that something blocks.
- **Branches drawn as separate diagrams** instead of `alt`, so the reader
  cannot see they are alternatives.
- **Participants that are classes.** At this level they should be services,
  processes or people — something that can be waiting.

## Why this one is a picture

Route C. Mermaid draws it and the engine themes the result; it does not
become editable Google Slides shapes. Lifelines, activation bars and
attribute compartments have no Slides equivalent, so reading the geometry
back would produce a heap of loose rectangles that is worse than the picture.
Set `render: picture` explicitly — it is the default for this method anyway.
