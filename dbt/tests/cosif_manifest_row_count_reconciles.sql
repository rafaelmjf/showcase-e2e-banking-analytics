select
    source_checksum,
    max(declared_row_count) as declared_row_count,
    count(*) as actual_row_count
from {{ ref('account_balance') }}
group by source_checksum
having count(*) <> max(declared_row_count)
