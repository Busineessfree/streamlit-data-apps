# Patent Trends: aggregates by technology class, office, year and organisation (2006-2026)

Aggregate tables built by **Fliar BI** from worldwide patent publications in the **Google Patents Public Datasets**
(publications of the patent offices, 2006 to April 2026). They power the [Patent Trends Explorer](https://huggingface.co/spaces/fliarbi/patent-trends-explorer) Space.
**Aggregates only**: no inventor names and no individual (person) assignees; only organisations are listed.

## Key facts (computed from these tables)
- **90,925,801 publications** in 2006-2025 in the answering shards (6 of 7, see Coverage); yearly volume went from 2,420,022 in 2006 to 6,217,964 in 2025.
- **China's office published 61% of all 2025 publications** in this corpus.
- Most active organisations 2021-2025: SAMSUNG ELECTRONICS CO LTD (175,272), HUAWEI TECH CO LTD (156,866), QUALCOMM INC (96,071), LG ELECTRONICS INC (73,682), CANON KK (64,798).
- Fastest-growing CPC classes 2020→2025 (min. 2,000 publications in 2020):

| CPC class | Title | 2020 | 2025 | CAGR |
|---|---|---|---|---|
| H10B | Electronic memory devices | 2,661 | 10,228 | 30.9% |
| Y02P | Climate change mitigation technologies in the production or processing… | 21,809 | 79,076 | 29.4% |
| C25B | Electrolytic or electrophoretic processes for the production of… | 2,876 | 9,489 | 27.0% |
| Y02W | Climate change mitigation technologies related to wastewater treatment… | 10,870 | 33,537 | 25.3% |
| Y02A | Technologies for adaptation to climate change | 21,098 | 50,108 | 18.9% |

## Tables
| Table | Rows |
|---|---|
| `by_class_year_office.parquet` | 173,075 |
| `by_year_office.parquet` | 1,689 |
| `class_summary.parquet` | 677 |
| `cpc_classes.parquet` | 681 |
| `top_assignees_by_class_year.parquet` | 201,024 |
| `top_assignees_by_year.parquet` | 22,667 |

- `by_year_office`: publication_year x publishing office (`country_code`, `office_name`): publications, granted (grant documents), sum_citations (backward citations listed), with_cpc.
- `by_class_year_office`: CPC class (first 4 characters of the first CPC code) x year x office (14 largest offices + `Other`).
- `class_summary`: one row per CPC class: title, section, publications 2006-2025, `grant_share` (= granted publications / publications), `avg_citations` (backward citations per publication), publications in 2015/2020/2024/2025, CAGR 2015-2025 and 2020-2025, share of 2025 publications, share change 2020-2025 in percentage points, China's share of the class in 2025.
- `cpc_classes`: CPC class titles from the official CPC scheme (version 2026.08), shortened (references in brackets removed).
- `top_assignees_by_year`: organisations that reach the top 500 by publications in any year, with yearly publications, granted and citations, and the organisation's most frequent assignee country.
- `top_assignees_by_class_year`: per CPC class, the top 25 organisations in 2006-2025 and in 2021-2025, by year.

## Method
- A **publication** is one published document (an application and its later grant are two publications); counts are not patent families.
- `granted` counts grant documents (kind codes B/C/U/S etc. as flagged in the source). `grant_share` is a publication-level mix measure, not an approval rate.
- `sum_citations` sums the references each publication cites (backward citations), so `avg_citations` = references per publication.
- CPC class = first four characters of the first-listed CPC code; publications without a CPC code (mostly designs and some offices) are excluded from class tables but counted in `by_year_office`.
- A publication with several assignees counts once for each organisation. Assignee names are the harmonised names in the source (upper case, abbreviated).
- **Individuals removed**: names without an organisation signal (legal form such as CO/LTD/INC/GMBH/KK, or words such as UNIV, INST, TECH, ELECTRIC) and with more than one word are treated as persons and dropped (75,972 names); this is conservative and also drops a few small organisations.

## Coverage
- Database shards answering at build time: 6 of 7 (missing: 2 (192.168.50.6)); 92,593,512 of 108,034,545 publications (85.7%). Rows were spread round-robin across shards, so shares, rates and averages are unbiased, while **absolute counts are about 86% of the true totals**.
- CPC codes are the current classification of each publication, so a class created recently (for example H10B, H10K and H10N in 2023) includes older publications re-classified into it; growth rates of such classes also reflect the shift from the codes they replaced.
- Some offices are incomplete in the public source for 2025 (fewer than a quarter of their 2022-2024 average): BR, PH, RO, RU, UY. Treat their 2025 drop as a source gap, not a real decline.
- Full years 2006-2025; **2026 is partial** (publications up to 2026-04-21). Patents publish about 18 months after filing, so publication years lag invention years.

## Licence and attribution
CC BY-NC 4.0, attribution "Fliar BI" ([fliarbi.com](https://fliarbi.com)). Source data: Google Patents Public Datasets (CC BY 4.0), built from the publications of the national and regional patent offices; CPC titles from the Cooperative Patent Classification scheme (EPO/USPTO).
More datasets: [fliarbi.com/datasets](https://fliarbi.com/datasets/) · [GitHub index](https://github.com/Busineessfree/open-company-datasets) · contact **b2b@fliarbi.com**.
