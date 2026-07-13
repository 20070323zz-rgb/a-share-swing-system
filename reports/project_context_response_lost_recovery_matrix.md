# Project Context Response Lost Recovery Matrix

生成时间：2026-07-07 23:37:14 CST

| Classification | Detection Conditions | Allowed Action | Forbidden Action | Batch State Before Validation | Batch State After Success |
| --- | --- | --- | --- | --- | --- |
| PARTIAL SIDE EFFECT | Some expected outputs exist; some expected outputs are missing; task objective is incomplete | Resume missing work only, then run required validation | Blind full batch rerun | IN_PROGRESS | IN_PROGRESS until enclosing batch completion protocol explicitly completes the batch |
| COMPLETE BUT RESPONSE LOST | Expected outputs complete; validation passed; decision generated; checkpoint persisted; only final response missing | Verify existing outputs and summarize or continue to next checkpoint | Re-execute completed task | IN_PROGRESS or already valid next checkpoint | Preserve existing state; do not duplicate state transition |
| VALIDATION MISSING | Expected outputs basically complete; required validation did not run; validation artifact missing or stale | Run missing validation only and decide from validation result | Mark COMPLETE before validation | IN_PROGRESS | Eligible for checkpoint or batch completion according to protocol |

All three recovery classifications required by the transition protocol are defined.
