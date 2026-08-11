with bank_month as (
    select
        report_month,
        institution_cnpj,
        sum(balance_amount) filter (where account_code = '1000000009') as class_1,
        sum(balance_amount) filter (where account_code = '2000000008') as class_2,
        sum(balance_amount) filter (where account_code = '3000000007') as class_3,
        sum(balance_amount) filter (where account_code = '3999999009') as total_general
    from {{ ref('account_balance') }}
    where is_fixture
    group by report_month, institution_cnpj
)

select *
from bank_month
where class_1 is null
   or class_2 is null
   or class_3 is null
   or total_general is null
   or abs((class_1 + class_2) - (total_general - class_3)) > 0.01
