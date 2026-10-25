select week_start, language, sum(share_of_search) as total
from {{ ref('fct_weekly_share_of_search') }}
group by all
having abs(sum(share_of_search) - 1) > 0.0001