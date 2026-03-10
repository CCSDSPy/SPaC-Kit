"""Unit tests for Excel export functionality."""
import os
import tempfile

import pandas as pd
import pytest
from spac_kit.parser.downlink_to_excel import add_tab_to_xlsx
from spac_kit.parser.downlink_to_excel import export_dfs_to_xlsx
from spac_kit.parser.downlink_to_excel import get_parser


class TestGetParser:
    """Tests for get_parser function."""

    def test_get_parser_returns_argument_parser(self):
        """Test that get_parser returns an ArgumentParser."""
        parser = get_parser()
        assert parser is not None
        assert hasattr(parser, "parse_args")

    def test_parser_has_file_argument(self):
        """Test that parser has required --file argument."""
        parser = get_parser()

        # Test with valid file argument
        args = parser.parse_args(["--file", "test.bin"])
        assert args.file == "test.bin"

    def test_parser_file_argument_required(self):
        """Test that --file argument is required."""
        parser = get_parser()

        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_parser_bdsem_flag(self):
        """Test that parser has --bdsem flag."""
        parser = get_parser()

        args = parser.parse_args(["--file", "test.bin", "--bdsem"])
        assert args.bdsem is True

        args = parser.parse_args(["--file", "test.bin"])
        assert args.bdsem is False

    def test_parser_pkt_header_flag(self):
        """Test that parser has --pkt-header flag."""
        parser = get_parser()

        args = parser.parse_args(["--file", "test.bin", "--pkt-header"])
        assert args.pkt_header is True

        args = parser.parse_args(["--file", "test.bin"])
        assert args.pkt_header is False

    def test_parser_json_header_flag(self):
        """Test that parser has --json-header flag."""
        parser = get_parser()

        args = parser.parse_args(["--file", "test.bin", "--json-header"])
        assert args.json_header is True

        args = parser.parse_args(["--file", "test.bin"])
        assert args.json_header is False

    def test_parser_calculate_crc_flag(self):
        """Test that parser has --calculate-crc flag."""
        parser = get_parser()

        args = parser.parse_args(["--file", "test.bin", "--calculate-crc"])
        assert args.calculate_crc is True

        args = parser.parse_args(["--file", "test.bin"])
        assert args.calculate_crc is False

    def test_parser_multiple_flags(self):
        """Test parser with multiple flags combined."""
        parser = get_parser()

        args = parser.parse_args(
            ["--file", "test.bin", "--bdsem", "--pkt-header", "--calculate-crc"]
        )

        assert args.file == "test.bin"
        assert args.bdsem is True
        assert args.pkt_header is True
        assert args.calculate_crc is True
        assert args.json_header is False


class TestAddTabToXlsx:
    """Tests for add_tab_to_xlsx function."""

    def test_add_single_dataframe(self):
        """Test adding a single DataFrame to Excel."""
        df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            with pd.ExcelWriter(tmp_path) as writer:
                add_tab_to_xlsx(df, writer, name="TestSheet")

            # Read back and verify
            result = pd.read_excel(tmp_path, sheet_name="TestSheet", index_col=0)
            pd.testing.assert_frame_equal(df, result)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_add_dict_of_dataframes(self):
        """Test adding a dictionary of DataFrames."""
        dfs = {
            "Sheet1": pd.DataFrame({"A": [1, 2], "B": [3, 4]}),
            "Sheet2": pd.DataFrame({"X": [5, 6], "Y": [7, 8]}),
        }

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            with pd.ExcelWriter(tmp_path) as writer:
                add_tab_to_xlsx(dfs, writer)

            # Read back and verify
            result1 = pd.read_excel(tmp_path, sheet_name="Sheet1", index_col=0)
            result2 = pd.read_excel(tmp_path, sheet_name="Sheet2", index_col=0)

            pd.testing.assert_frame_equal(dfs["Sheet1"], result1)
            pd.testing.assert_frame_equal(dfs["Sheet2"], result2)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_add_nested_dict_of_dataframes(self):
        """Test adding a nested dictionary of DataFrames."""
        dfs = {
            "Group1": {
                "SubSheet1": pd.DataFrame({"A": [1, 2]}),
                "SubSheet2": pd.DataFrame({"B": [3, 4]}),
            }
        }

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            with pd.ExcelWriter(tmp_path) as writer:
                add_tab_to_xlsx(dfs, writer)

            # Read back and verify - nested structure uses leaf names
            result1 = pd.read_excel(tmp_path, sheet_name="SubSheet1", index_col=0)
            result2 = pd.read_excel(tmp_path, sheet_name="SubSheet2", index_col=0)

            pd.testing.assert_frame_equal(dfs["Group1"]["SubSheet1"], result1)
            pd.testing.assert_frame_equal(dfs["Group1"]["SubSheet2"], result2)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_add_empty_dataframe(self):
        """Test adding an empty DataFrame."""
        df = pd.DataFrame()

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            with pd.ExcelWriter(tmp_path) as writer:
                add_tab_to_xlsx(df, writer, name="EmptySheet")

            # Read back and verify
            result = pd.read_excel(tmp_path, sheet_name="EmptySheet")
            assert result.empty or len(result) == 0
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


class TestExportDfsToXlsx:
    """Tests for export_dfs_to_xlsx function."""

    def test_export_single_dataframe(self):
        """Test exporting a dictionary with single DataFrame."""
        dfs = {"TestSheet": pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})}

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            export_dfs_to_xlsx(dfs, tmp_path)

            # Verify file was created
            assert os.path.exists(tmp_path)

            # Read back and verify
            result = pd.read_excel(tmp_path, sheet_name="TestSheet", index_col=0)
            pd.testing.assert_frame_equal(dfs["TestSheet"], result)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_export_multiple_dataframes(self):
        """Test exporting multiple DataFrames."""
        dfs = {
            "Sheet1": pd.DataFrame({"A": [1, 2]}),
            "Sheet2": pd.DataFrame({"B": [3, 4]}),
            "Sheet3": pd.DataFrame({"C": [5, 6]}),
        }

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            export_dfs_to_xlsx(dfs, tmp_path)

            # Verify all sheets exist
            excel_file = pd.ExcelFile(tmp_path)
            assert set(excel_file.sheet_names) == set(dfs.keys())

            # Verify content
            for sheet_name in dfs.keys():
                result = pd.read_excel(tmp_path, sheet_name=sheet_name, index_col=0)
                pd.testing.assert_frame_equal(dfs[sheet_name], result)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_export_overwrites_existing_file(self):
        """Test that export overwrites existing file."""
        dfs1 = {"Sheet1": pd.DataFrame({"A": [1, 2]})}
        dfs2 = {"Sheet2": pd.DataFrame({"B": [3, 4]})}

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # First export
            export_dfs_to_xlsx(dfs1, tmp_path)

            # Second export should overwrite
            export_dfs_to_xlsx(dfs2, tmp_path)

            # Verify only second export content exists
            excel_file = pd.ExcelFile(tmp_path)
            assert excel_file.sheet_names == ["Sheet2"]
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


class TestExportCcsdsToExcel:
    """Tests for export_ccsds_to_excel function."""

    def test_export_ccsds_to_excel_integration(self):
        """Integration test for complete CCSDS to Excel export.

        Note: This test requires actual CCSDS packet definitions via
        ccsds.packets module, which is not available without a plugin
        package installed.
        """
        pytest.skip("Requires ccsds.packets plugin module - skipping integration test")
