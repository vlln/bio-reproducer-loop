# Reproduction Plan: Data Integrity Recovery

Status: COMPLETE

Inspect local `data/counts.csv` before analysis. The paper claims a comma-separated
15-gene by 8-sample matrix, but the supplied file may have a delimiter mismatch,
truncation or missing rows. Report observed format and dimensions, preserve recoverable
data, and mark unavailable rows as unrecoverable rather than fabricating them.
