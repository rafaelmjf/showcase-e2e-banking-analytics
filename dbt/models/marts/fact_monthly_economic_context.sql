select
    md5(observation.report_month::text || '|' || observation.series_code)::text as monthly_context_key,
    series.macro_series_key,
    date.month_key,
    observation.report_month,
    observation.series_code,
    series.display_name,
    series.unit,
    series.derived_metric,
    observation.value,
    observation.source_observation_date,
    observation.is_fixture
from {{ ref('macro_observation') }} as observation
inner join {{ ref('dim_macro_series') }} as series
    on observation.series_code = series.series_code
inner join {{ ref('dim_date') }} as date
    on observation.report_month = date.month_start
