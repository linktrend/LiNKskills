# Proposed adversarial cases

These fixtures are proposed and not run.

- **join-fanout:** Input: Two records per ticker are joined to one bar; counts rise 10 to 20. Expected: Flag one-to-many expansion and block aggregate claim.
- **late-amendment:** Input: An amendment published after historical decision revises period-end data. Expected: Keep original historical known-at and mark amended value unavailable then.
- **unknown-delisting:** Input: Delisted name lacks terminal proceeds. Expected: Retain membership and mark payoff unknown; never silently set zero.
