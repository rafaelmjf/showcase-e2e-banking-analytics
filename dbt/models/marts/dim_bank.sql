with official_members as (
    select
        md5(population.institution_cnpj)::text as bank_key,
        population.institution_cnpj::text as institution_cnpj,
        population.institution_name::text as institution_name,
        population.taxonomy::text as taxonomy,
        to_date(population.freeze_period || '01', 'YYYYMMDD') as freeze_month,
        population.freeze_rank::integer as freeze_rank,
        min(period.report_month)::date as first_report_month,
        max(period.report_month)::date as last_report_month,
        false::boolean as is_fixture
    from {{ ref('top15_population_seed') }} as population
    inner join {{ ref('bank_period') }} as period
        on population.institution_cnpj = period.institution_cnpj
        and not period.is_fixture
    group by
        population.institution_cnpj,
        population.institution_name,
        population.taxonomy,
        population.freeze_period,
        population.freeze_rank
),

fixture_latest_month as (
    select max(report_month) as report_month
    from {{ ref('bank_period') }}
    where is_fixture
),

fixture_totals as (
    select
        balance.institution_cnpj,
        sum(balance.balance_amount) as total_assets
    from {{ ref('account_balance') }} as balance
    cross join fixture_latest_month
    where balance.is_fixture
        and balance.report_month = fixture_latest_month.report_month
        and balance.document_code = '4010'
        and balance.account_code in ('1000000009', '2000000008')
    group by balance.institution_cnpj
),

fixture_ranked as (
    select
        institution_cnpj,
        row_number() over (order by total_assets desc, institution_cnpj)::integer as freeze_rank
    from fixture_totals
),

fixture_members as (
    select
        md5(period.institution_cnpj)::text as bank_key,
        period.institution_cnpj,
        max(period.institution_name)::text as institution_name,
        max(period.taxonomy)::text as taxonomy,
        max(period.report_month)::date as freeze_month,
        ranked.freeze_rank,
        min(period.report_month)::date as first_report_month,
        max(period.report_month)::date as last_report_month,
        true::boolean as is_fixture
    from {{ ref('bank_period') }} as period
    inner join fixture_ranked as ranked
        on period.institution_cnpj = ranked.institution_cnpj
    where period.is_fixture
    group by period.institution_cnpj, ranked.freeze_rank
)

select * from official_members
union all
select * from fixture_members
