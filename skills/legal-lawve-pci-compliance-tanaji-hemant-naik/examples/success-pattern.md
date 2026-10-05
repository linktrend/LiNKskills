# Worked synthetic success example — legal-lawve-pci-compliance-tanaji-hemant-naik

**Task:** golden-task from this skill’s `references/eval-suite.json`.

**Case facts**
- `entity_role_and_volume`: Synthetic online merchant, transaction volume and validation tier unknown.
- `data_flow_inventory`: Hosted checkout returns a payment token; PAN capture is by third party; merchant logs and support tooling not mapped.
- `architecture_and_segmentation`: Network diagram missing; segmentation test not supplied.
- `control_evidence`: MFA policy exists; latest access review and ASV scan absent.
- `current_pci_authority`: No current PCI SSC standard/SAQ supplied.
- `scope_and_as_of`: Synthetic scope only; law applicability unknown unless identified in the case facts.

**Source route:** lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/pci-compliance-tanaji-hemant-naik/SKILL.md

**Worked task output**
Scope remains open: hosted checkout returns a token and a third party captures PAN, but merchant logs/support tools and network paths are unmapped; tokenization alone does not exclude connected systems. Missing: transaction volume/tier, network diagram, segmentation test, latest access review, ASV scan and current PCI SSC standard/SAQ. Obtain validated data flow and current scope rules; mark missing evidence unresolved, not failed controls. No SAQ tier or PCI certification claimed.

**Method/contract check:** The example follows this skill’s active trigger and procedure in `SKILL.md` and `advanced/advanced.md`; it is bounded by the output contract in `references/schemas.json`. Where a source-selection/applicability note is present, use that route and its stated limits; it does not substitute for current authority. It does not represent an executed native operation.

**Limit:** All case facts are synthetic. No current primary legal text is supplied unless stated in the case; legal applicability and conclusions remain unverified where the example says so. This is a draft demonstration, not legal advice, approval, filing, or external action.
