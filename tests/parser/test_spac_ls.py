"""Unit tests for spac-ls CLI tool."""
import sys
from io import StringIO
from unittest.mock import MagicMock, patch, PropertyMock

import ccsdspy
import pytest
from spac_kit.parser.spac_ls import format_packet_info, list_packages, main


def create_mock_packet(class_name, module, base_class, apid, name=None, description=None):
    """Create a properly mocked packet for testing.

    Args:
        class_name: Name of the packet class
        module: Module path
        base_class: Base class (e.g., ccsdspy.FixedLength) - only the name is used
        apid: APID value
        name: Optional packet name (None means no name attribute)
        description: Optional packet description (None means no description attribute)
    """
    # Create a mock base class with the right name
    MockBase = type(base_class.__name__, (object,), {})

    # Create the packet class inheriting from the mock base
    DynamicClass = type(class_name, (MockBase,), {})
    DynamicClass.__module__ = module

    # Create an instance
    mock_packet = DynamicClass()

    # Set attributes
    mock_packet.apid = apid
    if name is not None:
        mock_packet.name = name
    if description is not None:
        mock_packet.description = description

    return mock_packet


class TestFormatPacketInfo:
    """Tests for format_packet_info function."""

    def test_format_packet_with_all_attributes(self):
        """Test formatting a packet with all attributes."""
        mock_packet = create_mock_packet(
            "TestPacket",
            "ccsds.packets.test",
            ccsdspy.FixedLength,
            100,
            "Test Telemetry Packet",
            "Fixed length telemetry packet"
        )

        info = format_packet_info(mock_packet)

        assert info["apid"] == 100
        assert info["packet"] == "ccsds.packets.test.TestPacket"
        assert info["name"] == "Test Telemetry Packet"
        assert info["description"] == "Fixed length telemetry packet"

    def test_format_packet_without_name(self):
        """Test formatting a packet without name attribute."""
        mock_packet = create_mock_packet(
            "AnonymousPacket",
            "ccsds.packets.generic",
            ccsdspy.VariableLength,
            200,
            None,  # No name
            "Variable length packet"
        )

        info = format_packet_info(mock_packet)

        assert info["apid"] == 200
        assert info["packet"] == "ccsds.packets.generic.AnonymousPacket"
        assert info["name"] == ""
        assert info["description"] == "Variable length packet"

    def test_format_packet_without_apid(self):
        """Test formatting a packet without apid attribute."""
        mock_packet = create_mock_packet(
            "NoApidPacket",
            "ccsds.packets.test",
            ccsdspy.FixedLength,
            999,  # Will be deleted
            "No APID",
            "Packet without APID"
        )
        delattr(mock_packet, 'apid')

        info = format_packet_info(mock_packet)

        assert info["apid"] == "N/A"
        assert info["packet"] == "ccsds.packets.test.NoApidPacket"
        assert info["name"] == "No APID"
        assert info["description"] == "Packet without APID"

    def test_format_packet_without_description(self):
        """Test formatting a packet without description attribute."""
        # Python classes always have at least object as a base
        mock_class = type("DirectObjectPacket", (object,), {})
        mock_class.__module__ = "ccsds.packets.test"
        mock_packet = mock_class()
        mock_packet.apid = 300
        mock_packet.name = "Direct Object"
        # No description attribute

        info = format_packet_info(mock_packet)

        assert info["apid"] == 300
        assert info["packet"] == "ccsds.packets.test.DirectObjectPacket"
        assert info["name"] == "Direct Object"
        assert info["description"] == ""

    def test_format_packet_with_none_name(self):
        """Test formatting a packet where name attribute is explicitly None."""
        mock_class = type("NoneNamePacket", (object,), {})
        mock_class.__module__ = "ccsds.packets.test"
        mock_packet = mock_class()
        mock_packet.apid = 400
        mock_packet.name = None  # Explicitly None
        mock_packet.description = "Test description"

        info = format_packet_info(mock_packet)

        assert info["apid"] == 400
        assert info["packet"] == "ccsds.packets.test.NoneNamePacket"
        assert info["name"] == ""
        assert info["description"] == "Test description"

    def test_format_packet_with_none_description(self):
        """Test formatting a packet where description attribute is explicitly None."""
        mock_class = type("NoneDescPacket", (object,), {})
        mock_class.__module__ = "ccsds.packets.test"
        mock_packet = mock_class()
        mock_packet.apid = 500
        mock_packet.name = "Test Name"
        mock_packet.description = None  # Explicitly None

        info = format_packet_info(mock_packet)

        assert info["apid"] == 500
        assert info["packet"] == "ccsds.packets.test.NoneDescPacket"
        assert info["name"] == "Test Name"
        assert info["description"] == ""


class TestListPackages:
    """Tests for list_packages function."""

    def test_list_packages_with_no_parsers(self, capsys):
        """Test list_packages when no parsers are found."""
        with patch("spac_kit.parser.spac_ls.import_ccsds_packet_packages", return_value=[]):
            result = list_packages()

            assert result == 1
            captured = capsys.readouterr()
            assert "No CCSDS packet packages found" in captured.out

    def test_list_packages_with_single_parser(self, capsys):
        """Test list_packages with a single parser."""
        mock_packet = create_mock_packet(
            "TestPacket",
            "ccsds.packets.test",
            ccsdspy.FixedLength,
            100,
            "Test Packet",
            "A test packet"
        )

        with patch("spac_kit.parser.spac_ls.import_ccsds_packet_packages", return_value=[mock_packet]):
            result = list_packages()

            assert result == 0
            captured = capsys.readouterr()
            assert "APID" in captured.out
            assert "PACKET" in captured.out
            assert "NAME" in captured.out
            assert "DESCRIPTION" in captured.out
            assert "100" in captured.out
            assert "ccsds.packets.test.TestPacket" in captured.out
            assert "Test Packet" in captured.out
            assert "A test packet" in captured.out
            assert "Total: 1 packet definition(s)" in captured.out

    def test_list_packages_with_multiple_parsers_sorted(self, capsys):
        """Test list_packages with multiple parsers sorted by APID."""
        mock_packet1 = create_mock_packet("Packet200", "ccsds.packets.test", ccsdspy.FixedLength, 200, "Second", "Second packet")
        mock_packet2 = create_mock_packet("Packet100", "ccsds.packets.test", ccsdspy.FixedLength, 100, "First", "First packet")
        mock_packet3 = create_mock_packet("Packet150", "ccsds.packets.test", ccsdspy.FixedLength, 150, "Middle", "Middle packet")

        # Pass in unsorted order
        with patch("spac_kit.parser.spac_ls.import_ccsds_packet_packages",
                   return_value=[mock_packet1, mock_packet2, mock_packet3]):
            result = list_packages()

            assert result == 0
            captured = capsys.readouterr()
            output_lines = captured.out.split('\n')

            # Find lines with APIDs (skip header and separator)
            apid_lines = [line for line in output_lines if line.strip() and not line.startswith('APID') and not line.startswith('-')]

            # Check that APIDs appear in sorted order
            assert "100" in apid_lines[0]
            assert "150" in apid_lines[1]
            assert "200" in apid_lines[2]
            assert "Total: 3 packet definition(s)" in captured.out

    def test_list_packages_includes_full_packet_identifier(self, capsys):
        """Test that output includes full packet identifier (module.class)."""
        mock_packet = create_mock_packet(
            "TestPacket",
            "ccsds.packets.test.submodule",
            ccsdspy.VariableLength,
            100,
            "Test",
            "Variable length test packet"
        )

        with patch("spac_kit.parser.spac_ls.import_ccsds_packet_packages", return_value=[mock_packet]):
            result = list_packages()

            assert result == 0
            captured = capsys.readouterr()
            assert "PACKET" in captured.out
            assert "ccsds.packets.test.submodule.TestPacket" in captured.out
            assert "DESCRIPTION" in captured.out
            assert "Variable length test packet" in captured.out

    def test_list_packages_handles_import_error(self, capsys):
        """Test list_packages when import raises an error."""
        with patch("spac_kit.parser.spac_ls.import_ccsds_packet_packages",
                   side_effect=ImportError("ccsds.packets not found")):
            result = list_packages()

            assert result == 1
            captured = capsys.readouterr()
            assert "Error: Unable to import ccsds.packets namespace" in captured.err

    def test_list_packages_handles_general_exception(self, capsys):
        """Test list_packages when a general exception occurs."""
        with patch("spac_kit.parser.spac_ls.import_ccsds_packet_packages",
                   side_effect=RuntimeError("Something went wrong")):
            result = list_packages()

            assert result == 1
            captured = capsys.readouterr()
            assert "Error: Something went wrong" in captured.err

    def test_list_packages_with_csv_delimiter(self, capsys):
        """Test list_packages with CSV delimiter."""
        mock_packet = create_mock_packet("TestPacket", "ccsds.packets.test", ccsdspy.FixedLength, 100, "Test Packet", "A test packet for CSV")

        with patch("spac_kit.parser.spac_ls.import_ccsds_packet_packages", return_value=[mock_packet]):
            result = list_packages(delimiter=",")

            assert result == 0
            captured = capsys.readouterr()
            lines = captured.out.strip().split('\n')

            # Check header
            assert lines[0] == "APID,PACKET,NAME,DESCRIPTION"
            # Check data row
            assert lines[1] == "100,ccsds.packets.test.TestPacket,Test Packet,A test packet for CSV"
            # No total count in CSV mode
            assert "Total:" not in captured.out

    def test_list_packages_with_tab_delimiter(self, capsys):
        """Test list_packages with tab delimiter."""
        mock_packet = create_mock_packet("TestPacket", "ccsds.packets.test", ccsdspy.VariableLength, 200, "Tab Test", "Tab delimited test packet")

        with patch("spac_kit.parser.spac_ls.import_ccsds_packet_packages", return_value=[mock_packet]):
            result = list_packages(delimiter="\t")

            assert result == 0
            captured = capsys.readouterr()
            lines = captured.out.strip().split('\n')

            # Check header
            assert lines[0] == "APID\tPACKET\tNAME\tDESCRIPTION"
            # Check data row
            assert lines[1] == "200\tccsds.packets.test.TestPacket\tTab Test\tTab delimited test packet"

    def test_list_packages_with_delimiter_multiple_packets_sorted(self, capsys):
        """Test list_packages with delimiter and multiple packets are sorted."""
        mock_packet1 = create_mock_packet("Packet300", "ccsds.packets.test", ccsdspy.FixedLength, 300, "Third", "Third packet")
        mock_packet2 = create_mock_packet("Packet100", "ccsds.packets.test", ccsdspy.FixedLength, 100, "First", "First packet")
        mock_packet3 = create_mock_packet("Packet200", "ccsds.packets.test", ccsdspy.FixedLength, 200, "Second", "Second packet")

        # Pass in unsorted order
        with patch("spac_kit.parser.spac_ls.import_ccsds_packet_packages",
                   return_value=[mock_packet1, mock_packet2, mock_packet3]):
            result = list_packages(delimiter="|")

            assert result == 0
            captured = capsys.readouterr()
            lines = captured.out.strip().split('\n')

            # Check sorting (skip header)
            assert "100|" in lines[1]
            assert "200|" in lines[2]
            assert "300|" in lines[3]

    def test_list_packages_with_delimiter_empty_name(self, capsys):
        """Test list_packages with delimiter when packet has no name."""
        mock_packet = create_mock_packet("NoNamePacket", "ccsds.packets.test", ccsdspy.FixedLength, 400, None, "Packet without a name")

        with patch("spac_kit.parser.spac_ls.import_ccsds_packet_packages", return_value=[mock_packet]):
            result = list_packages(delimiter=",")

            assert result == 0
            captured = capsys.readouterr()
            lines = captured.out.strip().split('\n')

            # Empty name should result in empty field
            assert lines[1] == "400,ccsds.packets.test.NoNamePacket,,Packet without a name"

    def test_list_packages_with_none_attributes(self, capsys):
        """Test list_packages when packet has None for name and description."""
        # Create mock packet with None attributes
        mock_class = type("NullAttributePacket", (object,), {})
        mock_class.__module__ = "ccsds.packets.test"
        mock_packet = mock_class()
        mock_packet.apid = 500
        mock_packet.name = None  # Explicitly None
        mock_packet.description = None  # Explicitly None

        with patch("spac_kit.parser.spac_ls.import_ccsds_packet_packages", return_value=[mock_packet]):
            result = list_packages()

            assert result == 0
            captured = capsys.readouterr()
            # Should not crash and should handle None values as empty strings
            assert "500" in captured.out
            assert "ccsds.packets.test.NullAttributePacket" in captured.out


class TestMain:
    """Tests for main CLI entry point."""

    def test_main_with_no_arguments(self):
        """Test main function with no arguments (default behavior)."""
        mock_packet = create_mock_packet("TestPacket", "ccsds.packets.test", ccsdspy.FixedLength, 100, "Test", "Test description")

        with patch("spac_kit.parser.spac_ls.import_ccsds_packet_packages", return_value=[mock_packet]):
            with patch("sys.argv", ["spac-ls"]):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 0

    def test_main_with_no_packages(self):
        """Test main function when no packages are found."""
        with patch("spac_kit.parser.spac_ls.import_ccsds_packet_packages", return_value=[]):
            with patch("sys.argv", ["spac-ls"]):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 1

    def test_main_with_import_error(self):
        """Test main function when import fails."""
        with patch("spac_kit.parser.spac_ls.import_ccsds_packet_packages",
                   side_effect=ImportError("ccsds.packets not found")):
            with patch("sys.argv", ["spac-ls"]):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 1

    def test_main_with_delimiter_flag(self):
        """Test main function with delimiter flag."""
        mock_packet = create_mock_packet("TestPacket", "ccsds.packets.test", ccsdspy.FixedLength, 100, "Test", "Test description")

        with patch("spac_kit.parser.spac_ls.import_ccsds_packet_packages", return_value=[mock_packet]):
            with patch("sys.argv", ["spac-ls", "-d", ","]):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 0
