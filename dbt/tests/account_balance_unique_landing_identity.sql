select source_checksum, file_row_number
from {{ ref('account_balance') }}
group by source_checksum, file_row_number
having count(*) <> 1
