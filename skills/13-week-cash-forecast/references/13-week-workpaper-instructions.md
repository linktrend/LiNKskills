# Blank 13-week cash workpaper

This locally authored scaffold implements method card C. It contains no company data, assumed liquidity policy or forecast. The copied monthly publisher examples remain unchanged.

Record entity, currency, forecast vintage and availability basis before filling `13-week-workpaper.csv`. Each week needs a dated start/end, opening available cash, supported receipts and supported disbursements. Retain evidence references and distinguish committed cash from assumptions. Restricted cash is outside available cash unless its availability is evidenced.

For each fully supported row: net cash = receipts minus disbursements; ending cash = opening cash plus net cash. Next week's opening equals the preceding ending cash. Blank or unavailable components make the affected result unknown, not zero. A recorded zero needs an evidence basis.

Create a separate filled table for each requested scenario and identify changed source lines and timing assumptions. Identify the lowest supported ending balance, largest outflow week and first supported negative week within this horizon. Do not extrapolate a zero-cash date beyond week 13 without a separately stated method and assumptions. Preserve prior-vintage evidence when rolling forward.
