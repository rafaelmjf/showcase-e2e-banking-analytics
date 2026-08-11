select
    observation.series_code,
    observation.source_observation_date,
    observation.report_month,
    observation.value_raw,
    observation.value,
    observation.retrieved_at_utc,
    observation.source_url,
    observation.is_fixture,
    observation.dlt_load_id
from {{ ref('stg_sgs_observation') }} as observation
inner join {{ ref('macro_series') }} as series
    on observation.series_code = series.series_code
