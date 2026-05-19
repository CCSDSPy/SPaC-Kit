"""Unit tests for packet generator CLI."""
import io
import sys
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from spac_kit.generator.cli import main


class TestCLI:
    """Tests for CLI functionality."""

    @patch("spac_kit.generator.cli.import_ccsds_packet_packages")
    def test_no_packets_error(self, mock_import, capsys):
        """Test error when no packets are found."""
        mock_import.return_value = []

        with patch.object(sys, "argv", ["cli", "--output", "test.bin"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "No packet definitions found" in captured.err
        assert "spac-ls" in captured.err

    @patch("spac_kit.generator.cli.import_ccsds_packet_packages")
    @patch("builtins.open")
    def test_generate_all_packets(self, mock_open, mock_import, capsys):
        """Test generating packets for all APIDs."""
        mock_packet = MagicMock()
        mock_packet.apid = 100
        mock_packet.name = "TestPacket"
        mock_packet._fields = []

        mock_import.return_value = [
            {
                "packet": mock_packet,
                "variable_name": "test1",
                "module_path": "test.module",
            }
        ]

        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        with patch.object(sys, "argv", ["cli", "--output", "test.bin"]):
            main()

        captured = capsys.readouterr()
        assert "Success!" in captured.out
        assert "test.bin" in captured.out

    @patch("spac_kit.generator.cli.import_ccsds_packet_packages")
    @patch("builtins.open")
    def test_generate_specific_apid(self, mock_open, mock_import, capsys):
        """Test generating packets for specific APID."""
        mock_packet1 = MagicMock()
        mock_packet1.apid = 100
        mock_packet1.name = "TestPacket1"
        mock_packet1._fields = []

        mock_packet2 = MagicMock()
        mock_packet2.apid = 200
        mock_packet2.name = "TestPacket2"
        mock_packet2._fields = []

        mock_import.return_value = [
            {
                "packet": mock_packet1,
                "variable_name": "test1",
                "module_path": "test.module1",
            },
            {
                "packet": mock_packet2,
                "variable_name": "test2",
                "module_path": "test.module2",
            },
        ]

        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        with patch.object(
            sys, "argv", ["cli", "--output", "test.bin", "--apid", "100"]
        ):
            main()

        captured = capsys.readouterr()
        assert "APID 100" in captured.out

    @patch("spac_kit.generator.cli.import_ccsds_packet_packages")
    @patch("builtins.open")
    def test_generate_multiple_packets_per_apid(self, mock_open, mock_import, capsys):
        """Test generating multiple packets per APID."""
        mock_packet = MagicMock()
        mock_packet.apid = 100
        mock_packet.name = "TestPacket"
        mock_packet._fields = []

        mock_import.return_value = [
            {
                "packet": mock_packet,
                "variable_name": "test1",
                "module_path": "test.module",
            }
        ]

        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        with patch.object(sys, "argv", ["cli", "--output", "test.bin", "--count", "5"]):
            main()

        captured = capsys.readouterr()
        assert "5 packet(s)" in captured.out

    @patch("spac_kit.generator.cli.import_ccsds_packet_packages")
    def test_invalid_apid(self, mock_import, capsys):
        """Test error when requesting non-existent APID."""
        mock_packet = MagicMock()
        mock_packet.apid = 100
        mock_packet.name = "TestPacket"
        mock_packet._fields = []

        mock_import.return_value = [
            {
                "packet": mock_packet,
                "variable_name": "test1",
                "module_path": "test.module",
            }
        ]

        with patch.object(
            sys, "argv", ["cli", "--output", "test.bin", "--apid", "999"]
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "No packets found" in captured.err

    @patch("spac_kit.generator.cli.import_ccsds_packet_packages")
    def test_import_error(self, mock_import, capsys):
        """Test handling of import errors."""
        mock_import.side_effect = ImportError("No module found")

        with patch.object(sys, "argv", ["cli", "--output", "test.bin"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "No CCSDS packet definitions found" in captured.err

    @patch("spac_kit.generator.cli.import_ccsds_packet_packages")
    @patch("builtins.open")
    def test_generate_with_zeros_flag(self, mock_open, mock_import, capsys):
        """Test generating packets with --zeros flag."""
        mock_packet = MagicMock()
        mock_packet.apid = 100
        mock_packet.name = "TestPacket"
        mock_packet._fields = []

        mock_import.return_value = [
            {
                "packet": mock_packet,
                "variable_name": "test1",
                "module_path": "test.module",
            }
        ]

        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        with patch.object(sys, "argv", ["cli", "--output", "test.bin", "--zeros"]):
            main()

        captured = capsys.readouterr()
        assert "Success!" in captured.out
        assert "test.bin" in captured.out

    @patch("spac_kit.generator.cli.import_ccsds_packet_packages")
    @patch("builtins.open")
    def test_generate_multiple_apids(self, mock_open, mock_import, capsys):
        """Test generating packets for multiple specific APIDs."""
        mock_packet1 = MagicMock()
        mock_packet1.apid = 100
        mock_packet1.name = "TestPacket1"
        mock_packet1._fields = []

        mock_packet2 = MagicMock()
        mock_packet2.apid = 200
        mock_packet2.name = "TestPacket2"
        mock_packet2._fields = []

        mock_packet3 = MagicMock()
        mock_packet3.apid = 300
        mock_packet3.name = "TestPacket3"
        mock_packet3._fields = []

        mock_import.return_value = [
            {
                "packet": mock_packet1,
                "variable_name": "test1",
                "module_path": "test.module1",
            },
            {
                "packet": mock_packet2,
                "variable_name": "test2",
                "module_path": "test.module2",
            },
            {
                "packet": mock_packet3,
                "variable_name": "test3",
                "module_path": "test.module3",
            },
        ]

        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        with patch.object(
            sys, "argv", ["cli", "--output", "test.bin", "--apid", "100", "300"]
        ):
            main()

        captured = capsys.readouterr()
        # Should generate for APID 100 and 300
        assert "APID 100" in captured.out
        assert "APID 300" in captured.out
        # Should NOT generate for APID 200
        assert "APID 200" not in captured.out
        assert "Success!" in captured.out
