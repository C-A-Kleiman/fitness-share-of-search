with daily as (
    select view_date, language, brand, article_type, sum(views) as views
    from {{ ref('stg_pageviews') }}
    group by all
)

select
    *,
    avg(views) over (
        partition by language, brand
        order by view_date
        rows between 6 preceding and current row
    ) as views_7d_avg
from daily