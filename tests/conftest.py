"""Pytest configuration and shared fixtures."""
import io
import struct

import pytest


@pytest.fixture
def sample_ccsds_packet():
    """Create a sample CCSDS packet for testing.

    CCSDS Primary Header (6 bytes):
    - Version (3 bits): 0
    - Type (1 bit): 0 (telemetry)
    - Secondary Header Flag (1 bit): 0
    - APID (11 bits): 100
    - Sequence Flags (2 bits): 3 (standalone packet)
    - Sequence Count (14 bits): 0
    - Packet Length (16 bits): 7 (8 bytes of data - 1)

    Data: 8 bytes of test data
    """
    # Build CCSDS header
    # First 16 bits: version(3) + type(1) + sec_hdr(1) + apid(11)
    word1 = (0 << 13) | (0 << 12) | (0 << 11) | 100
    # Second 16 bits: seq_flags(2) + seq_count(14)
    word2 = (3 << 14) | 0
    # Third 16 bits: packet length (data bytes - 1)
    word3 = 7

    header = struct.pack(">HHH", word1, word2, word3)
    data = b"\x01\x02\x03\x04\x05\x06\x07\x08"

    return header + data


@pytest.fixture
def sample_ccsds_file_multiple_apids(sample_ccsds_packet):
    """Create a binary file with multiple CCSDS packets with different APIDs."""
    packets = []

    # Create packets with different APIDs
    for apid in [100, 101, 102]:
        word1 = (0 << 13) | (0 << 12) | (0 << 11) | apid
        word2 = (3 << 14) | 0
        word3 = 7

        header = struct.pack(">HHH", word1, word2, word3)
        data = bytes([apid % 256] * 8)
        packets.append(header + data)

    return io.BytesIO(b"".join(packets))


@pytest.fixture
def sample_bdsem_wrapped_packet(sample_ccsds_packet):
    """Create a BDSEM-wrapped CCSDS packet for testing header removal."""
    # BDSEM wrapper structure:
    # - Control word (4 bytes, little-endian): packet length including unused bytes
    # - Unused (4 bytes)
    # - CCSDS packet data
    # - CRC (1 byte)

    ccsds_packet_len = len(sample_ccsds_packet)
    sse_length = ccsds_packet_len + 4  # packet + unused bytes

    control_word = struct.pack("<I", sse_length)
    unused = b"\x00\x00\x00\x00"
    crc = b"\xaa"

    return io.BytesIO(control_word + unused + sample_ccsds_packet + crc)


@pytest.fixture
def sample_mise_wrapped_packet(sample_ccsds_packet):
    """Create a MISE-wrapped CCSDS packet for testing header removal."""
    # MISE wrapper: 4-byte marker before each packet
    # Format: [XX, 0xF0, XX, XX] where all bytes except byte 1 are the same and != 0x00
    marker = b"\xaa\xf0\xaa\xaa"

    return io.BytesIO(marker + sample_ccsds_packet)


@pytest.fixture
def sample_json_header_file(sample_ccsds_packet):
    """Create a file with JSON header followed by CCSDS packet."""
    json_header = b'{"mission": "test", "date": "2024-01-01"}\n'

    return io.BytesIO(json_header + sample_ccsds_packet)
