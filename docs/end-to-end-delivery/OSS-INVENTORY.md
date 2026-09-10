# OSS and runtime inventory

This inventory avoids reinstalling healthy shared components. Versions and
digests must be refreshed at execution time without printing secret values.

| Component | Current state / host | Sole shared owner | Required executor configuration and connection | Delivery decision |
|---|---|---|---|---|
| Docker Engine + Compose | Installed and running on LiNKserver 01; existing `linktrend-core-services` project hosts Skills. | Platform/Server 01 operations | Preserve current project, network, volumes, image and compose projection; build/pull only approved digest. | Reuse; do not install another container runtime. |
| LiNKskills Python image | Running `linux/amd64` image digest `sha256:7cf2780…`; source release `7067716…`. | LiNKskills artifact; Platform deploys | Python ≥3.11; exact source/tree/image labels; packages core, publisher, eval runner, persistence, gateway, MCP, client, librarian domain and tool runtime as required. | Replace only with an independently verified release candidate after approval. |
| PostgreSQL/Supabase | Existing Platform stage/prod projects; current Skills store probe fails. | LiNKplatform | Governed migration package, least-privilege `svc_lskills_runtime`/worker roles, SecretRef DSN, TLS, backup/restore receipt. | Reuse; no new database project and no direct Skills live DDL. |
| Google Secret Manager | Existing server secret custody and read-only mount pattern. | Platform security/operations | Environment contains names/paths only; keys and DSNs render to root-owned files; never arguments/logs/Git. | Reuse; provision/rotate after approval as execution work. |
| PACI / Platform identity | Existing HTTPS issuer/JWKS/token/introspection service configured in container. | LiNKplatform | Audience `lskills-api`, scope `lskills`, separate client/runtime bindings, trusted mint allowlist, ES256 key file, expiry/rotation/revocation. | Reuse after current Platform recovery receipts; do not create a Skills identity authority. |
| Tailscale | Installed; private routes exist for other loopback services, not direct Skills `18798`. | Platform networking | Select one private Skills route only if required; retain loopback/container-network restriction otherwise. | Reuse; no public ingress by default. |
| Prometheus + Grafana + node exporter | Existing and healthy on Server 01 according to current recovery evidence. | Platform observability | Add/verify Skills scrape, dashboards and alerts; redact payloads and credentials. | Reuse; do not add another monitoring stack. |
| Sealed Linux evaluation | Docker-based confined executor and digest-pinned image contract exist in repo. | LiNKskills qualification | External issuer key through SecretRef, immutable evaluator image digest, network isolation, exact runtime/tool profile and retained receipts. | Configure and run for five initial releases after approval; do not use prompt-only substitutes. |
| LiNKskills MCP | Source package exists; target v2 is sessionless/resource-first. | LiNKskills contract; consumer owns process/adapter | Cursor/Codex project/provider adapter or OpenClaw host bridge connects privately to exact provider route and validates digest/pins. | Configure existing package; no separate public MCP daemon is required unless the approved adapter needs it. |
| Generic Librarian host | Platform source exists; production Skills worker operation is unproven. | LiNKplatform host; LiNKskills domain worker | Exact domain-worker artifact pin, separate identity, queue/schedule/retry/DLQ, redacted audit and disable switch. | Reuse; Platform integrates, LiNKskills supplies conformance. |
| Bubblewrap | Used inside the sealed Linux evaluator path. | LiNKskills evaluation image | Digest-pinned image, denied network, allowed executable/file paths, no privileged host install outside the evaluator. | Reuse in the evaluation image. |

## Not required for initial delivery

- Kubernetes, a second staging VPS, Traefik, Redis, NATS, n8n, or a second
  gateway/database/monitoring stack.
- The retired Logic Engine, its Compose configuration, or any combined
  Brain/Skills process.
- Paid model/provider jobs. Ordinary work routes through Cursor SDK/API Grok 4.6
  Medium; Luna High is used only where the installed route policy or founder
  instruction makes it appropriate.

If an executor proposes one of these components, it is a material architecture
change and requires founder approval rather than a routine implementation
choice.
