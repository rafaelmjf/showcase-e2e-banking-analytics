select series_code, source_observation_date
from {{ ref('macro_observation') }}
group by series_code, source_observation_date
having count(*) <> 1
