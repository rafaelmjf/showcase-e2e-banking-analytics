with metrics as (
    select
        (select count(*) from {{ ref('dim_bank') }} where not is_fixture) as bank_count,
        (
            select count(distinct report_month)
            from {{ ref('fact_reporting_line_balance') }}
            where not is_fixture
        ) as month_count,
        (
            select count(*)
            from {{ ref('fact_reporting_line_balance') }}
            where not is_fixture
        ) as reporting_line_rows,
        (
            select count(distinct reporting_line_code)
            from {{ ref('fact_reporting_line_balance') }}
            where not is_fixture
        ) as reporting_line_count
)

select *
from metrics
where bank_count > 0
  and not (
      bank_count = 15
      and month_count = 15
      and reporting_line_rows = 900
      and reporting_line_count = 4
  )
