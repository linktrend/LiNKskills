# Fictional bounded futures sizing example

This is a synthetic arithmetic example, not a behavioral receipt. Price is measured in `index_point`; cash multiplier is USD 5 per index point per contract; FX is TWD 32 per USD. Round-trip cost is USD 1.50 per contract; gap is an additional 3 index points beyond the stop.

The calculated stressed loss is TWD 2,448 per contract. A TWD 10,000 budget yields 4 whole contracts and TWD 9,792 modeled risk, leaving TWD 208. See `worked-bounded-sizing.json` for the complete task-shaped input and output.
