with source as (
    select * from {{ source('raw', 'pageviews') }}
),

articles as (
    select * from {{ ref('articles') }}
)

select
    cast(s.view_date as date)  as view_date,
    s.project,
    a.language,
    a.brand,
    a.article_type,
    s.article,
    s.access,
    cast(s.views as integer)   as views
from source s
left join articles a
    on s.project = a.project
   and s.article = a.article