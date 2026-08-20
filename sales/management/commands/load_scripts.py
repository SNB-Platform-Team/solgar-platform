"""Management command to load DadQuery SQL scripts into the database."""

from django.core.management.base import BaseCommand

from sales.models import DadQuery


SCRIPTS = {
    "PAR_REP_PHARMDATA_CATEGORY_GET": r"""select PARAMFROM x.A,x.A_PLUS,x.B,x.B_PLUS,x.C,x.C_PLUS,x.EMPTY,x.Total,
round(((x.A+x.A_PLUS)/x.Total)*100) as '%A', round(((x.B+x.B_PLUS)/x.Total)*100) as '%B',
round(((x.C+x.C_PLUS)/x.Total)*100) as '%C'
from 
(select PARAMFROM sum(case when pharmacy_category = 'A' THEN 1 else 0 END) as A,
sum(case when pharmacy_category = 'A+' THEN 1 else 0 END) as A_PLUS,
sum(case when pharmacy_category = 'B' THEN 1 else 0 END) as B,
sum(case when pharmacy_category = 'B+' THEN 1 else 0 END) as B_PLUS,
sum(case when pharmacy_category = 'C' THEN 1 else 0 END) as C,
sum(case when pharmacy_category = 'C+' THEN 1 else 0 END) as C_PLUS,
sum(case when (pharmacy_category is null or length (pharmacy_category)=0) THEN 1 else 0 END) as EMPTY,
count(0) as Total from solgar_tst.pharmacy_data_BRANDTYPE where status = 1 PRMDATE PARAMWHERE group by 1,PARAMGROUP 
union all 
select PARAMUNION sum(case when pharmacy_category = 'A' THEN 1 else 0 END) as A,
sum(case when pharmacy_category = 'A+' THEN 1 else 0 END) as A_PLUS,
sum(case when pharmacy_category = 'B' THEN 1 else 0 END) as B,
sum(case when pharmacy_category = 'B+' THEN 1 else 0 END) as B_PLUS,
sum(case when pharmacy_category = 'C' THEN 1 else 0 END) as C,
sum(case when pharmacy_category = 'C+' THEN 1 else 0 END) as C_PLUS,
sum(case when (pharmacy_category is null or length (pharmacy_category)=0) THEN 1 else 0 END) as EMPTY,
count(0) as Total from solgar_tst.pharmacy_data_BRANDTYPE where status = 1 PRMDATE PRMWHEREUNION) x 
order by x.total desc""",
    "PAR_REP_PHARMDATA_QUANTITY_GET": r"""select * from (select PARAMFROM count(0) as Total from solgar_tst.pharmacy_data_BRANDTYPE where status =1  PRMDATE PARAMWHERE group by 1,PARAMGROUP union all select PARAMUNION count(0) as Total from solgar_tst.pharmacy_data_BRANDTYPE where status = 1 PRMDATE PRMWHEREUNION) x order by x.total desc""",
    "PAR_REP_PHARMDATA_ACTIVENESS_GET": r"""select * from (select PARAMFROM sum(case when pharmacy_activeness = 'Актив' THEN 1 else 0 END) as Active,sum(case when pharmacy_activeness = 'В процессе' THEN 1 else 0 END) as InProcess,sum(case when pharmacy_activeness = 'Не Актив' THEN 1 else 0 END) as NotActive,count(0) as Total from solgar_tst.pharmacy_data_BRANDTYPE where status = 1 PRMDATE PARAMWHERE group by 1,PARAMGROUP union all select PARAMUNION sum(case when pharmacy_activeness = 'Актив' THEN 1 else 0 END) as Active,sum(case when pharmacy_activeness = 'В процессе' THEN 1 else 0 END) as InProcess,sum(case when pharmacy_activeness = 'Не Актив' THEN 1 else 0 END) as NotActive,count(0) as Total from solgar_tst.pharmacy_data_BRANDTYPE where status = 1 PRMDATE PRMWHEREUNION) x order by x.total desc""",
    "PAR_REP_DOCTORDATA_CATEGORY_GET": r"""select PARAMFROM A_PLUS as 'A+',A,B,C,Total, 
 round(((x.A_PLUS)/x.Total)*100) as '%A+',round(((x.A)/x.Total)*100) as '%A',
 round(((x.B)/x.Total)*100) as '%B',round(((x.C)/x.Total)*100) as '%C'
 from (
 select PARAMFROM 
 sum(case when category = 'A+' THEN 1 else 0 END) as A_PLUS, 
 sum(case when category = 'A' THEN 1 else 0 END) as A,
 sum(case when category = 'B' THEN 1 else 0 END) as B,
 sum(case when category = 'C' THEN 1 else 0 END) as C,
  count(0) as Total from 
  solgar_tst.doctor_data where status = 1 PRMDATE PARAMWHERE 
  group by 1, PARAMGROUP 
  union all 
  select PARAMUNION 
  sum(case when category = 'A+' THEN 1 else 0 END) as A_PLUS, 
 sum(case when category = 'A' THEN 1 else 0 END) as A,
 sum(case when category = 'B' THEN 1 else 0 END) as B,
 sum(case when category = 'C' THEN 1 else 0 END) as C,
  count(0) as Total 
  from solgar_tst.doctor_data 
  where status = 1 PRMDATE PRMWHEREUNION) x order by x.total desc""",
    "PAR_REP_DOCTORDATA_QUANTITY_GET": r"""select * from (select PARAMFROM count(0) as Total from solgar_tst.doctor_data where status = 1 PRMDATE PARAMWHERE group by 1,PARAMGROUP union all select PARAMUNION  count(0) as Total from solgar_tst.doctor_data where status = 1 PRMDATE PRMWHEREUNION) x order by x.total desc""",
    "PAR_REP_PHARMDATA_CATEGORY_GET_REGIONS": r"""select PARAMFROM x.A,x.A_PLUS,x.B,x.B_PLUS,x.C,x.C_PLUS,x.EMPTY,x.Total,
round(((x.A+x.A_PLUS)/x.Total)*100) as '%A', round(((x.B+x.B_PLUS)/x.Total)*100) as '%B',
round(((x.C+x.C_PLUS)/x.Total)*100) as '%C' from (
select PARAMFROM sum(case when pharmacy_category = 'A' THEN 1 else 0 END) as A,
sum(case when pharmacy_category = 'A+' THEN 1 else 0 END) as A_PLUS,
sum(case when pharmacy_category = 'B' THEN 1 else 0 END) as B,
sum(case when pharmacy_category = 'B+' THEN 1 else 0 END) as B_PLUS,
sum(case when pharmacy_category = 'C' THEN 1 else 0 END) as C,
sum(case when pharmacy_category = 'C+' THEN 1 else 0 END) as C_PLUS,
sum(case when (pharmacy_category is null or length (pharmacy_category)=0) THEN 1 else 0 END) as EMPTY,
count(0) as Total 
from solgar_tst.pharmacy_data_BRANDTYPE 
where status = 1 and area ='Region' PRMDATE PARAMWHERE group by 1,PARAMGROUP 
union all
select PARAMFROM1 sum(case when pharmacy_category = 'A' THEN 1 else 0 END) as A,
sum(case when pharmacy_category = 'A+' THEN 1 else 0 END) as A_PLUS,
sum(case when pharmacy_category = 'B' THEN 1 else 0 END) as B,
sum(case when pharmacy_category = 'B+' THEN 1 else 0 END) as B_PLUS,
sum(case when pharmacy_category = 'C' THEN 1 else 0 END) as C,
sum(case when pharmacy_category = 'C+' THEN 1 else 0 END) as C_PLUS,
sum(case when (pharmacy_category is null or length (pharmacy_category)=0) THEN 1 else 0 END) as EMPTY,
count(0) as Total 
from solgar_tst.pharmacy_data_BRANDTYPE 
where status = 1 and area in('Moscow','Saint Petersburg') PRMDATE PARAMWHERE group by 1,PARAMGROUP1 
union all 
select PARAMUNION sum(case when pharmacy_category = 'A' THEN 1 else 0 END) as A,
sum(case when pharmacy_category = 'A+' THEN 1 else 0 END) as A_PLUS,
sum(case when pharmacy_category = 'B' THEN 1 else 0 END) as B,
sum(case when pharmacy_category = 'B+' THEN 1 else 0 END) as B_PLUS,
sum(case when pharmacy_category = 'C' THEN 1 else 0 END) as C,
sum(case when pharmacy_category = 'C+' THEN 1 else 0 END) as C_PLUS,
sum(case when (pharmacy_category is null or length (pharmacy_category)=0) THEN 1 else 0 END) as EMPTY,count(0) as Total 
from solgar_tst.pharmacy_data_BRANDTYPE where status = 1 PRMDATE PRMWHEREUNION) 
x order by x.total desc""",
    "PAR_REP_PHARMDATA_QUANTITY_GET_REGIONS": r"""select * from (
select PARAMFROM count(0) as Total 
from solgar_tst.pharmacy_data_BRANDTYPE 
where status =1 and area ='Region' PRMDATE PARAMWHERE group by 1,PARAMGROUP 
union all
select PARAMFROM1 count(0) as Total 
from solgar_tst.pharmacy_data_BRANDTYPE 
where status =1 and area in('Moscow','Saint Petersburg') PRMDATE PARAMWHERE group by 1,PARAMGROUP1
union all 
select PARAMUNION count(0) as Total from solgar_tst.pharmacy_data_BRANDTYPE 
where status = 1 PRMDATE PRMWHEREUNION) x order by x.total desc""",
    "PAR_REP_PHARMDATA_ACTIVENESS_GET_REGIONS": r"""select * from (
select PARAMFROM sum(case when pharmacy_activeness = 'Актив' THEN 1 else 0 END) as Active,
sum(case when pharmacy_activeness = 'В процессе' THEN 1 else 0 END) as InProcess,
sum(case when pharmacy_activeness = 'Не Актив' THEN 1 else 0 END) as NotActive,
count(0) as Total from solgar_tst.pharmacy_data_BRANDTYPE 
where status = 1 and area ='Region' PRMDATE PARAMWHERE group by 1,PARAMGROUP 
union all
select PARAMFROM1 sum(case when pharmacy_activeness = 'Актив' THEN 1 else 0 END) as Active,
sum(case when pharmacy_activeness = 'В процессе' THEN 1 else 0 END) as InProcess,
sum(case when pharmacy_activeness = 'Не Актив' THEN 1 else 0 END) as NotActive,
count(0) as Total from solgar_tst.pharmacy_data_BRANDTYPE 
where status = 1 and area in('Moscow','Saint Petersburg') PRMDATE PARAMWHERE group by 1,PARAMGROUP1
union all 
select PARAMUNION sum(case when pharmacy_activeness = 'Актив' THEN 1 else 0 END) as Active,
sum(case when pharmacy_activeness = 'В процессе' THEN 1 else 0 END) as InProcess,
sum(case when pharmacy_activeness = 'Не Актив' THEN 1 else 0 END) as NotActive,
count(0) as Total from solgar_tst.pharmacy_data_BRANDTYPE 
where status = 1 PRMDATE PRMWHEREUNION) x order by x.total desc""",
    "PAR_REP_DOCTORDATA_CATEGORY_GET_REGION": r"""select PARAMFROM A_PLUS as 'A+', A,B,C,Total, 
round(((x.A_PLUS)/x.Total)*100) as '%A+',round(((x.A)/x.Total)*100) as '%A',
round(((x.B)/x.Total)*100) as '%B',round(((x.C)/x.Total)*100) as '%C'
 from (
 select PARAMFROM 
 sum(case when category = 'A+' THEN 1 else 0 END) as A_PLUS,
 sum(case when category = 'A' THEN 1 else 0 END) as A,
 sum(case when category = 'B' THEN 1 else 0 END) as B,
 sum(case when category = 'C' THEN 1 else 0 END) as C,
 count(0) as Total from solgar_tst.doctor_data 
 where status = 1 and area ='Region' PRMDATE PARAMWHERE group by 1,PARAMGROUP 
 union all 
 select PARAMFROM1
 sum(case when category = 'A+' THEN 1 else 0 END) as A_PLUS,
 sum(case when category = 'A' THEN 1 else 0 END) as A,
 sum(case when category = 'B' THEN 1 else 0 END) as B,
 sum(case when category = 'C' THEN 1 else 0 END) as C,
 count(0) as Total from solgar_tst.doctor_data 
 where status = 1 and area in('Moscow','Saint Petersburg') PRMDATE PARAMWHERE group by 1,PARAMGROUP1 
 union all 
 select PARAMUNION 
 sum(case when category = 'A+' THEN 1 else 0 END) as A_PLUS,
 sum(case when category = 'A' THEN 1 else 0 END) as A,
 sum(case when category = 'B' THEN 1 else 0 END) as B,
 sum(case when category = 'C' THEN 1 else 0 END) as C,
 count(0) as Total from solgar_tst.doctor_data 
 where status = 1 PRMDATE PRMWHEREUNION) x order by x.total desc""",
    "PAR_REP_DOCTORDATA_QUANTITY_GET_REGION": r"""select * from (
select PARAMFROM count(0) as Total from solgar_tst.doctor_data 
where status = 1 and area ='Region' PRMDATE PARAMWHERE group by 1,PARAMGROUP 
union all 
select PARAMFROM1 count(0) as Total from solgar_tst.doctor_data 
where status = 1 and area in('Moscow','Saint Petersburg') PRMDATE PARAMWHERE group by 1,PARAMGROUP1 
union all
select PARAMUNION  count(0) as Total from solgar_tst.doctor_data 
where status = 1 PRMDATE PRMWHEREUNION) x order by x.total desc""",
    "CHAIN_SALES_WHRE_CONDITION_SL": r"""FROM
 solgar_tst.sales_pharmacy a
 LEFT JOIN
 solgar_tst.sales_address_group b
 LEFT JOIN
 solgar_tst.solgar_address_group e ON b.administrative_area_name = e.administrative_area_name
 AND b.sub_administrative_area_name = e.sub_administrative_area_name ON a.reader_id = b.id
 LEFT JOIN
 solgar_tst.sales_product_group f ON a.product_id = f.id
 LEFT JOIN
 solgar_tst.pharmacy_data_solgar d ON d.status = 1
 AND a.pharm_id = d.pharmacy_id 
 where a.product_type = 'SL'""",
    "CHAIN_SALES_WHRE_CONDITION_BN": r"""FROM
 solgar_tst.sales_pharmacy a 
 LEFT JOIN
 solgar_tst.sales_address_group b
 LEFT JOIN
 solgar_tst.solgar_address_group e ON b.administrative_area_name = e.administrative_area_name
 AND b.sub_administrative_area_name = e.sub_administrative_area_name ON a.reader_id = b.id
 LEFT JOIN
 solgar_tst.sales_product_group f ON a.product_id = f.id
 LEFT JOIN
 solgar_tst.pharmacy_data_bounty d ON d.status = 1
 AND a.pharm_id = d.pharmacy_id
 where a.product_type = 'BN'""",
    "CHAIN_SALES_WHRE_CONDITION_SL_CAT": r"""FROM
 solgar_tst.sales_pharmacy a use index (ind_date_prd)
 LEFT JOIN
 solgar_tst.sales_address_group b
 LEFT JOIN
 solgar_tst.solgar_address_group e ON b.administrative_area_name = e.administrative_area_name
 AND b.sub_administrative_area_name = e.sub_administrative_area_name ON a.reader_id = b.id
 LEFT JOIN
 solgar_tst.pharmacy_data_solgar d ON d.status = 1 AND a.pharm_id = d.pharmacy_id
 LEFT JOIN
 solgar_tst.sales_product_group f 
 LEFT JOIN
 solgar_org.products g
 LEFT JOIN
 solgar_org.product_category h ON h.product_id = g.product_table_id ON g.product_table_id = f.product_official_id ON a.product_id = f.id 
 where a.product_type = 'SL'""",
    "CHAIN_SALES_WHRE_CONDITION_BN_CAT": r"""FROM
 solgar_tst.sales_pharmacy a use index (ind_date_prd)
 LEFT JOIN
 solgar_tst.sales_address_group b
 LEFT JOIN
 solgar_tst.solgar_address_group e ON b.administrative_area_name = e.administrative_area_name
 AND b.sub_administrative_area_name = e.sub_administrative_area_name ON a.reader_id = b.id
 LEFT JOIN
 solgar_tst.pharmacy_data_bounty d ON d.status = 1 AND a.pharm_id = d.pharmacy_id
 LEFT JOIN
 solgar_tst.sales_product_group f 
 LEFT JOIN
 solgar_org.products g
 LEFT JOIN
 solgar_org.product_category h ON h.product_id = g.product_table_id ON g.product_table_id = f.product_official_id ON a.product_id = f.id
 where a.product_type = 'BN'""",
    "CHAIN_SALES_WHRE_CONDITION_OS_CAT": r"""FROM
 solgar_tst.sales_pharmacy a use index (ind_date_prd)
 LEFT JOIN
 solgar_tst.sales_address_group b
 LEFT JOIN
 solgar_tst.solgar_address_group e ON b.administrative_area_name = e.administrative_area_name
 AND b.sub_administrative_area_name = e.sub_administrative_area_name ON a.reader_id = b.id
 LEFT JOIN
 solgar_tst.pharmacy_data_bounty d ON d.status = 1 AND a.pharm_id = d.pharmacy_id
 LEFT JOIN
 solgar_tst.sales_product_group f 
 LEFT JOIN
 solgar_org.products g
 LEFT JOIN
 solgar_org.product_category h ON h.product_id = g.product_table_id ON g.product_table_id = f.product_official_id ON a.product_id = f.id
 where a.product_type = 'OS'""",
    "CHAIN_SALES_WHRE_CONDITION_OS": r"""FROM
  solgar_tst.sales_pharmacy a
  LEFT JOIN
  solgar_tst.sales_address_group b
  LEFT JOIN
  solgar_tst.solgar_address_group e ON b.administrative_area_name = e.administrative_area_name
  AND b.sub_administrative_area_name = e.sub_administrative_area_name ON a.reader_id = b.id
  LEFT JOIN
  solgar_tst.sales_product_group f ON a.product_id = f.id
  LEFT JOIN
  solgar_tst.pharmacy_data_bounty d ON d.status = 1
  AND a.pharm_id = d.pharmacy_id
  where a.product_type = 'OS'""",
}


class Command(BaseCommand):
    """Load or update the report SQL script fragments in DadQuery."""

    help = "Load DadQuery SQL script fragments (Sales Report + Pharmacy/Doctor Managerial)."

    def handle(self, *args, **options):
        """Insert or update each named script."""
        created_count = 0
        updated_count = 0
        for name, script in SCRIPTS.items():
            obj, created = DadQuery.objects.update_or_create(
                query_name=name,
                defaults={"query_script": script, "is_active": True},
            )
            if created:
                created_count += 1
                self.stdout.write(f"CREATED {name}")
            else:
                updated_count += 1
                self.stdout.write(f"UPDATED {name}")
        total = DadQuery.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f"Done. Created {created_count}, updated {updated_count}. Total: {total}"))
