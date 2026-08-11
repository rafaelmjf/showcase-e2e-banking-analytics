select
    series_code,
    theme,
    display_name,
    official_title,
    unit,
    frequency,
    source_start_date,
    observation_semantics,
    monthly_alignment,
    derived_metric,
    max_expected_lag_months,
    revision_policy,
    source_url,
    metadata_url
from {{ ref('stg_sgs_series_metadata') }}
