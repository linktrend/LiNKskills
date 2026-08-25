# Wave 2 — Lisa-Canary Reusable Skill Families

These are agent-agnostic releases with synthetic fixtures. Every executor must read `../LISA-CANARY-BINDINGS.md` and prove the generic contract can support those values without copying instance bindings into the release. Schedules, addresses, account/calendar IDs, private records, personal wording, runtime state, and delivery remain outside LiNKskills. Each packet must map and supersede overlaps rather than preserve two authorities.

## PKT-09 — Operational Reporting

**Depends on:** PKT-08.

**Objective:** Replace hardcoded reporting drafts with one reusable multi-mode family.

**Required modes:** Executive Digest, Flash Report, concise no-material-change, supervised-agent summary, maintenance-result input.

**Acceptance scenarios:** morning/evening delta windows; verified completed work only; work/personal calendar excluding Routine; Principal Tasks distinguished; own mailbox only; attention-worthy email only; compact supervised-agent state; morning maintenance input; evening remaining work; omission of empty sections; deadlines not start times; supplied Battery Status; one-line no change; no health/selfie duplication; final checkpoint does not request another reading; structured mobile output with no emojis.

**Migration:** Assess `executive-sync-8am` and `studio-health-reporting`; publish one new authority and explicit supersession mapping without rewriting immutable usable content.

**Evidence:** Mode schema, omission/verification tests, synthetic end-to-end reports, migration finding.

## PKT-10 — Personal Compliance

**Depends on:** PKT-08.

**Objective:** Cover selfie compliance and adaptive battery tracking in one reusable release.

**Acceptance scenarios:** configurable valid window; early/Completed/Reported Late/Missed states; conditional reminders and calendar deduplication; private consumer state; charger/location-specific rate learning; discharge rate; saturation-aware unplug interval; material-rate updates; 35% projections; silent no-alert hourly checks; overnight alert without maintenance cancellation; bundled measurements; final daily checkpoint; image extraction, material uncertainty confirmation, and correction history.

**Privacy:** No real image, battery value, location, routine, rate, schedule, or identifier in skill/eval/telemetry.

**Evidence:** State-transition/property tests, rate/projection fixtures, privacy-negative report, output-contract tests.

## PKT-11 — Time Management

**Depends on:** PKT-06, PKT-08.

**Objective:** Publish the store-independent reasoning contract from intake through monthly reporting.

**Acceptance scenarios:** confirmed versus Provisional intake; short capture receipt; read-only provisional research; authority before commitment; owner/importance/difficulty/period/dependency/unlock/deadline assessment; priority order; stable `T-` IDs and external mappings; all settled statuses; protected work periods and breaks; flexible-period decision; continuous weekly plan and four-week look-ahead; mobile Monday email; decision options; morning/evening review; no acknowledgement inference; conditional end check; evidence verification; monthly report; capacity-state replanning without health causes; standing-rule proposal without activation.

**Migration:** Reuse applicable `department-head` and `task-decomposition` reasoning while retaining their distinct generic uses only if non-overlapping.

**Evidence:** Status/state-machine tests, planning fixtures, authority-negative tests, estimate-learning tests, migration matrix.

## PKT-12 — Private Health and Wellbeing

**Depends on:** PKT-08.

**Objective:** Publish one private-domain health tracking/reporting skill with strict data separation.

**Acceptance scenarios:** initial/monthly assessment with `not_reported`; three checkpoints with separate 1–5 energy/mood/stress and capacity; no redundant known questions; calendar reminder deduplication; hydration from bottle/remaining values; treatment/appointment mode; combined dose/dose-change record; nutrition/protein estimates labeled; meal/photo support; evidence-based exercise proposals without spot-reduction claims; sleep duration calculation; separate scale/device/source; waist and bowel tracking; material image uncertainty and correction records.

**Safety/privacy:** No diagnosis or treatment change; no real personal data; only capacity state may leave the private system; rejected automatic emergency-support wording/behavior is prohibited.

**Evidence:** Synthetic category coverage, private-destination contract, privacy-negative fixtures, image-correction tests, wording prohibition test.
