"""Unit tests for test utility functions."""
import pandas as pd
import pytest
from spac_kit.parser.test_utils import recursive_compare


class TestRecursiveCompare:
    """Tests for recursive_compare function."""

    def test_compare_identical_dataframes(self):
        """Test comparing identical DataFrames succeeds."""
        df1 = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        df2 = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})

        dfs = {"sheet1": df1}
        dfs_expected = {"sheet1": df2}

        # Should not raise
        recursive_compare(dfs, dfs_expected)

    def test_compare_different_dataframes_raises(self):
        """Test comparing different DataFrames raises assertion."""
        df1 = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        df2 = pd.DataFrame({"A": [1, 2, 9], "B": [4, 5, 6]})  # Different value

        dfs = {"sheet1": df1}
        dfs_expected = {"sheet1": df2}

        with pytest.raises(AssertionError):
            recursive_compare(dfs, dfs_expected)

    def test_compare_missing_key_raises(self):
        """Test comparing when expected has missing key raises assertion."""
        df1 = pd.DataFrame({"A": [1, 2, 3]})
        df2 = pd.DataFrame({"B": [4, 5, 6]})

        dfs = {"sheet1": df1}
        dfs_expected = {"sheet2": df2}

        with pytest.raises(AssertionError):
            recursive_compare(dfs, dfs_expected)

    def test_compare_extra_keys_raises(self):
        """Test comparing when expected has extra keys raises assertion."""
        df1 = pd.DataFrame({"A": [1, 2, 3]})
        df2 = pd.DataFrame({"B": [4, 5, 6]})

        dfs = {"sheet1": df1}
        dfs_expected = {"sheet1": df1.copy(), "sheet2": df2}

        with pytest.raises(AssertionError):
            recursive_compare(dfs, dfs_expected)

    def test_compare_nested_dictionaries(self):
        """Test comparing nested dictionaries of DataFrames."""
        df1 = pd.DataFrame({"A": [1, 2]})
        df2 = pd.DataFrame({"B": [3, 4]})

        dfs = {"group1": {"subsheet1": df1, "subsheet2": df2}}
        dfs_expected = {"group1": {"subsheet1": df1.copy(), "subsheet2": df2.copy()}}

        # Should not raise
        recursive_compare(dfs, dfs_expected)

    def test_compare_nested_with_difference_raises(self):
        """Test comparing nested dictionaries with differences raises."""
        df1 = pd.DataFrame({"A": [1, 2]})
        df2 = pd.DataFrame({"B": [3, 4]})
        df3 = pd.DataFrame({"B": [9, 9]})  # Different

        dfs = {"group1": {"subsheet1": df1, "subsheet2": df2}}
        dfs_expected = {"group1": {"subsheet1": df1.copy(), "subsheet2": df3}}

        with pytest.raises(AssertionError):
            recursive_compare(dfs, dfs_expected)

    def test_compare_empty_dictionaries(self):
        """Test comparing empty dictionaries succeeds."""
        dfs = {}
        dfs_expected = {}

        # Should not raise
        recursive_compare(dfs, dfs_expected)

    def test_compare_multiple_sheets(self):
        """Test comparing dictionaries with multiple sheets."""
        dfs = {
            "sheet1": pd.DataFrame({"A": [1, 2]}),
            "sheet2": pd.DataFrame({"B": [3, 4]}),
            "sheet3": pd.DataFrame({"C": [5, 6]}),
        }
        dfs_expected = {
            "sheet1": pd.DataFrame({"A": [1, 2]}),
            "sheet2": pd.DataFrame({"B": [3, 4]}),
            "sheet3": pd.DataFrame({"C": [5, 6]}),
        }

        # Should not raise
        recursive_compare(dfs, dfs_expected)

    def test_compare_mixed_nesting_levels(self):
        """Test comparing with mixed nesting levels."""
        dfs = {
            "flat_sheet": pd.DataFrame({"A": [1, 2]}),
            "nested_group": {"nested_sheet": pd.DataFrame({"B": [3, 4]})},
        }
        dfs_expected = {
            "flat_sheet": pd.DataFrame({"A": [1, 2]}),
            "nested_group": {"nested_sheet": pd.DataFrame({"B": [3, 4]})},
        }

        # Should not raise
        recursive_compare(dfs, dfs_expected)

    def test_compare_dataframe_different_columns_raises(self):
        """Test comparing DataFrames with different columns raises."""
        df1 = pd.DataFrame({"A": [1, 2, 3]})
        df2 = pd.DataFrame({"B": [1, 2, 3]})  # Different column name

        dfs = {"sheet1": df1}
        dfs_expected = {"sheet1": df2}

        with pytest.raises(AssertionError):
            recursive_compare(dfs, dfs_expected)

    def test_compare_dataframe_different_length_raises(self):
        """Test comparing DataFrames with different lengths raises."""
        df1 = pd.DataFrame({"A": [1, 2, 3]})
        df2 = pd.DataFrame({"A": [1, 2]})  # Different length

        dfs = {"sheet1": df1}
        dfs_expected = {"sheet1": df2}

        with pytest.raises(AssertionError):
            recursive_compare(dfs, dfs_expected)

    def test_compare_ignores_dtype_differences(self):
        """Test that dtype differences are ignored (check_dtype=False)."""
        df1 = pd.DataFrame({"A": [1, 2, 3]})  # int
        df2 = pd.DataFrame({"A": [1.0, 2.0, 3.0]})  # float

        dfs = {"sheet1": df1}
        dfs_expected = {"sheet1": df2}

        # Should not raise because check_dtype=False in implementation
        recursive_compare(dfs, dfs_expected)


class TestCompareFunction:
    """Tests for the compare function.

    Note: These are limited integration tests as compare() requires
    actual file system setup with in.bin and out.pickle files.
    """

    def test_compare_with_test_directory(self):
        """Test compare function with a temporary test directory.

        Note: This test requires ccsds.packets plugin module.
        """
        pytest.skip("Requires ccsds.packets plugin module - skipping integration test")

    def test_compare_create_output_flag(self):
        """Test compare function with create_output=True.

        Note: This test requires ccsds.packets plugin module.
        """
        pytest.skip("Requires ccsds.packets plugin module - skipping integration test")
