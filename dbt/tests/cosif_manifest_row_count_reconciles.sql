select
    manifest.source_checksum,
    manifest.declared_row_count,
    count(balance.*) as actual_row_count
from {{ ref('cosif_file_manifest') }} as manifest
left join {{ ref('account_balance') }} as balance
    on manifest.source_checksum = balance.source_checksum
where manifest.is_selected
group by manifest.source_checksum, manifest.declared_row_count
having count(balance.*) <> manifest.declared_row_count
