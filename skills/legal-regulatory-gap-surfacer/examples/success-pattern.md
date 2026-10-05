# Synthetic success pattern

Input: a scoped policy diff and register snapshot with one duplicate and one unverified candidate.

Expected: propose only supported new/updated rows, preserve source and scope limitations, flag the unverified candidate, and return a draft notice without sending it.
