# research

## Capability Summary
Multi-tier research gateway with cost-aware routing. Starts on low-cost web search, escalates to neural search when confidence is low, and supports brief/social synthesis tiers.

## Tiers
- `web` (Brave, default/low cost)
- `neural` (Exa, specialized/mid cost)
- `brief` (Perplexity Sonar, summary/mid cost)
- `social` (Grok, sentiment/mid cost)

## Commands
- `search --query "..." --tier auto|web|neural|brief|social`

## CLI
- `--help`
- `--version`
- `--json`

## Usage
- `bin/research search --query "latest AI agent standards"`
- `bin/research search --query "RAG retrieval benchmarks" --tier web --limit 10`
- `bin/research search --query "Summarize this domain" --tier brief`
- `bin/research search --query "Public sentiment on X" --tier social`

## Escalation Logic
- In `auto` mode, Tier 1 (`web`) runs first.
- If `web` confidence is below threshold, router escalates to Tier 2 (`neural`).

## Vault Keys
Set these with `tools/vault/bin/vault set`:
- `BRAVE_API_KEY`
- `EXA_API_KEY`
- `PERPLEXITY_API_KEY`
- `GROK_API_KEY`
