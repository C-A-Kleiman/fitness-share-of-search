with weekly as (
    select
        date_trunc('week', view_date) as week_start,
        language,
        brand,
        sum(views) as views
    from {{ ref('fct_daily_brand_views') }}
    where article_type = 'brand'
    group by all
)

select
    *,
    views / sum(views) over (partition by week_start, language) as share_of_search
from weekly