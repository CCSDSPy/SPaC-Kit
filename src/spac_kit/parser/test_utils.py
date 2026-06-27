"""Utilities to test the packet parsing."""
import logging
import os
import pickle

import pandas as pd
from spac_kit.parser.downlink_to_excel import export_dfs_to_xlsx
from spac_kit.parser.parse_ccsds_downlink import parse_ccsds_file
from spac_kit.parser.remove_non_ccsds_headers import strip_non_ccsds_headers

logger = logging.getLogger(__name__)


# pylint: disable=too-many-arguments,too-many-positional-arguments
def compare(
    local_dir: str,
    is_bdsem: bool = False,
    has_pkt_header: bool = False,
    has_json_header: bool = False,
    create_output: bool = False,
    create_spreadsheet: bool = False,
):
    """Run parsing and compare results with a reference.

    Args:
        local_dir: local directory containing input file
        is_bdsem: whether file is from BDSEM
        has_pkt_header: whether file has packet headers
        has_json_header: whether file has JSON header
        create_output: whether to create output pickle file
        create_spreadsheet: whether to create Excel spreadsheet
    """
    input_file = os.path.join(local_dir, "in.bin")

    with open(input_file, "rb") as f:
        ccsds_file = strip_non_ccsds_headers(
            f, is_bdsem, has_pkt_header, has_json_header
        )
        dfs = parse_ccsds_file(ccsds_file, do_calculate_crc=True)

    output_file = os.path.join(local_dir, "out.pickle")

    # save the result as needed
    if create_output:
        with open(output_file, "wb") as f:
            f.write(pickle.dumps(dfs))

    if create_spreadsheet:
        xlsx_file = os.path.join(local_dir, "out.xlsx")
        export_dfs_to_xlsx(dfs, xlsx_file)

    with open(output_file, "rb") as f:
        dfs_expected = pickle.load(f)

    recursive_compare(dfs, dfs_expected)


def recursive_compare(dfs, dfs_expected):
    """Compare embedded dictionary of dictionaries of pandas dataframes.

    Compare the keys and the actual dataframes. None should be missing and all should
    match.

    Args:
        dfs: dictionary of dictionaries of dataframes
        dfs_expected: expected dictionary of dictionaries

    Returns:
        True if the pandas dataframes are identical at the same location
    """
    for k, df in dfs.items():
        logger.info("Compare dataframe %s", k)
        assert k in dfs_expected.keys()
        if isinstance(dfs_expected[k], dict):
            recursive_compare(df, dfs_expected[k])
        else:
            pd.testing.assert_frame_equal(df, dfs_expected[k], check_dtype=False)
        del dfs_expected[k]

    assert len(dfs_expected) == 0
