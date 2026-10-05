# Fictional worked scenario

See worked-input.json and worked-output.json: two USD100-value positions, ADV100 each, participation0.1, five-day horizon and no price shock. Maximum modelled sale50 each; full spread400bps implies half-spread cost1 each on sale50. Gross100 minus costs2 gives net98, requested cash100 leaves net shortfall2. Full position exit estimate10days. No fill guarantee or policy verdict. The artifacts are illustrative, not observed business evidence or an evaluation pass.

Unknown inputs must remain null with explicit missing_fields; do not treat unknown as zero. Nonlinear/short instruments cannot borrow this linear long-sale estimate. A structural validation accepts only the stated contract shape; it does not prove arithmetic or method behavior.
