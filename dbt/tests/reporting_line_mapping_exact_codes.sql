with expected(reporting_line_key, account_code) as (
    values
        ('total_assets', '1000000009'),
        ('total_assets', '2000000008'),
        ('credit_portfolio', '1600000007'),
        ('credit_portfolio', '1700000000'),
        ('credit_portfolio', '1810000000'),
        ('deposits', '4100000009'),
        ('equity', '6000000004')
),

actual as (
    select reporting_line_key, account_code
    from {{ ref('reporting_line_mapping') }}
),

differences as (
    (select * from expected except select * from actual)
    union all
    (select * from actual except select * from expected)
)

select * from differences
