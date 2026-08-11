select
    report_month,
    institution_cnpj,
    document_code,
    account_code,
    source_checksum,
    count(*) as row_count
from {{ ref('fact_account_balance') }}
group by 1, 2, 3, 4, 5
having count(*) > 1
