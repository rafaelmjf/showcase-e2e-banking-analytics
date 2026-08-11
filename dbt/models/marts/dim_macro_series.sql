select
    md5(series_code)::text as macro_series_key,
    series_code,
    theme,
    display_name,
    official_title,
    unit,
    frequency,
    observation_semantics,
    monthly_alignment,
    derived_metric,
    max_expected_lag_months,
    revision_policy,
    source_url,
    metadata_url
from {{ ref('macro_series') }}
