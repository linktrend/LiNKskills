# LiNKskills provider v2 consumer conformance

This repository supplies procedures and immutable release facts only. A
consumer selects a skill and performs local execution; neither retrieval nor a
telemetry receipt is authorization or proof of consumer-task completion.

## Required external canary flow

1. Present a Platform-bound identity and discover bounded catalogue metadata.
2. Select externally, then load only summary, sections/resources and one exact
   immutable version.
3. Verify the exact manifest/package digest and release availability before use.
4. For a mandatory skill, stop on unavailable, incompatible, revoked,
   quarantined, tampered or unsupported content. Do not use latest, stale cache,
   similarly named or native substitutes.
5. Execute locally and send either a score-10 use report with no diagnostics or
   a scored bounded issue report. Preserve only opaque consumer correlations.

LiNKsites/OpenClaw/LiNKdeveloper configuration, Platform claims, live signing
keys, consumer execution, rollout and production proof remain external HOLDs.
