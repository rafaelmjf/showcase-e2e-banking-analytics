with coverage as (
    select
        institution_cnpj,
        count(distinct report_month) as months
    from {{ ref('fact_reporting_line_balance') }}
    where not is_fixture
      and reporting_line_code = 'total_assets'
    group by institution_cnpj
)

select *
from coverage
where months <> 15
