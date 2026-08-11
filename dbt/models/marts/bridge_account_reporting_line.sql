select
    md5(mapping.account_code || '|' || mapping.reporting_line_key || '|' || mapping.mapping_version)::text as account_reporting_line_key,
    account.account_key,
    reporting_line.reporting_line_key,
    mapping.account_code,
    mapping.reporting_line_key as reporting_line_code,
    mapping.component_name,
    mapping.presentation_multiplier,
    mapping.mapping_version,
    mapping.status,
    mapping.source_url
from {{ ref('reporting_line_mapping') }} as mapping
inner join {{ ref('dim_cosif_account') }} as account
    on mapping.account_code = account.account_code
inner join {{ ref('dim_reporting_line') }} as reporting_line
    on mapping.reporting_line_key = reporting_line.reporting_line_code
