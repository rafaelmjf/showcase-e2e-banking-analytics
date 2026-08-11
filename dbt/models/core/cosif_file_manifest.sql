with ranked as (
    select
        *,
        row_number() over (
            partition by source_period
            order by
                (status = 'complete') desc,
                source_is_active desc,
                source_generated_at desc,
                retrieved_at_utc desc,
                source_checksum desc
        ) as version_rank
    from {{ ref('stg_cosif_file_manifest') }}
)

select
    source_period,
    report_month,
    source_url,
    source_checksum,
    source_generated_at,
    retrieved_at_utc,
    status,
    source_is_active,
    (version_rank = 1 and status = 'complete')::boolean as is_selected,
    declared_row_count,
    is_fixture,
    dlt_load_id
from ranked
