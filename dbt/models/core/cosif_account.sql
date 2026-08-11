with ranked as (
    select
        account_code,
        account_name,
        taxonomy,
        report_month,
        is_fixture,
        row_number() over (
            partition by account_code
            order by report_month desc, account_name desc
        ) as recency_rank
    from {{ ref('account_balance') }}
)

select
    account_code,
    account_name,
    taxonomy,
    is_fixture
from ranked
where recency_rank = 1
