select
    md5(
        balance.report_month::text || '|' || balance.institution_cnpj || '|' ||
        balance.document_code || '|' || mapping.reporting_line_key || '|' ||
        mapping.mapping_version
    )::text as reporting_line_balance_key,
    bank.bank_key,
    date.month_key,
    reporting_line.reporting_line_key,
    source.source_file_key,
    balance.report_month,
    balance.document_code,
    balance.institution_cnpj,
    mapping.reporting_line_key as reporting_line_code,
    mapping.mapping_version,
    sum(balance.balance_amount)::numeric as reported_balance_amount,
    sum(balance.balance_amount * mapping.presentation_multiplier)::numeric as presentation_balance_amount,
    count(distinct balance.account_code)::integer as contributing_account_count,
    string_agg(distinct balance.account_code, '|' order by balance.account_code)::text as contributing_account_codes,
    bool_and(balance.is_fixture)::boolean as is_fixture
from {{ ref('account_balance') }} as balance
inner join {{ ref('reporting_line_mapping') }} as mapping
    on balance.account_code = mapping.account_code
inner join {{ ref('dim_bank') }} as bank
    on balance.institution_cnpj = bank.institution_cnpj
    and balance.is_fixture = bank.is_fixture
inner join {{ ref('dim_date') }} as date
    on balance.report_month = date.month_start
inner join {{ ref('dim_reporting_line') }} as reporting_line
    on mapping.reporting_line_key = reporting_line.reporting_line_code
inner join {{ ref('dim_source_file') }} as source
    on balance.source_checksum = source.source_checksum
where balance.document_code = '4010'
group by
    balance.report_month,
    balance.institution_cnpj,
    balance.document_code,
    balance.source_checksum,
    mapping.reporting_line_key,
    mapping.mapping_version,
    bank.bank_key,
    date.month_key,
    reporting_line.reporting_line_key,
    source.source_file_key
