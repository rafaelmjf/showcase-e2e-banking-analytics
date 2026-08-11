select
    md5(account.account_code)::text as account_key,
    account.account_code,
    account.account_name,
    account.taxonomy,
    substring(account.account_code from 1 for 1)::text as account_class,
    substring(account.account_code from 1 for 2)::text as account_group,
    (mapping.account_code is not null)::boolean as is_reporting_line_component,
    account.is_fixture
from {{ ref('cosif_account') }} as account
left join {{ ref('reporting_line_mapping') }} as mapping
    on account.account_code = mapping.account_code
