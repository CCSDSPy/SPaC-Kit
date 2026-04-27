"""Unit tests for spac-ls CLI tool."""
import sys
from io import StringIO
from unittest.mock import MagicMock, patch

import ccsdspy
import pytest
from spac_kit.parser.spac_ls import format_packet_info, list_packages, main


class TestFormatPacketInfo:
    """Tests for format_packet_info function."""

    def test_format_packet_with_all_attributes(self):
        """Test formatting a packet with all attributes."""
        mock_packet = MagicMock(spec=ccsdspy.FixedLength)
        mock_packet.__class__.__name__ = "TestPacket"
        mock_packet.__class__.__module__ = "ccsds.packets.test"
        mock_packet.apid = 100
        mock_packet.name = "Test Telemetry Packet"
        mock_packet._fields = [MagicMock(), MagicMock(), MagicMock()]

        info = format_packet_info(mock_packet)

        assert info["apid"] == 100
        assert info["type"] == "TestPacket"
        assert info["name"] == "Test Telemetry Packet"
        assert info["module"] == "ccsds.packets.test"
        assert info["fields"] == 3

    def test_format_packet_without_name(self):
        """Test formatting a packet without name attribute."""
        mock_packet = MagicMock(spec=ccsdspy.FixedLength)
        mock_packet.__class__.__name__ = "AnonymousPacket"
        mock_packet.__class__.__module__ = "ccsds.packets.generic"
        mock_packet.apid = 200
        # Remove name attribute
        if hasattr(mock_packet, 'name'):
            delattr(mock_packet, 'name')
        mock_packet._fields = [MagicMock(), MagicMock()]

        info = format_packet_info(mock_packet)

        assert info["apid"] == 200
        assert info["type"] == "AnonymousPacket"
        assert info["name"] == ""
        assert info["fields"] == 2

    def test_format_packet_without_apid(self):
        """Test formatting a packet without apid attribute."""
        mock_packet = MagicMock(spec=ccsdspy.FixedLength)
        mock_packet.__class__.__name__ = "NoApidPacket"
        mock_packet.__class__.__module__ = "ccsds.packets.test"
        if hasattr(mock_packet, 'apid'):
            delattr(mock_packet, 'apid')
        mock_packet.name = "No APID"
        mock_packet._fields = []

        info = format_packet_info(mock_packet)

        assert info["apid"] == "N/A"
        assert info["type"] == "NoApidPacket"
        assert info["name"] == "No APID"
        assert info["fields"] == 0

    def test_format_packet_without_fields(self):
        """Test formatting a packet without _fields attribute."""
        mock_packet = MagicMock(spec=ccsdspy.FixedLength)
        mock_packet.__class__.__name__ = "NoFieldsPacket"
        mock_packet.__class__.__module__ = "ccsds.packets.test"
        mock_packet.apid = 300
        mock_packet.name = "No Fields"
        # Remove _fields attribute
        if hasattr(mock_packet, '_fields'):
            delattr(mock_packet, '_fields')

        info = format_packet_info(mock_packet)

        assert info["apid"] == 300
        assert info["fields"] == 0


class TestListPackages:
    """Tests for list_packages function."""

    def test_list_packages_with_no_parsers(self, capsys):
        """Test list_packages when no parsers are found."""
        with patch("spac_kit.parser.spac_ls.import_ccsds_packet_packages", return_value=[]):
            result = list_packages(verbose=False)

            assert result == 1
            captured = capsys.readouterr()
            assert "No CCSDS packet packages found" in captured.out

    def test_list_packages_with_single_parser(self, capsys):
        """Test list_packages with a single parser."""
        mock_packet = MagicMock(spec=ccsdspy.FixedLength)
        mock_packet.__class__.__name__ = "TestPacket"
        mock_packet.__class__.__module__ = "ccsds.packets.test"
        mock_packet.apid = 100
        mock_packet.name = "Test Packet"
        mock_packet._fields = [MagicMock(), MagicMock()]

        with patch("spac_kit.parser.spac_ls.import_ccsds_packet_packages", return_value=[mock_packet]):
            result = list_packages(verbose=False)

            assert result == 0
            captured = capsys.readouterr()
            assert "APID" in captured.out
            assert "TYPE" in captured.out
            assert "FIELDS" in captured.out
            assert "100" in captured.out
            assert "TestPacket" in captured.out
            assert "Test Packet" in captured.out
            assert "Total: 1 packet definition(s)" in captured.out

    def test_list_packages_with_multiple_parsers_sorted(self, capsys):
        """Test list_packages with multiple parsers sorted by APID."""
        mock_packet1 = MagicMock(spec=ccsdspy.FixedLength)
        mock_packet1.__class__.__name__ = "Packet200"
        mock_packet1.__class__.__module__ = "ccsds.packets.test"
        mock_packet1.apid = 200
        mock_packet1.name = "Second"
        mock_packet1._fields = [MagicMock()]

        mock_packet2 = MagicMock(spec=ccsdspy.FixedLength)
        mock_packet2.__class__.__name__ = "Packet100"
        mock_packet2.__class__.__module__ = "ccsds.packets.test"
        mock_packet2.apid = 100
        mock_packet2.name = "First"
        mock_packet2._fields = [MagicMock(), MagicMock()]

        mock_packet3 = MagicMock(spec=ccsdspy.FixedLength)
        mock_packet3.__class__.__name__ = "Packet150"
        mock_packet3.__class__.__module__ = "ccsds.packets.test"
        mock_packet3.apid = 150
        mock_packet3.name = "Middle"
        mock_packet3._fields = []

        # Pass in unsorted order
        with patch("spac_kit.parser.spac_ls.import_ccsds_packet_packages",
                   return_value=[mock_packet1, mock_packet2, mock_packet3]):
            result = list_packages(verbose=False)

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

    def test_list_packages_verbose_includes_module(self, capsys):
        """Test that verbose mode includes module path."""
        mock_packet = MagicMock(spec=ccsdspy.FixedLength)
        mock_packet.__class__.__name__ = "TestPacket"
        mock_packet.__class__.__module__ = "ccsds.packets.test.submodule"
        mock_packet.apid = 100
        mock_packet.name = "Test"
        mock_packet._fields = []

        with patch("spac_kit.parser.spac_ls.import_ccsds_packet_packages", return_value=[mock_packet]):
            result = list_packages(verbose=True)

            assert result == 0
            captured = capsys.readouterr()
            assert "MODULE" in captured.out
            assert "ccsds.packets.test.submodule" in captured.out

    def test_list_packages_non_verbose_excludes_module(self, capsys):
        """Test that non-verbose mode excludes module path."""
        mock_packet = MagicMock(spec=ccsdspy.FixedLength)
        mock_packet.__class__.__name__ = "TestPacket"
        mock_packet.__class__.__module__ = "ccsds.packets.test"
        mock_packet.apid = 100
        mock_packet.name = "Test"
        mock_packet._fields = []

        with patch("spac_kit.parser.spac_ls.import_ccsds_packet_packages", return_value=[mock_packet]):
            result = list_packages(verbose=False)

            assert result == 0
            captured = capsys.readouterr()
            # MODULE header should not be present in non-verbose mode
            header_line = [line for line in captured.out.split('\n') if 'APID' in line and 'TYPE' in line][0]
            assert "MODULE" not in header_line

    def test_list_packages_handles_import_error(self, capsys):
        """Test list_packages when import raises an error."""
        with patch("spac_kit.parser.spac_ls.import_ccsds_packet_packages",
                   side_effect=ImportError("ccsds.packets not found")):
            result = list_packages(verbose=False)

            assert result == 1
            captured = capsys.readouterr()
            assert "Error: Unable to import ccsds.packets namespace" in captured.err

    def test_list_packages_handles_general_exception(self, capsys):
        """Test list_packages when a general exception occurs."""
        with patch("spac_kit.parser.spac_ls.import_ccsds_packet_packages",
                   side_effect=RuntimeError("Something went wrong")):
            result = list_packages(verbose=False)

            assert result == 1
            captured = capsys.readouterr()
            assert "Error: Something went wrong" in captured.err

    def test_list_packages_with_csv_delimiter(self, capsys):
        """Test list_packages with CSV delimiter."""
        mock_packet = MagicMock(spec=ccsdspy.FixedLength)
        mock_packet.__class__.__name__ = "TestPacket"
        mock_packet.__class__.__module__ = "ccsds.packets.test"
        mock_packet.apid = 100
        mock_packet.name = "Test Packet"
        mock_packet._fields = [MagicMock(), MagicMock()]

        with patch("spac_kit.parser.spac_ls.import_ccsds_packet_packages", return_value=[mock_packet]):
            result = list_packages(verbose=False, delimiter=",")

            assert result == 0
            captured = capsys.readouterr()
            lines = captured.out.strip().split('\n')

            # Check header
            assert lines[0] == "APID,TYPE,FIELDS,NAME"
            # Check data row
            assert lines[1] == "100,TestPacket,2,Test Packet"
            # No total count in CSV mode
            assert "Total:" not in captured.out

    def test_list_packages_with_tab_delimiter(self, capsys):
        """Test list_packages with tab delimiter."""
        mock_packet = MagicMock(spec=ccsdspy.FixedLength)
        mock_packet.__class__.__name__ = "TestPacket"
        mock_packet.__class__.__module__ = "ccsds.packets.test"
        mock_packet.apid = 200
        mock_packet.name = "Tab Test"
        mock_packet._fields = [MagicMock()]

        with patch("spac_kit.parser.spac_ls.import_ccsds_packet_packages", return_value=[mock_packet]):
            result = list_packages(verbose=False, delimiter="\t")

            assert result == 0
            captured = capsys.readouterr()
            lines = captured.out.strip().split('\n')

            # Check header
            assert lines[0] == "APID\tTYPE\tFIELDS\tNAME"
            # Check data row
            assert lines[1] == "200\tTestPacket\t1\tTab Test"

    def test_list_packages_with_delimiter_verbose(self, capsys):
        """Test list_packages with delimiter in verbose mode."""
        mock_packet = MagicMock(spec=ccsdspy.FixedLength)
        mock_packet.__class__.__name__ = "VerbosePacket"
        mock_packet.__class__.__module__ = "ccsds.packets.verbose.test"
        mock_packet.apid = 300
        mock_packet.name = "Verbose"
        mock_packet._fields = []

        with patch("spac_kit.parser.spac_ls.import_ccsds_packet_packages", return_value=[mock_packet]):
            result = list_packages(verbose=True, delimiter=",")

            assert result == 0
            captured = capsys.readouterr()
            lines = captured.out.strip().split('\n')

            # Check header includes MODULE
            assert lines[0] == "APID,TYPE,FIELDS,NAME,MODULE"
            # Check data row includes module
            assert lines[1] == "300,VerbosePacket,0,Verbose,ccsds.packets.verbose.test"

    def test_list_packages_with_delimiter_multiple_packets_sorted(self, capsys):
        """Test list_packages with delimiter and multiple packets are sorted."""
        mock_packet1 = MagicMock(spec=ccsdspy.FixedLength)
        mock_packet1.__class__.__name__ = "Packet300"
        mock_packet1.__class__.__module__ = "ccsds.packets.test"
        mock_packet1.apid = 300
        mock_packet1.name = "Third"
        mock_packet1._fields = []

        mock_packet2 = MagicMock(spec=ccsdspy.FixedLength)
        mock_packet2.__class__.__name__ = "Packet100"
        mock_packet2.__class__.__module__ = "ccsds.packets.test"
        mock_packet2.apid = 100
        mock_packet2.name = "First"
        mock_packet2._fields = []

        mock_packet3 = MagicMock(spec=ccsdspy.FixedLength)
        mock_packet3.__class__.__name__ = "Packet200"
        mock_packet3.__class__.__module__ = "ccsds.packets.test"
        mock_packet3.apid = 200
        mock_packet3.name = "Second"
        mock_packet3._fields = []

        # Pass in unsorted order
        with patch("spac_kit.parser.spac_ls.import_ccsds_packet_packages",
                   return_value=[mock_packet1, mock_packet2, mock_packet3]):
            result = list_packages(verbose=False, delimiter="|")

            assert result == 0
            captured = capsys.readouterr()
            lines = captured.out.strip().split('\n')

            # Check sorting (skip header)
            assert "100|" in lines[1]
            assert "200|" in lines[2]
            assert "300|" in lines[3]

    def test_list_packages_with_delimiter_empty_name(self, capsys):
        """Test list_packages with delimiter when packet has no name."""
        mock_packet = MagicMock(spec=ccsdspy.FixedLength)
        mock_packet.__class__.__name__ = "NoNamePacket"
        mock_packet.__class__.__module__ = "ccsds.packets.test"
        mock_packet.apid = 400
        if hasattr(mock_packet, 'name'):
            delattr(mock_packet, 'name')
        mock_packet._fields = []

        with patch("spac_kit.parser.spac_ls.import_ccsds_packet_packages", return_value=[mock_packet]):
            result = list_packages(verbose=False, delimiter=",")

            assert result == 0
            captured = capsys.readouterr()
            lines = captured.out.strip().split('\n')

            # Empty name should result in empty field
            assert lines[1] == "400,NoNamePacket,0,"


class TestMain:
    """Tests for main CLI entry point."""

    def test_main_with_no_arguments(self):
        """Test main function with no arguments (default behavior)."""
        mock_packet = MagicMock(spec=ccsdspy.FixedLength)
        mock_packet.__class__.__name__ = "TestPacket"
        mock_packet.__class__.__module__ = "ccsds.packets.test"
        mock_packet.apid = 100
        mock_packet.name = "Test"
        mock_packet._fields = []

        with patch("spac_kit.parser.spac_ls.import_ccsds_packet_packages", return_value=[mock_packet]):
            with patch("sys.argv", ["spac-ls"]):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 0

    def test_main_with_verbose_flag(self):
        """Test main function with verbose flag."""
        mock_packet = MagicMock(spec=ccsdspy.FixedLength)
        mock_packet.__class__.__name__ = "TestPacket"
        mock_packet.__class__.__module__ = "ccsds.packets.test"
        mock_packet.apid = 100
        mock_packet.name = "Test"
        mock_packet._fields = []

        with patch("spac_kit.parser.spac_ls.import_ccsds_packet_packages", return_value=[mock_packet]):
            with patch("sys.argv", ["spac-ls", "-v"]):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 0

    def test_main_with_verbose_long_flag(self):
        """Test main function with verbose long flag."""
        mock_packet = MagicMock(spec=ccsdspy.FixedLength)
        mock_packet.__class__.__name__ = "TestPacket"
        mock_packet.__class__.__module__ = "ccsds.packets.test"
        mock_packet.apid = 100
        mock_packet.name = "Test"
        mock_packet._fields = []

        with patch("spac_kit.parser.spac_ls.import_ccsds_packet_packages", return_value=[mock_packet]):
            with patch("sys.argv", ["spac-ls", "--verbose"]):
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
        mock_packet = MagicMock(spec=ccsdspy.FixedLength)
        mock_packet.__class__.__name__ = "TestPacket"
        mock_packet.__class__.__module__ = "ccsds.packets.test"
        mock_packet.apid = 100
        mock_packet.name = "Test"
        mock_packet._fields = []

        with patch("spac_kit.parser.spac_ls.import_ccsds_packet_packages", return_value=[mock_packet]):
            with patch("sys.argv", ["spac-ls", "-d", ","]):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 0

    def test_main_with_delimiter_and_verbose(self):
        """Test main function with both delimiter and verbose flags."""
        mock_packet = MagicMock(spec=ccsdspy.FixedLength)
        mock_packet.__class__.__name__ = "TestPacket"
        mock_packet.__class__.__module__ = "ccsds.packets.test"
        mock_packet.apid = 100
        mock_packet.name = "Test"
        mock_packet._fields = []

        with patch("spac_kit.parser.spac_ls.import_ccsds_packet_packages", return_value=[mock_packet]):
            with patch("sys.argv", ["spac-ls", "-v", "--delimiter", "\t"]):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 0
