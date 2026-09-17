# Dependency Graph and Roadmap

## Graph

```mermaid
flowchart TD
    P00[PKT-00 baseline and ADR approval] --> P01[PKT-01 taxonomy and contracts]
    P01 --> P02[PKT-02 MCP v2 discovery and retrieval]
    P01 --> P03[PKT-03 external collection lifecycle]
    P03 --> P04[PKT-04 security privacy eval Librarian]
    P03 --> P05[PKT-05 Google collection]
    P04 --> P05
    P04 --> P06[PKT-06 Research]
    P04 --> P07[PKT-07 Browser Use]
    P04 --> P08[PKT-08 Communication]
    P08 --> P09[PKT-09 Operational Reporting]
    P08 --> P10[PKT-10 Personal Compliance]
    P06 --> P11[PKT-11 Time Management]
    P08 --> P11
    P08 --> P12[PKT-12 Private Health]
    P06 --> P13[PKT-13 Executive Governance]
    P08 --> P13
    P13 --> P14[PKT-14 Planning Performance]
    P03 --> P15[PKT-15 Finance Odoo]
    P03 --> P16[PKT-16 Sales Odoo]
    P03 --> P17[PKT-17 Legal]
    P06 --> P18[PKT-18 Meetings]
    P17 --> P19[PKT-19 Procurement]
    P13 --> P20[PKT-20 Workforce]
    P07 --> P21[PKT-21 Incident Continuity]
    P13 --> P21
    P05 --> P22[PKT-22 Role manifests]
    P09 --> P22
    P10 --> P22
    P11 --> P22
    P12 --> P22
    P13 --> P22
    P14 --> P22
    P15 --> P22
    P16 --> P22
    P17 --> P22
    P18 --> P22
    P19 --> P22
    P20 --> P22
    P21 --> P22
    P05 --> P23[PKT-23 cross-source qualification]
    P22 --> P23
    P02 --> P24[PKT-24 catalogue migration integration]
    P03 --> P24
    P23 --> P24
    P04 --> P24
    P24 --> P25[PKT-25 provider exact-tree proof]
    P25 --> X04[XPKT-04 OpenClaw Lisa canary]
    X01[XPKT-01 Platform review apply] --> X04
    X02[XPKT-02 OpenClaw v2 consumer] --> X04
    X03[XPKT-03 Autowork polling] --> X04
    X04 --> X05[XPKT-05 independent cross-repo verification]
    X05 --> P26[PKT-26 final reconciliation]
```

## Ordered waves and safe parallelism

| Wave | Ready set | Admission rule | Exit gate |
|---|---|---|---|
| 0 | PKT-00, then PKT-01 | Serial | Founder-approved ADR/schema/protocol direction and frozen contracts |
| 0B | PKT-02 and PKT-03 in parallel; PKT-04 after PKT-03 | Dependency-aware; PKT-04 hardens the lifecycle after its interfaces exist | Provider, lifecycle, and privacy foundations integrate cleanly |
| 1 | PKT-05–PKT-08 | Dependency-parallel | Google manifest plus three shared methods pass focused evals |
| 2 | PKT-09–PKT-12 | Dependency-parallel after required shared methods | Four Lisa families qualify with synthetic fixtures only |
| 3 | PKT-13–PKT-17 | Dependency-ready pool | First five business families qualify |
| 4 | PKT-18–PKT-21 | Dependency-ready pool | Remaining four business families qualify |
| 4B | PKT-22, then PKT-23 | Serial role references and qualification evidence | Five role manifests validate; all intended releases are deliberately classified; no activation occurs |
| 5 | PKT-24, then PKT-25 | Serial shared/generated paths and full proof | Exact provider source candidate proven |
| Cross-repository | XPKT-01–XPKT-03 may proceed once their inputs freeze; XPKT-04 follows provider and consumer readiness | Each owning repository uses its own manifest/lease | Lisa canary and external receipts complete |
| Closeout | XPKT-05, then PKT-26 | Independent verification before closure | Every PRD criterion classified and no unsupported proof claim remains |

The scheduler may admit at most one local and two hosted packets and must reduce concurrency when resource snapshots, leases, path ownership, or interactive pressure are uncertain. “Parallel” means dependency-compatible, not automatically simultaneous.

## Cross-repository gates

- **G1 Platform contract:** authentication claims and technical eligibility fixtures must be frozen before provider conformance; migration review/apply remains Platform-owned.
- **G2 OpenClaw consumer:** standard MCP v2 consumption, exact release verification, local execution, pins, private SQLite state, and rollback are OpenClaw-owned.
- **G3 Autowork:** polling/diff/candidate submission is deterministic and idempotent; qualification and current pointers remain Skills-owned.
- **G4 Brain rules:** Browser Use and standing-rule proposals consume approved Brain rules but cannot create or technically enforce them.
- **G5 Provider-live:** no stage/VPS/production claim until exact source, identity, migrations, endpoint, consumer, and rollback receipts align.

## Critical path

`PKT-00 -> PKT-01 -> PKT-03/PKT-04 -> PKT-05 and shared methods -> Lisa/business content -> PKT-22 -> PKT-23 -> PKT-24 -> PKT-25 -> XPKT-04 -> XPKT-05 -> PKT-26`

MCP completion (PKT-02) may proceed beside the external lifecycle, but it must finish before catalogue integration and any consumer canary.
