"""Generic code to parse a downlink binary file encoded using CCSDS."""
import os
from logging.config import fileConfig

from .parse_ccsds_downlink import parse_ccsds_file  # noqa: F401
from .remove_non_ccsds_headers import strip_non_ccsds_headers  # noqa: F401

conf_file_dir = os.path.dirname(os.path.abspath(__file__))
fileConfig(os.path.join(conf_file_dir, "logger.conf"))
