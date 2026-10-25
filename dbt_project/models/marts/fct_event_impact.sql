with daily as (
    select * from {{ ref('fct_daily_brand_views') }}
    where language = 'English'
),

category as (
    select view_date, sum(views) as category_views
    from daily
    where article_type = 'category'
    group by all
),

windows as (
    select
        e.event_date, e.brand, e.event,
        avg(case when d.view_date <  e.event_date then d.views end)          as brand_before,
        avg(case when d.view_date >= e.event_date then d.views end)          as brand_after,
        avg(case when d.view_date <  e.event_date then c.category_views end) as category_before,
        avg(case when d.view_date >= e.event_date then c.category_views end) as category_after
    from {{ ref('events') }} e
    join daily d
      on d.brand = e.brand
     and d.view_date between e.event_date - 28 and e.event_date + 27
    join category c on c.view_date = d.view_date
    group by all
)

select
    *,
    brand_after / brand_before - 1                                  as brand_lift,
    category_after / category_before - 1                            as category_lift,
    (brand_after / brand_before) - (category_after / category_before) as lift_vs_category
from windows