with months as (
    select report_month
    from {{ ref('bank_period') }}
    inner join {{ ref('dim_bank') }} using (institution_cnpj)
    union
    select report_month
    from {{ ref('macro_observation') }}
)

select
    to_char(report_month, 'YYYYMM')::integer as month_key,
    report_month::date as month_start,
    extract(year from report_month)::integer as calendar_year,
    extract(quarter from report_month)::integer as calendar_quarter,
    extract(month from report_month)::integer as calendar_month,
    to_char(report_month, 'Mon YYYY')::text as month_label,
    (date_trunc('quarter', report_month))::date as quarter_start,
    (date_trunc('year', report_month))::date as year_start
from months
