# Missing pair-side recovery

If one entity's due-to/due-from extract is unavailable, preserve the available side and its source control total. Mark reciprocal matching as `NEEDS_CONTEXT`, identify the missing entity, account and cutoff, and continue any unaffected mapping check. Do not infer the other entity's amount or claim a tie-out.
