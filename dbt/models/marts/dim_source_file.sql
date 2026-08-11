select
    md5(source_checksum)::text as source_file_key,
    source_period,
    report_month,
    source_url,
    source_checksum,
    source_generated_at,
    retrieved_at_utc,
    status,
    source_is_active,
    is_selected,
    declared_row_count,
    is_fixture,
    dlt_load_id
from {{ ref('cosif_file_manifest') }}
where is_selected
