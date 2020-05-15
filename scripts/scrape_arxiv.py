# -*- coding: utf-8 -*-
import datetime
import logging
import sys

from arxivdigest.core.config import config_arxiv_scraper
from arxivdigest.core.scraper.scrape_metadata import get_records_by_date
from arxivdigest.core.scraper.store_metadata import insert_into_db

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    start_date = config_arxiv_scraper.get('start_date', None)
    if not start_date:
        last_n_days = config_arxiv_scraper.get('last_n_days', 1)
        start_date = datetime.date.today() - datetime.timedelta(last_n_days)
    end_date = config_arxiv_scraper.get('end_date', None)

    insert_into_db(get_records_by_date(start_date, end_date))
