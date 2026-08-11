with expected as (
    select
        balance.report_month,
        balance.institution_cnpj,
        balance.document_code,
        mapping.reporting_line_key as reporting_line_code,
        mapping.mapping_version,
        sum(balance.balance_amount * mapping.presentation_multiplier)::numeric as amount
    from {{ ref('account_balance') }} as balance
    inner join {{ ref('reporting_line_mapping') }} as mapping
        on balance.account_code = mapping.account_code
    inner join {{ ref('dim_bank') }} as bank
        on balance.institution_cnpj = bank.institution_cnpj
        and balance.is_fixture = bank.is_fixture
    where balance.document_code = '4010'
    group by 1, 2, 3, 4, 5
),

actual as (
    select
        report_month,
        institution_cnpj,
        document_code,
        reporting_line_code,
        mapping_version,
        presentation_balance_amount as amount
    from {{ ref('fact_reporting_line_balance') }}
),

differences as (
    (select * from expected except select * from actual)
    union all
    (select * from actual except select * from expected)
)

select * from differences
