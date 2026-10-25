select project, article, access, view_date, count(*) as n
from {{ ref('stg_pageviews') }}
group by all
having count(*) > 1