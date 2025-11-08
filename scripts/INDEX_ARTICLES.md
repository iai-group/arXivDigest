# index_articles.py

Index arXiv articles from MySQL database to Elasticsearch.

## Usage

```bash
# Incremental indexing (default - only new articles)
python scripts/index_articles.py

# Full reindexing (all articles)
python scripts/index_articles.py --mode full

# Custom index name
python scripts/index_articles.py --index my_index

# Custom Elasticsearch URL
python scripts/index_articles.py --es-url http://localhost:9200
```

## Options

- `--mode {full,incremental,test}` - Indexing mode (default: incremental)
  - `full`: Reindex all articles from database
  - `incremental`: Only index articles newer than latest in index
  - `test`: Index limited number of articles for testing
- `--limit N` - Limit number of articles (default: 10000, used with test mode)
- `--index INDEX` - Elasticsearch index name (default: arxiv)
- `--es-url URL` - Elasticsearch URL (overrides config.json)

## Modes

**Incremental Mode**: Queries Elasticsearch for the latest article date and only indexes articles with newer dates. Falls back to full indexing if index is empty.

**Full Mode**: Indexes all articles from the database regardless of what's already in Elasticsearch.

**Test Mode**: Indexes a limited number of articles (default 10k) for testing purposes.

```bash
# Test with 10k articles
python scripts/index_articles.py --mode test

# Test with custom limit
python scripts/index_articles.py --mode test --limit 5000
```

## Server Deployment

### Cron Job (Daily Incremental)
```bash
0 2 * * * cd /path/to/arXivDigest && python scripts/index_articles.py
```

### Systemd Timer (Hourly Incremental)
```ini
# /etc/systemd/system/index-articles.timer
[Unit]
Description=Index arXiv articles hourly

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
```

```ini
# /etc/systemd/system/index-articles.service
[Unit]
Description=Index arXiv articles

[Service]
Type=oneshot
WorkingDirectory=/path/to/arXivDigest
ExecStart=/usr/bin/python3 scripts/index_articles.py
```

Enable: `systemctl enable --now index-articles.timer`

## Requirements

- MySQL database with arXivDigest schema
- Elasticsearch instance running
- Python packages: `mysql-connector-python`, `elasticsearch`
