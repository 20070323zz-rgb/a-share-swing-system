# ETF Expansion Staging Validation Report

- Generated on: 2026-06-08
- Input directory: `data/staging/jqdata_expanded/`
- Status: pending JQData staging download.
- Reason: `JQDATA_USER` and `JQDATA_PASSWORD` are not set in the current execution environment.
- Planned candidates: 94
- Validated files: 0
- Failed files: 0
- Formal data writes: 0
- Safety: no broker API, no real orders, no account/password storage, no strategy changes, no writes to `data/etf_daily/`.

Run after staging download:

```bash
python3 scripts/validate_manual_csv.py --all-etf --input-dir data/staging/jqdata_expanded
```
