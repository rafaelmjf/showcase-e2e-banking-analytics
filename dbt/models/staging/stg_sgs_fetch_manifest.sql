select
    series_code::text as series_code,
    requested_start_date::date as requested_start_date,
    requested_end_date::date as requested_end_date,
    retrieved_at_utc::timestamptz as retrieved_at_utc,
    status::text as status,
    response_count::bigint as response_count,
    fixture::boolean as is_fixture,
    _dlt_load_id::text as dlt_load_id
from {{ source('raw_macro', 'sgs_fetch_manifest') }}
