# -*- coding: utf-8 -*-
import logging
import sys

from arxivdigest.core.scraper.scrape_metadata import harvestMetadataRss
from arxivdigest.core.scraper.store_metadata import insertIntoDB

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    insertIntoDB(harvestMetadataRss())
