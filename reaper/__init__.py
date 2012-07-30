# encoding: utf-8

import logging



logging.basicConfig(
    format='%(asctime)s %(levelname) 10s %(message)s',
    datefmt='%m/%dT%H:%M:%S',
    level=logging.INFO
)

logger = logging.getLogger(name=__name__)
