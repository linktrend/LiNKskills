# SKILLS_CATALOGUE

Descriptive index of all registry targets (skills + tools), grouped by department/function.

- Total Targets: **53**
- Tools: **19**
- Skills: **34**

## Platform Core
- Tool `gws`: Pinned Google Workspace CLI integration sourced from the `link-gws-cli` fork with strict checksum/version pinning. (`/tools/gws`)
- Tool `ltr`: LiNKtrend Runtime gateway for non-Workspace Google services, non-Google services, and local runtime controls. (`tools/ltr/src/cli.py`)
- Tool `memory`: Supabase-backed memory tool with scoped recall plus Markdown notes in lsl_memory.notes. (`/tools/memory`)
- Tool `n8n`: n8n workflow API tool for read, create, activate/deactivate, and trigger operations with vault-backed API keys. (`/tools/n8n`)
- Tool `n8n-bridge`: Secure webhook trigger bridge for local n8n workflows using n8n API wrapper commands with Vault-backed token retrieval. (`/tools/n8n-bridge`)
- Tool `asset-filer`: Uploads assets through ltr and registers metadata records for retrieval in lsl_memory.assets. (`/tools/asset-filer`)
- Tool `usage`: Langfuse-based usage telemetry tool with silent local fallback, host defaulting, and vault-managed credentials. (`/tools/usage`)
- Skill `skill-template`: Golden template for creating production-grade LiNKskills skills. (`/skills/skill-template`)
- Skill `skill-architect`: Designs, migrates, and refines production-grade skills following the LiNKskills Golden Template. (`/skills/skill-architect`)
- Skill `tool-architect`: Designs, wraps, and validates CLI-first tools for the LiNKskills Global Tools Registry. (`/skills/tool-architect`)
- Skill `workflow-architect`: Designs n8n workflows as JSON, creates them via API, then activates and tests them autonomously. (`/skills/workflow-architect`)

## Product Strategy & Discovery
- Skill `prd-architect`: Transforms a vibe or idea into a professional technical specification with architecture, constraints, and acceptance criteria. (`/skills/prd-architect`)

## Engineering & Delivery
- Tool `playwright-cli`: Stateless Playwright CLI wrapper for browser install and one-shot automation tasks with deterministic JSON outputs. (`/tools/playwright-cli`)
- Tool `fast-playwright`: FastMCP Playwright server wrapper for interactive, session-based browser automation. (`/tools/fast-playwright`)
- Tool `sandbox`: Ephemeral Docker runtime for isolated command execution with memory limits and default network isolation. (`/tools/sandbox`)
- Tool `text-echo`: Deterministic echo utility for smoke-testing parser and wrapper pipelines. (`/tools/text-echo`)
- Skill `lead-engineer`: Refactored senior execution model for PRD decomposition, factory.json routing, and sub-agent sessions_spawn coordination. (`/skills/lead-engineer`)
- Skill `studio-architect`: Template-first architecture skill that enforces factory.json discovery and baseline initialization before custom development. (`/skills/studio-architect`)
- Skill `software-pm`: Software PM skill that decomposes PRDs into factory-aligned technical backlogs with QA-gated Definition of Done. (`/skills/software-pm`)
- Skill `devops-sre`: DevOps/SRE skill for Dockerization, VPS deployment hardening, and LSL_MASTER_KEY security enforcement. (`/skills/devops-sre`)
- Skill `persistent-qa`: Independent QA skill with recurrence tracking through Supabase-backed BUG_HISTORY memory. (`/skills/persistent-qa`)
- Skill `ui-ux-guardian`: Design system enforcement skill using Playwright-driven visual regression audits and policy-based gating. (`/skills/ui-ux-guardian`)
- Skill `blocker-resolution`: Escalation skill that triggers Root Cause Analysis when worker PROGRESS.md remains Blocked beyond two turns. (`/skills/blocker-resolution`)

## Research & Intelligence
- Tool `research`: Multi-tier research gateway with cost-aware routing across web, neural, brief, and social tiers. (`/tools/research`)
- Skill `market-analyst`: Runs competitor teardown and SWOT analysis using tiered research workflows and confidence-based escalation. (`/skills/market-analyst`)
- Skill `search-strategy`: Defines research intent, confidence-based tier escalation, and HITL controls for deep research sessions. (`/skills/search-strategy`)
- Skill `task-decomposition`: Applies Factored Cognition to break complex studio work into atomic verifiable plans. (`/skills/task-decomposition`)
- Skill `citation-enforcer`: Enforces evidence-first outputs by requiring Memory/Search/File citation for every claim. (`/skills/citation-enforcer`)
- Skill `self-critique-loop`: Runs System 2 self-audit loops to detect and correct errors before finalization. (`/skills/self-critique-loop`)
- Skill `self-improvement`: Analyzes execution_ledger trends to propose versioned upgrades for library tools and skills. (`/skills/self-improvement`)
- Skill `engagement-to-strategy-loop`: Analyzes views, CTR, and sentiment to deliver high-signal strategic feedback loops back to marketing. (`/skills/engagement-to-strategy-loop`)

## Growth & Marketing
- Tool `ad-intel`: Ad performance monitor for Spend vs CTR anomaly detection using ltr bridge inputs and deterministic JSON alerts. (`/tools/ad-intel`)
- Tool `sync-scheduler`: Calendar scheduling helper that uses gws to suggest Project Review time slots in deterministic JSON. (`/tools/sync-scheduler`)
- Skill `marketing-strategist`: Senior VP of Growth skill that decomposes product PRDs into multi-channel strategy with mandatory MARKETING_STRATEGY.md output. (`/skills/marketing-strategist`)
- Skill `seo-semantic-auditor`: Reverse-engineers competitor keyword strategy via Brave/Exa research and outputs prioritized content gaps. (`/skills/seo-semantic-auditor`)
- Skill `channel-ops`: Platform operations skill for YouTube, TikTok, and X scheduling, comment management, and support-to-sales funnel execution. (`/skills/channel-ops`)

## Creative & Content
- Tool `doc-engine`: Document engine for OCR via unstructured, conversion via pandoc, and Markdown print-to-Google-Doc. (`/tools/doc-engine`)
- Tool `social-ltr`: Unified social wrapper for posting and comment retrieval across YouTube, TikTok, and X via ltr. (`/tools/social-ltr`)
- Skill `creative-director`: Senior Creative Lead skill that decomposes marketing briefs into asset orders and orchestrates n8n rendering triggers. (`/skills/creative-director`)
- Skill `creative-qa`: High-fidelity creative QA gate that audits assets against brand guidelines and PRD with mandatory PASS/FAIL plus revision logic. (`/skills/creative-qa`)

## Finance & Revenue
- Tool `stripe`: Stripe billing operations tool with vault-backed API key and invoice retrieval commands. (`/tools/stripe`)
- Tool `shopify`: Shopify commerce operations tool with vault-backed access token and product listing commands. (`/tools/shopify`)
- Skill `revenue-adapter-base`: Normalizes YouTube, AdSense, and Stripe revenue inputs into canonical Venture Studio Transaction records. (`/skills/revenue-adapter-base`)
- Skill `studio-controller`: Financial oversight skill delivering GAAP reporting, reconciliation, and Supabase lsl_finance transaction logging. (`/skills/studio-controller`)

## Operations, Governance & Executive
- Skill `department-head`: COO coordination skill for managing Lead Engineer and QA execution via PROGRESS.md-driven governance. (`/skills/department-head`)
- Skill `studio-health-reporting`: Aggregates lsl_memory.audit_logs and PROGRESS.md streams into Venture Studio Health Reports for COO oversight. (`/skills/studio-health-reporting`)
- Skill `executive-sync-8am`: Exec sync skill that starts 06:00 Taipei data collection and produces the 08:00 AM Wins/Blockers/Financial Health briefing. (`/skills/executive-sync-8am`)
- Skill `repository-manager`: Enforces progress-sync handoffs, branch discipline, and staged file commit safeguards. (`/skills/repository-manager`)
- Skill `audit-protocol`: Enforces predictive intent logging to LTRAuditLogger before write actions across gws, ltr, and n8n. (`/skills/audit-protocol`)
- Skill `git-safeguard`: Requires mandatory safety checklist review (`git status`, `git diff --cached`) before any push. (`/skills/git-safeguard`)
- Skill `smart-file-clerk`: Senior document manager skill for hybrid Supabase/GDrive storage and OCR indexing of financial/legal documents. (`/skills/smart-file-clerk`)

## Security & Compliance
- Tool `vault`: Encrypted credential vault using LSL_MASTER_KEY with audited set/get/list operations. (`/tools/vault`)
- Skill `compliance-guardian`: Platform legal and safety specialist for YouTube/Meta terms monitoring, AI disclosures, and publication compliance gating. (`/skills/compliance-guardian`)
