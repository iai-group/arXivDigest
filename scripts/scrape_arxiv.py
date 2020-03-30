# -*- coding: utf-8 -*-
import logging
import sys

from arxivdigest.core.scraper.scrape_metadata import harvest_metadata_rss
from arxivdigest.core.scraper.store_metadata import insert_into_db

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    insert_into_db(harvest_metadata_rss())
