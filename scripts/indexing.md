# index_articles.py

Index arXiv articles from MySQL database to Elasticsearch.

## Usage

```bash
# Incremental indexing (default - only new articles)
python scripts/index_articles.py

# Full reindexing (all articles)
python scripts/index_articles.py --mode full

# Custom index name (overrides config.json)
python scripts/index_articles.py --index my_index

# Custom Elasticsearch URL
python scripts/index_articles.py --es-url http://localhost:9200
```

## Options

- `--mode {full,incremental,test}` - Indexing mode (default: incremental)
  - `full`: Reindex all articles from database
  - `incremental`: Only index articles newer than latest in index
  - `test`: Index limited number of articles for testing (default: 10000)
- `--limit N` - Maximum number of articles to index (batch size)
- `--offset N` - Number of articles to skip (for batch processing)
- `--batch-size N` - Alias for --limit (batch size for processing)
- `--index INDEX` - Elasticsearch index name (overrides config.json)
- `--es-url URL` - Elasticsearch URL (overrides config.json)
- `--progress-file PATH` - File to write progress updates to (default: /tmp/index_progress.txt)

## Configuration

The script reads configuration from the arxivdigest package config module (`arxivdigest.core.config`).

Required config settings:
- `config_elasticsearch`: Elasticsearch connection settings (url)
- `elastic_index_name`: Default index name
- `config_sql`: MySQL database connection settings (user, password, host, database)

### Index Settings

Elasticsearch index mappings and settings are defined in `config/index_settings.json`. This file contains:
- Index settings (shards, replicas)
- Field mappings (title, abstract, authors, categories, etc.)
- Analyzers and term vectors

Modify this file to customize the index structure.

## Modes

**Incremental Mode**: Queries Elasticsearch for the latest article date and only indexes articles with newer dates. Falls back to full indexing if index is empty.

**Full Mode**: Indexes all articles from the database regardless of what's already in Elasticsearch.

**Test Mode**: Indexes a limited number of articles (default 10000) for testing purposes.

```bash
# Test with 10k articles (default)
python scripts/index_articles.py --mode test

# Test with custom limit
python scripts/index_articles.py --mode test --limit 5000

# Batch processing with offset
python scripts/index_articles.py --mode full --limit 1000 --offset 0
python scripts/index_articles.py --mode full --limit 1000 --offset 1000
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

## Features

- Incremental indexing: Only indexes new articles since last run
- Batch processing: Process articles in chunks with progress tracking
- Progress monitoring: Writes progress to file for background job monitoring
- Automatic index creation: Creates index with proper mappings if it doesn't exist
- Bulk indexing: Uses Elasticsearch bulk API for efficient indexing (500 docs per chunk)

## Requirements

- MySQL database with arXivDigest schema
- Elasticsearch instance running
- Python packages: `mysql-connector-python`, `elasticsearch`
- arxivdigest package installed and configured
- Index settings at `config/index_settings.json`
