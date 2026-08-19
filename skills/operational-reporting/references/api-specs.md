# Operational reporting interface

`mode` selects digest, flash, numbered-plan, or periodic-report. `window`
contains the deadline and previous-report boundary. Each source declares its
kind, owner, freshness, and evidence reference. `delivery` declares the
authorized channels. The output lists sections, redactions, decision items,
and one receipt per accepted channel.
