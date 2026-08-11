# Source profile

Updated: 2026-08-11

## Status

WP0 is complete and checkpointed. Checkpoint 0A is complete from the official live
catalog: 15 MVP months are published from 202501 through 202603. Checkpoint 0B is now
complete from every active official archive in that range. The committed profile
contains 831,038 parsed rows, zero malformed rows and one stable source schema.
Checkpoint 0C certifies the total-assets mapping and freezes the 202603 top 15.
Checkpoint 0E consolidates the evidence and freezes the official-load boundary.

| Checkpoint | Status | Evidence |
|---|---|---|
| 0A — source availability | Complete | [Checkpoint record](checkpoints/00a-source-availability.md) |
| 0B — schema and volume | Complete; 15/15 official archives and profiles passed | [Checkpoint record](checkpoints/00b-schema-volume.md) and [profile](../artifacts/cosif_source_profile.csv) |
| 0C — total assets and top 15 | Complete; 11/11 controls passed | [Checkpoint record](checkpoints/00c-total-assets-top15.md), [population](../artifacts/top15_population.csv) and [controls](../artifacts/checkpoint_0c_controls.csv) |
| 0D — macro series | Complete for metadata/alignment; full-window live acquisition passed | [Checkpoint record](checkpoints/00d-macro-series.md) and [profile](../artifacts/macro_source_profile.csv) |
| 0E — readiness decision | Complete; 11/11 controls passed | [Checkpoint record](checkpoints/00e-source-profile-decision.md), [controls](../artifacts/checkpoint_0e_controls.csv) and [contract](../artifacts/source_profile_contract.csv) |

The governed monthly scope is document 4010 only. Document 4016 is a semiannual
individual balance sheet and would duplicate June/December positions if admitted to
the same trend. Ordinary total assets are the published top-level balances
`1000000009` (Ativo Realizável) plus `2000000008` (Ativo Permanente); compensation
class 3 is excluded. Where published, total-general less compensation is a reference
check rather than the analytical measure.

The latest complete-period ranking freezes 15 CNPJs from 202603. Rank 15 exceeds rank
16 by BRL 21,929,834,991.30. All 15 members, names and both asset components are
present across all 15 months. All 190 available top-15 reference checks reconcile
within BRL 1.00, with a maximum absolute difference of BRL 0.51. Exact monthly values
are preserved in
[the 225-row population evidence](../artifacts/top15_total_assets_by_month.csv).

This remains a base-individual comparison population, not a consolidated-system
market-share universe. It intentionally retains separate legal entities such as
Itaú Unibanco S.A. and Itaú Unibanco Holding S.A.

The combined 202501–202603 acquisition passed all nine machine-readable source
controls. Checkpoint 0E then passed all 11 consolidation controls and recorded
`ready_for_official_warehouse_certification`. It freezes `BANCOS` base-individual
scope, 4010 analytics, 4010/4016 landing, the 202603 top 15, five macro codes and the
ODbL boundary. It also states `warehouse_status=not_certified` and
`mart_status=not_built`; readiness authorizes the next certification run but does not
pretend it has already occurred. See the [full-window readiness
evidence](../artifacts/live_readiness_full_202501_202603.csv) and [final source
contract](../artifacts/source_profile_contract.csv).

The bounded reporting-line draft certified total assets only at checkpoint 0E. It is
retained as the historical WP0 decision; Phase 1 subsequently resolved credit,
deposits and equity under mapping version `2026-08-11-v1` without rewriting that
source gate.

The follow-on official warehouse certification has now executed this exact contract.
Both initial dlt passes were identity-stable, all 117 core-only dbt nodes passed, the
original 16-asset Dagster job succeeded and the 225 top-15 total-assets values
reconciled with BRL 0.00 maximum difference. See [the warehouse certification
checkpoint](checkpoints/11-official-warehouse-certification.md).

The expanded follow-on build certifies the four reporting lines, twelve mart objects,
`214/214` dbt nodes and a 31-asset Dagster run. All 13 mart controls passed with exact
account and checkpoint 0C reconciliation. See [the reporting-mart
checkpoint](checkpoints/12-reporting-marts.md) and the frozen
[mart contract](../contracts/mart-schema.yml).
