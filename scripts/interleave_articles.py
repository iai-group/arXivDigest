# -*- coding: utf-8 -*-
import logging
import sys

from arxivdigest.core.interleave import multileave_articles

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    multileave_articles.run()
