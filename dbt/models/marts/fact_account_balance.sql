select
    md5(balance.source_checksum || '|' || balance.file_row_number::text)::text as account_balance_key,
    bank.bank_key,
    date.month_key,
    account.account_key,
    source.source_file_key,
    balance.report_month,
    balance.document_code,
    balance.institution_cnpj,
    balance.account_code,
    balance.account_name,
    balance.balance_amount,
    balance.source_checksum,
    balance.file_row_number,
    balance.is_fixture
from {{ ref('account_balance') }} as balance
inner join {{ ref('dim_bank') }} as bank
    on balance.institution_cnpj = bank.institution_cnpj
    and balance.is_fixture = bank.is_fixture
inner join {{ ref('dim_date') }} as date
    on balance.report_month = date.month_start
inner join {{ ref('dim_cosif_account') }} as account
    on balance.account_code = account.account_code
inner join {{ ref('dim_source_file') }} as source
    on balance.source_checksum = source.source_checksum
where balance.document_code = '4010'
