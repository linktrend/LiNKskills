# Contract risk source selection and method integration

## Base source

- **Evolsb `claude-legal-skill`** at the pinned commit in `references/upstream/SOURCE-MANIFEST.json` is the base. It supplies the broad agreement intake, clause-by-clause issue spotting, evidence locator and risk-review output shape.

## Same-task methods integrated

- **Lawve contract-risk analyzer (Sneha Ganapavarapu):** same task because both analyze a supplied agreement and produce plain-language clause risk and negotiation options. Integrated its five-clause initial screen (liability, indemnity, IP, data, termination) and source-locator/plain-language output prompts. Excluded the unsupported source-era severity thresholds and market assertions.
- **Lawve technology-contract reviewer (Parth Desai):** same underlying contract-risk task, applied as a conditional technology-agreement branch. Integrated source prompts for service/API scope, training/data use, subprocessors, incidents, retention/deletion, SLA measurement/remedies, acceptance/change orders, background/foreground IP and suspension/exit. Excluded fixed-jurisdiction legal tables, fixed deadlines/caps, severity colors, and legal assertions.
- **Lawve contract-intelligence workflow reviewer:** its clause-risk/document-comparison branch maps to this task. Integrated a version-comparison procedure that records additions/changes/removals and separates textual change from risk inference. Lifecycle intake, playbook normalization, negotiation strategy, and proposal drafting remain in their distinct task packs.

## Preserved but not used as a method base

- **Lawve Kevin Tso contract-review source** has an entrypoint byte-identical to the selected Evolsb base; it is retained with provenance but adds no distinct procedure.
- The original source documents and supporting files are immutable provenance. The active instructions above own behavior. Declared source licenses and repository notice remain recorded without a license-clearance claim.
