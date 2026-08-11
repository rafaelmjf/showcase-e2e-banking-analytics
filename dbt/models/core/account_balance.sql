select
    balance.source_period,
    balance.report_month,
    balance.document_code,
    balance.institution_cnpj,
    balance.agency_code,
    balance.institution_name,
    balance.conglomerate_code,
    balance.conglomerate_name,
    balance.taxonomy,
    balance.account_code,
    balance.account_name,
    balance.balance_raw,
    balance.balance_amount,
    balance.source_url,
    balance.source_checksum,
    balance.source_generated_at,
    balance.retrieved_at_utc,
    balance.file_row_number,
    balance.is_fixture,
    balance.dlt_load_id
from {{ ref('stg_cosif_balance_row') }} as balance
inner join {{ ref('cosif_file_manifest') }} as manifest
    on balance.source_checksum = manifest.source_checksum
    and manifest.is_selected
