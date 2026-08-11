select
    reporting_line_key::text as reporting_line_key,
    reporting_line_name::text as reporting_line_name,
    display_order::integer as display_order,
    account_code::text as account_code,
    component_name::text as component_name,
    presentation_multiplier::integer as presentation_multiplier,
    mapping_version::text as mapping_version,
    status::text as status,
    source_url::text as source_url
from {{ ref('reporting_line_mapping_seed') }}
