# Synthetic contract fixtures

These small authored files exercise the acquisition and transformation contracts when
official BCB endpoints are unavailable. They are synthetic test data, not Brazilian
bank observations and not analytical evidence.

- `cosif_balance_rows.csv`: two months, three fictional institutions and four COSIF
  total/control rows per institution.
- `macro_observations.csv`: three months for each of the five accepted SGS codes.

The values deliberately satisfy the provisional accounting identity used by the
fixture tests: class 1 plus class 2 equals total general assets minus class-3 controls.
