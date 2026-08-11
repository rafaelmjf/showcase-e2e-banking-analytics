with sequenced as (
    select
        series_code,
        report_month,
        lag(report_month) over (
            partition by series_code order by report_month
        ) as previous_month
    from {{ ref('macro_observation') }}
)

select *
from sequenced
where previous_month is not null
  and report_month <> (previous_month + interval '1 month')::date
