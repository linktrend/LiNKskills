# Worked synthetic success example — legal-lawve-regulatory-threat-model-ansvar-ai

**Task:** golden-task from this skill’s `references/eval-suite.json`.

**Case facts**
- `system_snapshot`: Synthetic support chatbot: web UI → API service → hosted model; admin console separate trust zone.
- `data_flows_and_people`: User messages may contain email addresses; logs and model retention unspecified.
- `threat_scope`: Protect account data, prompt content, admin credentials and service availability.
- `jurisdictions_and_roles`: Operating entity and market not provided; legal scope unknown.
- `source_evidence`: Architecture sketch only; dependency list and current vulnerability feed absent.
- `scope_and_as_of`: Synthetic scope only; law applicability unknown unless identified in the case facts.

**Source route:** lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/regulatory-threat-model-ansvar-ai/SKILL.md

**Worked task output**
Intake output (no workflow run): trust boundaries shown are web UI → API → hosted model, with a separate admin console. Assets are account data, prompts, admin credentials and availability. Email may occur in user messages; log/model retention, dependency inventory, vulnerability feed, operating entity and market are unknown. Request data-flow and retention evidence, dependency/SBOM and current authorized findings. No STRIDE/LINDDUN or Ansvar result is simulated; legal scope remains unknown.

**Method/contract check:** The example follows this skill’s active trigger and procedure in `SKILL.md` and `advanced/advanced.md`; it is bounded by the output contract in `references/schemas.json`. Where a source-selection/applicability note is present, use that route and its stated limits; it does not substitute for current authority. It does not represent an executed native operation.

**Limit:** All case facts are synthetic. No current primary legal text is supplied unless stated in the case; legal applicability and conclusions remain unverified where the example says so. This is a draft demonstration, not legal advice, approval, filing, or external action.
