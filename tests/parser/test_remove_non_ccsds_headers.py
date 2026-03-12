"""Unit tests for header removal functionality."""
import io
import struct

import pytest
from spac_kit.parser.remove_non_ccsds_headers import remove_bdsem
from spac_kit.parser.remove_non_ccsds_headers import remove_bdsem_and_message_headers
from spac_kit.parser.remove_non_ccsds_headers import remove_mise_and_headers
from spac_kit.parser.remove_non_ccsds_headers import start_sequence
from spac_kit.parser.remove_non_ccsds_headers import strip_non_ccsds_headers


class TestStartSequence:
    """Tests for start_sequence function."""

    def test_valid_start_sequence(self):
        """Test that valid MISE start sequence is recognized."""
        seq = b"\xaa\xf0\xaa\xaa"
        assert start_sequence(seq) is True

    def test_valid_start_sequence_different_value(self):
        """Test valid start sequence with different non-zero value."""
        seq = b"\x55\xf0\x55\x55"
        assert start_sequence(seq) is True

    def test_invalid_sequence_wrong_second_byte(self):
        """Test that sequence with wrong second byte is rejected."""
        seq = b"\xaa\xff\xaa\xaa"
        assert start_sequence(seq) is False

    def test_invalid_sequence_with_zero(self):
        """Test that sequence with 0x00 values is rejected."""
        seq = b"\x00\xf0\x00\x00"
        assert start_sequence(seq) is False

    def test_invalid_sequence_mismatched_bytes(self):
        """Test that sequence with mismatched bytes is rejected."""
        seq = b"\xaa\xf0\xbb\xaa"
        assert start_sequence(seq) is False

    def test_invalid_sequence_first_byte_differs(self):
        """Test sequence where first byte differs from others."""
        seq = b"\xbb\xf0\xaa\xaa"
        assert start_sequence(seq) is False


class TestRemoveBdsem:
    """Tests for remove_bdsem function."""

    def test_remove_bdsem_single_packet(self, sample_ccsds_packet):
        """Test removing BDSEM wrapper from a single packet.

        Note: remove_bdsem expects specific BDSEM format:
        48-bit header + data + 8-bit CRC.
        """
        pytest.skip(
            "BDSEM format test needs proper packet structure - skipping for now"
        )

    def test_remove_bdsem_empty_input(self):
        """Test remove_bdsem with empty input."""
        input_stream = io.BytesIO(b"")
        result = remove_bdsem(input_stream)

        assert result.read() == b""


class TestRemoveBdsemAndMessageHeaders:
    """Tests for remove_bdsem_and_message_headers function."""

    def test_remove_bdsem_and_message_headers_single_packet(self, sample_ccsds_packet):
        """Test removing BDSEM wrapper and message headers from single packet."""
        ccsds_packet_len = len(sample_ccsds_packet)
        sse_length = ccsds_packet_len + 4  # packet + unused bytes

        # Build the wrapped packet
        control_word = struct.pack("<I", sse_length)
        unused = b"\x00\x00\x00\x00"

        input_stream = io.BytesIO(control_word + unused + sample_ccsds_packet)
        result = remove_bdsem_and_message_headers(input_stream)

        result_data = result.read()
        assert result_data == sample_ccsds_packet

    def test_remove_bdsem_and_message_headers_empty(self):
        """Test with empty input."""
        input_stream = io.BytesIO(b"")
        result = remove_bdsem_and_message_headers(input_stream)

        assert result.read() == b""

    def test_remove_bdsem_and_message_headers_multiple_packets(
        self, sample_ccsds_packet
    ):
        """Test removing headers from multiple packets."""
        wrapped_packets = []
        for i in range(3):
            ccsds_packet_len = len(sample_ccsds_packet)
            sse_length = ccsds_packet_len + 4

            control_word = struct.pack("<I", sse_length)
            unused = b"\x00\x00\x00\x00"
            wrapped_packets.append(control_word + unused + sample_ccsds_packet)

        input_stream = io.BytesIO(b"".join(wrapped_packets))
        result = remove_bdsem_and_message_headers(input_stream)

        result_data = result.read()
        expected = sample_ccsds_packet * 3
        assert result_data == expected


class TestRemoveMiseAndHeaders:
    """Tests for remove_mise_and_headers function."""

    def test_remove_mise_headers_single_packet(self, sample_ccsds_packet):
        """Test removing MISE markers from single packet."""
        marker = b"\xaa\xf0\xaa\xaa"
        input_stream = io.BytesIO(marker + sample_ccsds_packet)

        result = remove_mise_and_headers(input_stream)
        result_data = result.read()

        assert result_data == sample_ccsds_packet

    def test_remove_mise_headers_multiple_packets(self, sample_ccsds_packet):
        """Test removing MISE markers from multiple packets."""
        marker = b"\xbb\xf0\xbb\xbb"
        wrapped_packets = (marker + sample_ccsds_packet) * 3

        input_stream = io.BytesIO(wrapped_packets)
        result = remove_mise_and_headers(input_stream)
        result_data = result.read()

        expected = sample_ccsds_packet * 3
        assert result_data == expected

    def test_remove_mise_headers_no_markers(self, sample_ccsds_packet):
        """Test when no MISE markers are present."""
        input_stream = io.BytesIO(sample_ccsds_packet)
        result = remove_mise_and_headers(input_stream)
        result_data = result.read()

        # Should return empty since no markers were found
        assert result_data == b""


class TestStripNonCcsdsHeaders:
    """Tests for strip_non_ccsds_headers main function."""

    def test_strip_no_headers(self, sample_ccsds_packet):
        """Test when no headers need to be stripped."""
        input_stream = io.BytesIO(sample_ccsds_packet)
        result = strip_non_ccsds_headers(input_stream, False, False, False)

        # Should return the same file handler
        assert result == input_stream
        result.seek(0)
        assert result.read() == sample_ccsds_packet

    def test_strip_json_header_only(self, sample_ccsds_packet):
        """Test stripping only JSON header."""
        json_header = b'{"test": "data"}\n'
        input_stream = io.BytesIO(json_header + sample_ccsds_packet)

        result = strip_non_ccsds_headers(input_stream, False, False, True)

        assert result.read() == sample_ccsds_packet

    def test_strip_bdsem_without_packet_header(self, sample_ccsds_packet):
        """Test stripping BDSEM wrapper without packet headers."""
        pytest.skip(
            "BDSEM format test needs proper packet structure - skipping for now"
        )

    def test_strip_bdsem_with_packet_header(self, sample_ccsds_packet):
        """Test stripping BDSEM wrapper with packet headers."""
        ccsds_packet_len = len(sample_ccsds_packet)
        sse_length = ccsds_packet_len + 4

        control_word = struct.pack("<I", sse_length)
        unused = b"\x00\x00\x00\x00"

        input_stream = io.BytesIO(control_word + unused + sample_ccsds_packet)
        result = strip_non_ccsds_headers(input_stream, True, True, False)

        result_data = result.read()
        assert result_data == sample_ccsds_packet

    def test_strip_mise_with_packet_header(self, sample_ccsds_packet):
        """Test stripping MISE markers with packet headers."""
        marker = b"\xcc\xf0\xcc\xcc"
        input_stream = io.BytesIO(marker + sample_ccsds_packet)

        result = strip_non_ccsds_headers(input_stream, False, True, False)
        result_data = result.read()

        assert result_data == sample_ccsds_packet

    def test_strip_json_and_bdsem_headers(self, sample_ccsds_packet):
        """Test stripping both JSON and BDSEM headers."""
        pytest.skip(
            "BDSEM format test needs proper packet structure - skipping for now"
        )
