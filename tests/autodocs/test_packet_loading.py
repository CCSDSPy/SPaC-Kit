"""Unit tests for packet loading and directive execution."""
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

from ccsdspy.packet_types import _BasePacket


class TestLoadPacket:
    """Tests for _load_packet method."""

    @patch("spac_kit.autodocs.importlib.import_module")
    def test_load_valid_packet(self, mock_import, mock_directive):
        """Test loading a valid packet from a module."""

        # Create a mock module with a packet
        mock_module = MagicMock()
        mock_packet = Mock(spec=_BasePacket)
        mock_packet.name = "TestPacket"
        mock_packet._fields = []
        mock_module.test_packet = mock_packet
        mock_import.return_value = mock_module

        result = mock_directive._load_packet("test.module.test_packet")

        assert result is not None
        assert isinstance(result, Mock)
        assert result.name == "TestPacket"

    def test_load_nonexistent_module(self, mock_directive):
        """Test loading from a nonexistent module returns None."""
        with patch("spac_kit.autodocs.importlib.import_module") as mock_import:
            mock_import.side_effect = ImportError("Module not found")

            result = mock_directive._load_packet("nonexistent.module.packet")

            assert result is None

    @patch("spac_kit.autodocs.importlib.import_module")
    def test_load_nonexistent_attribute(self, mock_import, mock_directive):
        """Test loading nonexistent attribute returns None."""
        # Create a mock module without the requested packet
        mock_module = MagicMock()
        mock_module.test_packet = None  # Doesn't have the attribute
        mock_import.return_value = mock_module

        # Use getattr to simulate missing attribute
        with patch("spac_kit.autodocs.getattr", return_value=None):
            result = mock_directive._load_packet("test.module.missing_packet")

        assert result is None

    @patch("spac_kit.autodocs.importlib.import_module")
    def test_load_non_packet_attribute(self, mock_import, mock_directive):
        """Test loading a non-packet attribute returns None."""
        # Create a mock module with a non-packet attribute
        mock_module = MagicMock()
        mock_module.not_a_packet = "just a string"
        mock_import.return_value = mock_module

        result = mock_directive._load_packet("test.module.not_a_packet")

        assert result is None

    @patch("spac_kit.autodocs.importlib.import_module")
    def test_load_packet_with_complex_path(self, mock_import, mock_directive):
        """Test loading packet from deeply nested module path."""
        # Create a mock module
        mock_module = MagicMock()
        mock_packet = Mock(spec=_BasePacket)
        mock_packet.name = "DeepPacket"
        mock_packet._fields = []
        mock_module.deep_packet = mock_packet
        mock_import.return_value = mock_module

        result = mock_directive._load_packet(
            "ccsds.mission.instrument.subsystem.deep_packet"
        )

        # Should successfully import the module (minus the last component)
        mock_import.assert_called_once_with("ccsds.mission.instrument.subsystem")
        assert result is not None


class TestDirectiveRun:
    """Tests for the SpacDocsDirective.run method."""

    def test_run_with_valid_packet(self, mock_directive):
        """Test running directive with a valid packet."""
        # Mock the packet loading
        mock_packet = Mock(spec=_BasePacket)
        mock_packet.name = "TestPacket"
        mock_packet._fields = []

        with patch.object(
            mock_directive, "_load_packet", return_value=mock_packet
        ) as mock_load_packet:
            with patch.object(
                mock_directive, "_gen_nodes", return_value=[Mock()]
            ) as mock_gen_nodes:
                result = mock_directive.run()

                # Should call load and gen_nodes
                mock_load_packet.assert_called_once_with("test.module.packet")
                mock_gen_nodes.assert_called_once_with(mock_packet)

                # Should return the generated nodes
                assert len(result) == 1

    def test_run_with_nonexistent_packet(self, mock_directive):
        """Test running directive with nonexistent packet returns empty list."""
        # Mock packet loading to return None
        with patch.object(mock_directive, "_load_packet", return_value=None):
            with patch.object(mock_directive, "_gen_nodes") as mock_gen_nodes:
                # Update the directive's arguments for this test
                mock_directive.arguments = ["nonexistent.module.packet"]
                result = mock_directive.run()

                # Should not call gen_nodes
                mock_gen_nodes.assert_not_called()

                # Should return empty list
                assert result == []

    def test_run_uses_first_argument(self, mock_directive):
        """Test that run uses the first argument from directive arguments."""
        mock_packet = Mock(spec=_BasePacket)
        mock_packet.name = "TestPacket"
        mock_packet._fields = []

        with patch.object(
            mock_directive, "_load_packet", return_value=mock_packet
        ) as mock_load_packet:
            with patch.object(mock_directive, "_gen_nodes", return_value=[]):
                # Update directive's arguments
                mock_directive.arguments = ["correct.module.packet", "ignore.this"]
                mock_directive.run()

                # Should use first argument only
                mock_load_packet.assert_called_once_with("correct.module.packet")


class TestColumnDefinitions:
    """Tests for column definitions in SpacDocsDirective."""

    def test_all_columns_defined(self, mock_directive):
        """Test that ALL_COLUMNS is properly defined."""
        # Should have ALL_COLUMNS defined
        assert hasattr(mock_directive, "ALL_COLUMNS")
        assert len(mock_directive.ALL_COLUMNS) > 0

        # Each column should be a _Column namedtuple
        for col in mock_directive.ALL_COLUMNS:
            assert hasattr(col, "colname")
            assert hasattr(col, "attr")
            assert hasattr(col, "show_on_summary")

    def test_column_attributes(self, mock_directive):
        """Test that columns have expected attributes."""
        # Expected columns
        expected_cols = [
            "Name",
            "DataType",
            "BitLength",
            "BitOffset",
            "ByteOrder",
            "FieldType",
            "ArrayShape",
            "ArrayOrder",
        ]

        actual_cols = [col.colname for col in mock_directive.ALL_COLUMNS]

        for expected in expected_cols:
            assert expected in actual_cols

    def test_summary_columns(self, mock_directive):
        """Test that summary columns are correctly marked."""
        # These columns should be shown in summary
        summary_cols = [
            col.colname for col in mock_directive.ALL_COLUMNS if col.show_on_summary
        ]

        # Should include at least Name, DataType, BitLength, BitOffset, ByteOrder
        assert "Name" in summary_cols
        assert "DataType" in summary_cols
        assert "BitLength" in summary_cols
        assert "BitOffset" in summary_cols
        assert "ByteOrder" in summary_cols

    def test_detail_only_columns(self, mock_directive):
        """Test that some columns are detail-only."""
        # These columns should NOT be shown in summary
        detail_only = [
            col.colname for col in mock_directive.ALL_COLUMNS if not col.show_on_summary
        ]

        # Should include FieldType, ArrayShape, ArrayOrder
        assert "FieldType" in detail_only
        assert "ArrayShape" in detail_only
        assert "ArrayOrder" in detail_only
