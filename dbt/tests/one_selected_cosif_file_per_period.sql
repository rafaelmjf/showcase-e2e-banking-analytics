select source_period
from {{ ref('cosif_file_manifest') }}
group by source_period
having count(*) filter (where is_selected) <> 1
