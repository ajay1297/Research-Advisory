---
name: portfolio-analysis
description: >
  PLACEHOLDER — not yet implemented. Reserved for a future skill covering
  portfolio-level analysis and advisory (e.g. holdings/exposure breakdown,
  concentration and risk checks, rebalancing suggestions — exact scope TBD).
  Do not activate this skill for any request yet; there are no trigger
  phrases defined and no pipeline implemented below.
---

# Portfolio Analysis

**Status: not yet implemented.** This is a placeholder directory reserving the
`portfolio-analysis` skill name inside the `Research-Advisory` plugin. There is
no pipeline, no scripts, and no trigger phrases here yet — nothing should treat
this file as an active skill.

## Planned scope (TBD)

To be defined. Likely candidates, subject to change once actual requirements
are set:

- Portfolio-level holdings/exposure analysis across multiple positions
- Concentration and risk checks (sector, single-name, factor)
- Cross-references into `report-generator`'s per-company research where relevant

## Structure

Once implemented, this skill should follow the same shape as
[`report-generator`](../report-generator/SKILL.md): a `SKILL.md` with real
trigger phrases and a pipeline, plus its own `reference/`, `scripts/`, and
`README.md` as needed — self-contained under this directory, writing any
working state/deliverables outside the plugin (e.g. `~/.portfolio-analysis/`),
never inside `skills/portfolio-analysis/` itself.
