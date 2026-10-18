# Business News Pulse: aggregate bundle

Monthly volume, sentiment and topic aggregates of **business & financial news**, 2019-01..2026-06, plus monthly corporate-event counts.
Built by Fliar BI for the [Business News Pulse](https://huggingface.co/spaces/fliarbi/business-news-pulse) Space and the
[fliarbi/business-news-pulse-aggregates](https://huggingface.co/datasets/fliarbi/business-news-pulse-aggregates) dataset.
**Aggregates only**: no article text, headlines, URLs, publisher names or person names. Every value is a count per month and label.

| file | content | columns |
|---|---|---|
| `monthly_topic_country.parquet` | Business & financial news articles per month by topic (Google-style topic taxonomy, level 2) and the article's primary country (top 30, else 'Other countries'; 'Unspecified' when no country was detected), with sentiment counts. | month, topic_group, topic, country, articles, positive, negative, neutral, tone_sum |
| `monthly_sector.parquet` | Articles per month by company sector (60 most frequent sectors; multi-label, so an article counts once in each sector it is tagged with). | month, sector, articles, positive, negative, neutral, tone_sum |
| `monthly_subtopic.parquet` | Articles per month by the article's top model sub-category (400 largest plus every rising/falling topic). | month, subtopic, articles, positive, negative, neutral, tone_sum |
| `rising_topics.parquet` | Sub-topics whose share of business news grew (100 rising) or shrank (50 falling) most: share in the last 6 full months vs the 12 months before. Minimum 300 articles in the last 6 months and 100 before. | subtopic, articles_last6, articles_prev12, growth_x, share_last6_pct, share_prev12_pct, window_last6, window_prev12, direction |
| `monthly_events_country.parquet` | Corporate events per month by type and company country, from the published Corporate Events 2019-2026 dataset (de-duplicated). | month, event_label, country, events |
| `monthly_events_sector.parquet` | Corporate events per month by type and company sector. | month, event_label, sector, events |
| `monthly_totals.parquet` | Business & financial news articles per month (after exclusions). | month, articles |

## Method
- Business & financial news = articles whose top-scoring topic label sits under Business & Industrial, Finance or Real Estate. 17,411,471 articles over 90 months after exclusions.
- Each article carries model sentiment labels (extreme/very/fair/slight x positive/negative, or none). The top-scoring label decides the article's polarity. Net sentiment = (positive - negative) / all articles x 100. Tone = mean of the label weight (extreme 1, very 0.75, fair 0.5, slight 0.25, negative sign for negative, 0 for none) x 100.
- Topics, sub-topics and sectors are labels from fixed model taxonomies, not free-text tags.
- Rising topics compare shares, not counts, because monthly article volume follows crawler capacity as much as the news cycle.

## Coverage and caveats
- 13 of 14 database shards answered (missing: shard 2). Articles are spread over the shards by hash, so a missing shard removes a random slice of about 1/14 of articles. Counts are lower by that slice; shares and sentiment are unaffected.
- Excluded bulk back-fill days (ingest artefacts carrying an ingest date instead of the publication date): 2022-06-14, 2022-12-29, 2024-04-22, 2025-01-21, 2025-02-13, 2025-02-14, 2025-03-19, 2025-04-11.
- 2026-05 is the last full month. June 2026 is partial (83,732 articles vs 321,496 in May 2026) because ingest thinned from mid-June 2026.
- A primary country was detected for 48% of articles; 51% carry a sub-topic.
- Corporate events: 1,339,579 de-duplicated events, see the Corporate Events 2019-2026 dataset card for its method.

Licence **CC BY-NC 4.0**, attribution "Fliar BI" (https://fliarbi.com). Contact b2b@fliarbi.com.
Index of all datasets: https://fliarbi.com/datasets/ and https://github.com/Busineessfree/open-company-datasets
