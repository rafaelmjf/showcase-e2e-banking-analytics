select
    md5(observation.series_code || '|' || observation.source_observation_date::text)::text as macro_observation_key,
    series.macro_series_key,
    date.month_key,
    observation.series_code,
    observation.source_observation_date,
    observation.report_month,
    observation.value,
    observation.value_raw,
    observation.retrieved_at_utc,
    observation.source_url,
    observation.is_fixture
from {{ ref('macro_observation') }} as observation
inner join {{ ref('dim_macro_series') }} as series
    on observation.series_code = series.series_code
inner join {{ ref('dim_date') }} as date
    on observation.report_month = date.month_start
