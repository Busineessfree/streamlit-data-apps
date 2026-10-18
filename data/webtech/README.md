# Web Technology Trends: technology adoption, Core Web Vitals and structured data (HTTP Archive crawls, May 2025 and May 2026)

Aggregate tables built by **Fliar BI** from the **HTTP Archive / Chrome UX Report (public web crawl data)**: the mobile crawls of 2025-05 and 2026-05
(14,585,243 and 14,547,080 root pages in the answering shards). They power the [Web Technology Explorer](https://huggingface.co/spaces/fliarbi/web-technology-explorer) Space.
Only counts and shares are published; no page-level or site-level rows.

## Key facts (computed from these tables)
- **66.0% of sites run jQuery**, the most common detected technology in 2026-05 (300 technologies kept, 3,564 detected).
- **Core Web Vitals:** 47.5% of sites with Chrome UX Report field data passed all three metrics in 2026-05, up from 43.8% a year earlier.
- Largest gains in share of sites (pp, technologies on ≥2% of sites): Twitter Emoji (Twemoji) (+13.3), Cloudflare Browser Insights (+8.8), Priority Hints (+6.5), Cloudflare (+3.8), HTTP/3 (+3.5).
- Largest losses: jQuery (-4.9), PHP (-2.7), Apache HTTP Server (-2.5), Bootstrap (-2.3), core-js (-1.9).
- Among platforms with ≥50,000 field-data sites, the CWV pass rate ranges from 80.9% (Wix) to 27.3% (Nuxt.js).
- **WebSite** is the most common structured-data type (37.4% of sites), then Organization (28.5%).

## Tables
| Table | Rows |
|---|---|
| `categories.parquet` | 55 |
| `cwv_by_platform.parquet` | 255 |
| `overview_by_rank.parquet` | 10 |
| `stack_size.parquet` | 155 |
| `structured_data_types.parquet` | 200 |
| `technologies_top300.parquet` | 300 |
| `technology_by_rank.parquet` | 2,962 |
| `technology_by_tld.parquet` | 9,144 |
| `tlds.parquet` | 122 |

- `technologies_top300`: the 300 most common technologies in 2026-05: category, share of sites, share a year earlier, change (pp), share among the top 1M sites (CrUX rank), share of **company websites** in Fliar BI's [website technology stack dataset](https://huggingface.co/datasets/fliarbi/website-technology-stack) (2,079,163 company sites, matched by name), and Core Web Vitals pass rates of sites using it.
- `technology_by_rank`: share of each top-300 technology within CrUX popularity buckets (top 10k … beyond 10M), both crawls.
- `technology_by_tld`: share of the 150 most common technologies within each of the 60 largest TLDs.
- `cwv_by_platform`: CMS, e-commerce, blog and site-builder platforms with ≥1,000 field-data sites: pages, LCP/CLS/INP good rates and all-three pass rate, both crawls.
- `tlds`: per TLD (60 largest + other): pages, share, kind (country code / generic), CWV pass rates, JSON-LD and Open Graph rates, leading platform.
- `structured_data_types`: the 200 most common schema.org types declared in JSON-LD or microdata, share of sites, both crawls.
- `overview_by_rank`, `stack_size`, `categories`: overall rates by popularity bucket, distribution of the number of technologies per site, category summary.

## Method
- One row in the source = one crawled root page (mobile). "Share of sites" = pages with the technology / all pages in that crawl.
- Technologies come from HTTP Archive's open-source detection rules (pattern matches on page code, headers and scripts); categories use the same rule set (first listed category).
- Core Web Vitals use the Chrome UX Report p75 values embedded in the crawl (phone form factor): good = LCP ≤ 2.5 s, CLS ≤ 0.1, INP ≤ 200 ms. A site passes when LCP and CLS are good and INP is good or not reported. Rates are over sites that have CrUX data (31.4% of pages in 2026-05).
- Structured-data types = distinct `@type` values in JSON-LD (including nested types such as ListItem) or schema.org microdata item types on the page.
- Year-on-year changes mix real adoption with updates to the detection rules between crawls; a very large jump for one technology (for example an emoji script or a CDN add-on) can come from a new or changed rule.
- TLD = last label of the domain (so `co.uk` counts as `uk`).

## Coverage
- 13 of 14 database shards answered (missing: 2 (192.168.50.6)). Domains are sharded by hash, so the missing shard removes an even random sample of about 1/14 of domains: shares and rates are unbiased, absolute page counts are about 93% of the crawl.
- The crawl covers sites known to the Chrome UX Report (popular origins), not every website.

## Licence and attribution
Source: **HTTP Archive / Chrome UX Report (public web crawl data)**. HTTP Archive data is published under the Creative Commons Attribution 4.0 licence (CC BY 4.0) and Chrome UX Report data under CC BY 4.0 by Google; please credit them when reusing.
These aggregate tables: CC BY-NC 4.0, attribution "Fliar BI" ([fliarbi.com](https://fliarbi.com)) and the upstream sources above.
More datasets: [fliarbi.com/datasets](https://fliarbi.com/datasets/) · [GitHub index](https://github.com/Busineessfree/open-company-datasets) · contact **b2b@fliarbi.com**.
