select
    source_period::varchar(6) as source_period,
    to_date(source_period, 'YYYYMM')::date as report_month,
    source_url::text as source_url,
    source_checksum::text as source_checksum,
    source_generated_at::date as source_generated_at,
    retrieved_at_utc::timestamptz as retrieved_at_utc,
    status::text as status,
    is_active::boolean as source_is_active,
    row_count::bigint as declared_row_count,
    fixture::boolean as is_fixture,
    _dlt_load_id::text as dlt_load_id
from {{ source('raw_cosif', 'cosif_file_manifest') }}
