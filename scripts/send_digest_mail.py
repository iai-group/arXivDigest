# -*- coding: utf-8 -*-
import logging
import sys

from arxivdigest.core.mail import digest_mail

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    digest_mail.send_digest_mail()
