# Cloud topology

Route A, layout `flow` with nested `groups`.

## When

A design review or a security audit needs to see containment and perimeters,
not just which service calls which. Audience is cloud architects, platform
engineers and security reviewers.

If the question is "what are the moving parts", a C4 container diagram is
cheaper and clearer. Reach for this when the *boundaries* are the subject.

## Notation

**Nesting is the content.** Resources sit in subnets, subnets in availability
zones, AZs in a VPC or VNet, that in a region. A group names its `parent`,
which is what lets the engine draw the hierarchy:

```json
"groups": [
  {"id": "region", "label": "eu-west-1"},
  {"id": "vpc", "label": "VPC 10.0.0.0/16", "parent": "region"},
  {"id": "az-a", "label": "eu-west-1a", "parent": "vpc"},
  {"id": "sub-a", "label": "Private 10.0.1.0/24", "parent": "az-a"}]
```

Four conventions worth holding to, each of which an auditor will look for:

1. **Label subnets with their CIDR.** A subnet without one is decoration.
2. **A regional resource spans its zones.** A load balancer belongs to the
   VPC group, not inside one AZ — putting it in one misstates the resilience
   posture.
3. **Security perimeters are explicit.** Draw a security group as its own
   group with a label naming the permitted ports, rather than implying it.
4. **Show egress, not just ingress.** NAT gateway, internet gateway, or
   PrivateLink endpoint. Outbound paths are where exfiltration surface lives
   and are the thing most often left off.

Use `shape: cylinder` for stores and queues, `rect` for structural elements,
and `dash: dashed` for asynchronous or replicated paths.

This repository has no vendor icon sets. For an external audit where AWS or
Azure iconography is expected, say so and point at diagrams.net or Cloudcraft.

## Mistakes this invites

- **Flat groups.** Without nesting it is a service diagram with a box drawn
  round it, and it answers no boundary question.
- **Omitting egress.** The most common gap, and the one a security reviewer
  notices first.
- **A load balancer inside one AZ.** Quietly claims a single point of failure
  that does not exist, or hides one that does.
- **Nesting past four levels.** The engine reports rather than drawing
  something unreadable. Split by region or by tier.
