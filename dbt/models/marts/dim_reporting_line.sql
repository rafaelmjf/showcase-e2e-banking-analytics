select distinct
    md5(reporting_line_key)::text as reporting_line_key,
    reporting_line_key::text as reporting_line_code,
    reporting_line_name,
    display_order,
    1::integer as presentation_multiplier,
    mapping_version,
    status
from {{ ref('reporting_line_mapping') }}
