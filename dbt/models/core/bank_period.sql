select
    md5(report_month::text || '|' || institution_cnpj)::text as bank_period_key,
    report_month,
    institution_cnpj,
    max(institution_name)::text as institution_name,
    max(taxonomy)::text as taxonomy,
    count(*)::bigint as account_row_count,
    bool_and(is_fixture)::boolean as is_fixture
from {{ ref('account_balance') }}
group by report_month, institution_cnpj
