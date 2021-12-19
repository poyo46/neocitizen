import logging
from logging import NullHandler

from .api import NeocitiesApi  # noqa: F401

__title__ = "neocitizen"
__description__ = "Python client library for Neocities API"
__url__ = "https://github.com/poyo46/neocitizen"
__version__ = "1.0.0"
__author__ = "poyo46"
__author_email__ = "poyo4rock@gmail.com"
__license__ = "Apache-2.0"
__copyright__ = "Copyright 2021 poyo46"

# Set default logging handler to avoid "No handler found" warnings.
logging.getLogger(__name__).addHandler(NullHandler())
