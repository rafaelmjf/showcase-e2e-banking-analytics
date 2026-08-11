# Foundation checkpoint — machine-readable live readiness

Updated: 2026-08-11

## Objective

Replace log interpretation with a stable contract that declares whether bounded
COSIF and SGS evidence is safe to load. The assessment must be read-only, preserve
specific failures and exit nonzero whenever the overall state is blocked.

## Delivered

`banking-data assess-readiness` writes nine CSV controls:

| Scope | Controls |
|---|---|
| COSIF | exact manifest-period coverage; every download complete; one matching profile per checksum; every profile nonempty and structurally valid |
| Macro | exact five-series coverage; every series complete; requested windows match; every series has observations |
| Overall | all eight source controls pass |

Missing files are treated as absent evidence rather than parser crashes. HTTP error
details, duplicate identities, actual counts and requested bounds remain visible in
the CSV. The command writes the assessment before returning exit code 1 for a blocked
state, allowing CI to retain the diagnosis without permitting a load.

## Verification

[Standard CI run 31448608102](https://github.com/rafaelmjf/showcase-e2e-banking-analytics/actions/runs/31448608102)
passed 49 tests, both 117-node dbt builds and the fixture Dagster job.

[Bounded official run 31448688497](https://github.com/rafaelmjf/showcase-e2e-banking-analytics/actions/runs/31448688497)
then exercised the real workflow and produced:

```text
manifest_period_coverage: pass
all_downloads_complete: fail (0/1; HTTP 502)
profile_matches_complete_downloads: fail
all_profiles_valid: fail
exact_series_coverage: pass (5/5 definitions)
all_series_complete: fail (0/5; HTTP 502)
requested_window_matches: pass (5/5)
all_series_have_observations: fail (0/5)
bounded_official_load_ready: blocked
```

The workflow reported `failed_controls=5`, failed its explicit gate, skipped dlt,
dbt and official Dagster, and uploaded the full assessment in artifact `9085517313`.
The compact committed record is
`artifacts/live_readiness_checkpoint_summary.csv`.

## Boundary

This is an executable readiness decision, not source certification. At this retained
run it correctly kept checkpoints 0B, 0C and 0E open. Later local evidence completed
all three checkpoints; the official warehouse certification remains separate.
The `ready` acquisition result remains necessary but not by itself sufficient for
reporting-line approval or official warehouse certification.
