with expected(series_code) as (
    values ('4189'), ('433'), ('24363'), ('20539'), ('21082')
),
actual as (
    select series_code from {{ ref('macro_series') }}
)

select 'missing' as issue, expected.series_code
from expected
left join actual using (series_code)
where actual.series_code is null

union all

select 'unexpected' as issue, actual.series_code
from actual
left join expected using (series_code)
where expected.series_code is null
