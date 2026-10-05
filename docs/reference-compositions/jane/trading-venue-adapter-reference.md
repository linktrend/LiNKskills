# Trading venue and adapter reference

**Kind:** owner-routed technical research note; not a registered skill, connected provider, or execution adapter.

## Trigger and scope

Use when a research, market-structure, or strategy decision depends on venue-specific instrument identity, order-book meaning, authentication boundary, settlement, data freshness, order lifecycle, or execution-path behavior. It may compare named venues only when the requester supplies them. Jane should describe what must be true and what remains unknown; Eric verifies current contracts and owns adapters. Sara handles legal, jurisdiction, accounting, and tax questions. Do not select or recommend a currently usable broker from these historical source snapshots.

This reference does not place orders, connect accounts, sign transactions, obtain credentials, call providers, recommend enabling live access, alter risk controls, or activate capital. Quote, draft, simulation, order submission, chain inclusion, settlement, and final reconciliation are distinct states. If an approved downstream implementation exists, it remains within LiNKtrading and its established independent exact-version/two-channel approval gate.

## Inputs to request

Collect only what the supplied task needs:

- Research question and decision deadline; asset class, instrument/market identifiers, venue(s), and the user's intended comparison.
- Source and observation time for each quote, book, market rule, account/capability claim, and market-status fact; include timezone and freshness limit if the decision depends on it.
- Desired capability class: public/read-only data, paper simulation, draft-only proposal, or a separately authorized programmatic execution workflow. Unknown is a valid value; do not infer a capability from a product name, MCP listing, or public documentation.
- Unit convention and price representation (for example dollars, cents, probability, token quantity, base/quote units), contract multiplier/precision if supplied, and denominator for any comparison.
- If assessing an integration: current LiNKtrading owner/component and version, allowed read/write boundary, expected state transitions, reconciliation source, and already-approved authority envelope. Do not request or repeat secrets.
- Sara-owned jurisdiction, eligibility, legal interpretation, and accounting questions as explicit unresolved inputs rather than findings.

If a required identifier, timestamp/vintage, unit, market rule, or authority is missing, mark the affected row `unknown` and state what would resolve it. Do not fill from memory or silently pick a default.

## Outputs

Return a concise, dated reference packet with:

1. **Question and boundary:** exact decision being supported and what the note does not authorize.
2. **Capability/semantics matrix:** one row per named venue/path, with sourced observations separated from unknowns and from recommendations.
3. **Object map:** market/event/contract/token IDs, order/client IDs, and settlement identity only where current owner-reviewed sources establish them.
4. **Order/data lifecycle sketch:** read or quote → construct/draft → approval boundary → any separately approved effect → venue acknowledgement/status → reconciliation. Mark which steps are only conceptual versus verified for the current integration.
5. **Failure and uncertainty cases:** stale quote, invalid identifier, rejected schema, timeout/unknown submission outcome, partial fill, disconnect, mismatch, delayed settlement, and residual-account differences where relevant.
6. **Owner handoff:** current official docs/contracts Eric must verify, Sara questions, and any exact LiNKtrading source/version needed.

Do not output an executable payload, signed bytes, a command to trade, a credential-bearing configuration, or a claim of current access. Advisory strategy, sizing, exit, and monitoring recommendations are permitted when inputs support them; label them recommendations and keep them separate from any system action.

## Practical method

1. **Bound the question.** Name the instrument, decision, as-of time, and comparison. Separate market-view questions from implementation and authority questions.
2. **Classify the market model before comparing prices.** Identify whether the object is a conventional broker instrument, a binary/event contract, an on-chain outcome token, or a routed token swap. Preserve venue-specific contract and settlement distinctions; similar probabilities do not make instruments interchangeable.
3. **Normalize identifiers and units.** Keep event/series/market/condition/token identifiers distinct from order/client identifiers. Record whether a quote is a price, implied probability, bid, ask, payout, or token amount. Convert only with an explicit supplied rule and show the calculation; if the contract/multiplier is absent, do not compare nominal prices as equal exposure.
4. **Separate quote, book, route, and order.** A metadata catalog is not an order book; a quote is not a built transaction; a built transaction is not signed; a signed request is not accepted; venue acknowledgement is not fill or settlement. Capture source, observation time, sequence/status if provided, and expiry/freshness assumption for every state.
5. **Compare order-book conventions per venue.** For binary books, verify whether YES and NO sides are both represented as bids and whether the implied opposite ask is a complement under the supplied market contract. Never assume the convention transfers to another venue or that a displayed complement is executable liquidity. Preserve outcome identity, fees, tick/size units, and settlement terms.
6. **Trace authority and cryptographic boundary as requirements.** Distinguish public metadata, authenticated read, unsigned/draft construction, local signing, and remote submission. If a signature is needed, identify its owner-controlled boundary without collecting key material. No Jane-side signing, wallet/key access, brokerage auth, MCP install, or account connection.
7. **Name the path-specific risks.** For routed DEX transactions, distinguish hosted quote aggregation from self-hosted routing, route freshness, transaction construction, chain submission, and confirmation. If a bundle/relay path is in scope, separately record its grouping/atomicity claim, tip/fee policy, blockhash/expiry, landing result, and reconciliation source. Do not substitute a relay result for settlement/finality. For traditional broker APIs, preserve asset-specific action/payload and account/region boundaries; never transpose a stock payload to another product.
8. **Plan for uncertainty before retry.** On timeout or lost connection after a possible submit, call the result unknown. Eric's approved integration must query authoritative order/transaction state and reconcile balances/positions/fills before considering any retry. No blind resend, re-sign, or auto-correction. Mismatch means hold and escalate; do not create an order to repair state.
9. **Check downstream contracts and owner gates.** Eric verifies current official docs, SDK/schema, LiNKtrading seam, idempotency/status behavior, fee/settlement semantics, account permissions, and tests against the exact implementation version. Sara resolves legal/eligibility/accounting issues. Keep the change proposal advisory until the existing Lisa+Carlos two-channel approval for the exact version is present.
10. **Report evidence strength.** Give source URL/path, exact revision or access date, claim supported, observation time, and residual gap. Distinguish source statements from independently verified current facts and analyst inference. This source audit provides no current provider proof.

## Distinctions preserved from reviewed sources

| Path family | Keep distinct in analysis | Explicit exclusion / current-source requirement |
|---|---|---|
| Binary/event-contract venues (Kalshi-like and Polymarket-like source models) | Venue-specific YES/NO book conventions; event/series/market/condition/token identifiers; order-vs-market objects; off-chain order book vs on-chain token/settlement/dispute path | Do not merge them into one “prediction-market API.” Recheck present instrument terms, schemas, auth, fees, settlement/dispute and jurisdiction with current official sources and Sara. No availability, legality, KYC, or geo-eligibility claims from this note. |
| Hosted Solana route (Jupiter-like source model) | Quote, unsigned construction, local signing, network submission, confirmation/readback are separate operations; transaction version/account lookup affects construction requirements | No key use, generated tx, RPC request, endpoint, parameter, fee value, or current support assertion. Eric must inspect exact LiNKtrading transaction owner and current dependencies. |
| Self-hosted Solana route (Raptor-like source model) | A locally operated quote/routing service, stream, and submission transport have separate availability, deployment, data, and monitoring dependencies from a hosted aggregator | No service deployment, paid/free-tier guarantee, throughput/rate-limit claim, or provider recommendation. The source's deployment guide is not part of this review closure. |
| Bundle relay (Jito-like source model) | Bundle atomicity/ordering intent, tip as a distinct instruction/cost, expiry/blockhash, landing status, and chain reconciliation are separate from ordinary transaction submission | The source examples contain an undefined `keypair` reference and unsafe retry/re-sign hazards. No example code or tip formula adopted. Current relay support/semantics need Eric's review. |
| Centralized broker API (Webull source model) | Asset/product-specific order actions and schemas, region/account/environment, place versus replace, and data permissions must stay separate | Source is a dated snapshot. No current product, endpoint, exchange region, order-type, account, or sandbox/live assertion. Eric must revalidate each supported product against current official source. |
| Broker-MCP capability directory | Record authorship, read-only vs draft vs trade-capable, paper vs live, local vs remote, auth/permission, and source freshness as independent axes | Directory source was a dated snapshot and is not a current selector. No MCP is installed or assumed. Do not equate “MCP available” with authority or safe live capability. |
| Automated webhook-to-broker pipeline | None of the source's auto-trader workflow is adopted | Explicitly excluded: webhook-triggered model gate, zero-DTE trade pipeline, automated broker submission, thresholds, and code. It conflicts with the bounded Jane authority and would require a separate product decision. |

## Defect and repair rules

- Source examples and provider schemas are pinned historical material, not validated current contracts. Replace any implementation dependency with Eric's verification against the exact LiNKtrading source, installed dependency, and current official venue contract.
- One source bundle example references an undefined signing object; another transaction retry sample can resubmit without reconciling status or obtaining a fresh authorized decision. Do not reuse either sample. Require explicit typed input, owner-controlled signing, authoritative status readback, and idempotent or manual hold behavior before any later implementation review.
- Market identifiers, client order identifiers, price scales, tick sizes, fee units, and probability complements are not interchangeable. Missing unit/contract mapping yields an unresolved row, not a conversion guess.
- A hosted quote router and self-hosted routing service have different operational dependencies; a REST order, chain transaction, and relay bundle have different lifecycle guarantees. Never flatten them into a generic “submit” step.
- Broker MCP lists age and capability labels can be ambiguous. Require exact server/version, publisher, read/write capabilities, environment and authentication evidence before Eric may consider an authorized connector. No package or MCP activation here.
- Legal, eligibility, settlement, tax, and jurisdiction claims are out of Jane's decision authority; refer them to Sara with exact contract and dated primary sources.
- If state is uncertain or readback conflicts with the proposed outcome, stop the affected integration path, preserve evidence, and request owner review. Do not retry blindly, synthesize “missing” orders, or adjust the portfolio automatically.

## Primary choice

Use `agiprolabs/claude-trading-skills/skills/polymarket-api/SKILL.md` as the primary *reference spine* because it makes the distinctions among market metadata, CLOB orders, data objects, outcome-token identity, signing, settlement and dispute handling explicit. It is not a current implementation spec and is not qualified. The complementary sources supply separate venue-specific branches; they do not replace the spine or create an alternative execution stack. The source code/release/license status is recorded in `source-provenance.json`.
