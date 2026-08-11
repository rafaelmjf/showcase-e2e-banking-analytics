select
    series_code::text as series_code,
    theme::text as theme,
    display_name::text as display_name,
    official_title::text as official_title,
    unit::text as unit,
    frequency::text as frequency,
    source_start_date::date as source_start_date,
    observation_semantics::text as observation_semantics,
    monthly_alignment::text as monthly_alignment,
    derived_metric::text as derived_metric,
    max_expected_lag_months::bigint as max_expected_lag_months,
    revision_policy::text as revision_policy,
    source_url::text as source_url,
    metadata_url::text as metadata_url,
    _dlt_load_id::text as dlt_load_id
from {{ source('raw_macro', 'sgs_series_metadata') }}
