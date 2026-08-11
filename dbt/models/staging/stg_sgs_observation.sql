select
    series_code::text as series_code,
    source_observation_date::date as source_observation_date,
    to_date(report_month, 'YYYYMM')::date as report_month,
    value_raw::text as value_raw,
    value::numeric(38, 10) as value,
    retrieved_at_utc::timestamptz as retrieved_at_utc,
    source_url::text as source_url,
    fixture::boolean as is_fixture,
    _dlt_load_id::text as dlt_load_id
from {{ source('raw_macro', 'sgs_observation') }}
