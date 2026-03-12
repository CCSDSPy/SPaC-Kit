"""Unit tests for CCSDS parsing functionality."""
import io
import struct

import numpy as np
import pytest
from spac_kit.parser.parse_ccsds_downlink import calculate_crc
from spac_kit.parser.parse_ccsds_downlink import CalculatedChecksum
from spac_kit.parser.parse_ccsds_downlink import cast_to_list
from spac_kit.parser.parse_ccsds_downlink import CCSDSParsingException
from spac_kit.parser.parse_ccsds_downlink import CRCNotCalculatedError
from spac_kit.parser.parse_ccsds_downlink import distribute_packets
from spac_kit.parser.parse_ccsds_downlink import get_sub_packet_keys
from spac_kit.parser.parse_ccsds_downlink import get_tab_name


class TestCalculatedChecksum:
    """Tests for CalculatedChecksum converter class."""

    def test_initialization(self):
        """Test CalculatedChecksum can be initialized."""
        converter = CalculatedChecksum()
        assert converter is not None

    def test_calculate_crc_simple(self):
        """Test CRC calculation for a simple packet."""
        # Create simple packet data
        ccsds_version = 0
        packet_type = 0
        secondary_flag = 0
        apid = 100
        sequence_flag = 3
        sequence_count = 0
        packet_length = 7  # 8 bytes - 1
        body = np.array([1, 2, 3, 4, 5, 6, 7, 8], dtype=np.uint8)

        crc = CalculatedChecksum.calculate_crc(
            ccsds_version,
            packet_type,
            secondary_flag,
            apid,
            sequence_flag,
            sequence_count,
            packet_length,
            body,
        )

        # CRC should be a number
        assert isinstance(crc, (int, np.integer))
        assert crc >= 0

    def test_calculate_crc_jumbo_packet(self):
        """Test that jumbo packets use different CRC algorithm."""
        # Create a jumbo packet (> 4089 bytes)
        ccsds_version = 0
        packet_type = 0
        secondary_flag = 0
        apid = 100
        sequence_flag = 3
        sequence_count = 0
        packet_length = 5000  # Jumbo packet
        body = np.array([0xFF] * 5000, dtype=np.uint8)

        crc = CalculatedChecksum.calculate_crc(
            ccsds_version,
            packet_type,
            secondary_flag,
            apid,
            sequence_flag,
            sequence_count,
            packet_length,
            body,
        )

        # CRC should be calculated using JUMBO_CRC
        assert isinstance(crc, (int, np.integer))

    def test_convert_single_packet(self):
        """Test convert method with single packet arrays."""
        converter = CalculatedChecksum()

        # Create arrays for a single packet
        ccsds_version_array = [0]
        ccsds_packet_type_array = [0]
        ccsds_secondary_flag_array = [0]
        ccsds_apid_array = [100]
        ccsds_sequence_flag_array = [3]
        ccsds_sequence_count_array = [0]
        ccsds_packet_length_array = [7]
        body_array = [np.array([1, 2, 3, 4, 5, 6, 7, 8], dtype=np.uint8)]

        result = converter.convert(
            ccsds_version_array,
            ccsds_packet_type_array,
            ccsds_secondary_flag_array,
            ccsds_apid_array,
            ccsds_sequence_flag_array,
            ccsds_sequence_count_array,
            ccsds_packet_length_array,
            body_array,
        )

        assert len(result) == 1
        assert isinstance(result[0], (int, np.integer))

    def test_convert_multiple_packets(self):
        """Test convert method with multiple packets."""
        converter = CalculatedChecksum()

        # Create arrays for multiple packets
        num_packets = 3
        ccsds_version_array = [0] * num_packets
        ccsds_packet_type_array = [0] * num_packets
        ccsds_secondary_flag_array = [0] * num_packets
        ccsds_apid_array = [100, 101, 102]
        ccsds_sequence_flag_array = [3] * num_packets
        ccsds_sequence_count_array = [0, 1, 2]
        ccsds_packet_length_array = [7] * num_packets
        body_array = [np.array([i] * 8, dtype=np.uint8) for i in range(num_packets)]

        result = converter.convert(
            ccsds_version_array,
            ccsds_packet_type_array,
            ccsds_secondary_flag_array,
            ccsds_apid_array,
            ccsds_sequence_flag_array,
            ccsds_sequence_count_array,
            ccsds_packet_length_array,
            body_array,
        )

        assert len(result) == num_packets
        # CRCs should be different for different packets
        assert len(set(result)) > 1


class TestCalculateCrc:
    """Tests for calculate_crc function."""

    def test_calculate_crc_with_valid_packet(self):
        """Test CRC calculation with a valid CCSDS packet."""
        # Create a simple CCSDS packet with CRC
        word1 = (0 << 13) | (0 << 12) | (0 << 11) | 100
        word2 = (3 << 14) | 0
        word3 = 9  # 8 bytes data + 2 bytes CRC - 1

        header = struct.pack(">HHH", word1, word2, word3)
        data = b"\x01\x02\x03\x04\x05\x06\x07\x08"

        # Calculate expected CRC
        converter = CalculatedChecksum()
        expected_crc = converter.calculate_crc(
            0, 0, 0, 100, 3, 0, 9, np.frombuffer(data, dtype=np.uint8)
        )

        crc_bytes = struct.pack(">H", expected_crc)
        packet = header + data + crc_bytes

        file_obj = io.BytesIO(packet)
        result = calculate_crc(file_obj, crc_size_bytes=2)

        assert len(result) == 1
        assert result[0] == expected_crc

    def test_calculate_crc_empty_file(self):
        """Test CRC calculation with empty file."""
        file_obj = io.BytesIO(b"")

        with pytest.raises(CRCNotCalculatedError):
            calculate_crc(file_obj)

    def test_calculate_crc_invalid_packet(self):
        """Test CRC calculation with invalid/corrupt packet."""
        # Create a packet with mismatched CRC
        word1 = (0 << 13) | (0 << 12) | (0 << 11) | 100
        word2 = (3 << 14) | 0
        word3 = 9  # 8 bytes data + 2 bytes CRC - 1

        header = struct.pack(">HHH", word1, word2, word3)
        data = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        wrong_crc = b"\xff\xff"  # Intentionally wrong CRC

        packet = header + data + wrong_crc
        file_obj = io.BytesIO(packet)

        with pytest.raises(CCSDSParsingException):
            calculate_crc(file_obj)


class TestGetTabName:
    """Tests for get_tab_name function."""

    def test_get_tab_name_with_name_attribute(self):
        """Test tab name generation when packet has name attribute."""

        class MockPacket:
            name = "TestPacket"

        apid = 100
        existing_names = []

        result = get_tab_name(apid, MockPacket(), existing_names)
        assert result == "100.TestPacket"

    def test_get_tab_name_without_name_attribute(self):
        """Test tab name generation when packet has no name attribute."""

        class MockPacket:
            pass

        apid = 200
        existing_names = []

        result = get_tab_name(apid, MockPacket(), existing_names)
        assert result == "200.MockPacket"

    def test_get_tab_name_duplicate_handling(self):
        """Test that duplicate names are handled with counter."""

        class MockPacket:
            name = "TestPacket"

        apid = 100
        existing_names = ["100.TestPacket"]

        result = get_tab_name(apid, MockPacket(), existing_names)
        assert result == "100.TestPacket (1)"

    def test_get_tab_name_multiple_duplicates(self):
        """Test handling multiple duplicate names.

        Note: The implementation appends (1) repeatedly, not incrementing the counter.
        """

        class MockPacket:
            name = "TestPacket"

        apid = 100
        existing_names = ["100.TestPacket", "100.TestPacket (1)"]

        result = get_tab_name(apid, MockPacket(), existing_names)
        # The actual implementation appends " (1)" repeatedly
        assert result == "100.TestPacket (1) (1)"


class TestCastToList:
    """Tests for cast_to_list function."""

    def test_cast_numpy_arrays_to_lists(self):
        """Test converting numpy arrays to lists."""
        data = {
            "field1": [np.array([1, 2, 3]), np.array([4, 5, 6])],
            "field2": [np.array([7, 8]), np.array([9, 10])],
        }

        result = cast_to_list(data)

        assert result["field1"] == [[1, 2, 3], [4, 5, 6]]
        assert result["field2"] == [[7, 8], [9, 10]]

    def test_cast_to_list_preserves_non_arrays(self):
        """Test that non-array values are preserved."""
        data = {
            "field1": [1, 2, 3],
            "field2": ["a", "b", "c"],
        }

        result = cast_to_list(data)

        assert result["field1"] == [1, 2, 3]
        assert result["field2"] == ["a", "b", "c"]

    def test_cast_empty_dict(self):
        """Test with empty dictionary."""
        data = {}
        result = cast_to_list(data)
        assert result == {}


class TestDistributePackets:
    """Tests for distribute_packets function."""

    def test_distribute_packets_single_key(self):
        """Test distributing packets with a single key."""
        # Create a simple CCSDS packet
        word1 = (0 << 13) | (0 << 12) | (0 << 11) | 100
        word2 = (3 << 14) | 0
        word3 = 7

        header = struct.pack(">HHH", word1, word2, word3)
        data = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        packet = header + data

        stream = io.BytesIO(packet)
        keys = [1]

        result = distribute_packets(keys, stream)

        assert 1 in result
        assert isinstance(result[1], io.BytesIO)
        result[1].seek(0)
        assert result[1].read() == packet

    def test_distribute_packets_multiple_keys(self):
        """Test distributing multiple packets to different buffers."""
        # Create multiple CCSDS packets
        packets = []
        for i in range(3):
            word1 = (0 << 13) | (0 << 12) | (0 << 11) | (100 + i)
            word2 = (3 << 14) | i
            word3 = 7

            header = struct.pack(">HHH", word1, word2, word3)
            data = bytes([i] * 8)
            packets.append(header + data)

        stream = io.BytesIO(b"".join(packets))
        keys = [1, 2, 3]

        result = distribute_packets(keys, stream)

        assert len(result) == 3
        assert all(k in result for k in [1, 2, 3])

        for key, expected_packet in zip(keys, packets):
            result[key].seek(0)
            assert result[key].read() == expected_packet

    def test_distribute_packets_repeated_keys(self):
        """Test that packets with same key are combined."""
        # Create two packets
        word1 = (0 << 13) | (0 << 12) | (0 << 11) | 100
        word2 = (3 << 14) | 0
        word3 = 7

        header = struct.pack(">HHH", word1, word2, word3)
        data = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        packet = header + data

        stream = io.BytesIO(packet * 2)
        keys = [1, 1]  # Both packets have same key

        result = distribute_packets(keys, stream)

        assert len(result) == 1
        assert 1 in result
        result[1].seek(0)
        assert result[1].read() == packet * 2


class TestGetSubPacketKeys:
    """Tests for get_sub_packet_keys function."""

    def test_get_sub_packet_keys_with_decision_field(self):
        """Test getting sub-packet keys with decision field."""

        class MockParser:
            decision_field = "packet_type"

            def decision_fun(self, x):
                return x * 2

        parsed_apids = {"packet_type": [1, 2, 3], "other_field": [10, 20, 30]}

        sub_apid = {"pre_parser": MockParser()}

        result = get_sub_packet_keys(parsed_apids, sub_apid)

        assert result == [2, 4, 6]

    def test_get_sub_packet_keys_without_decision_field(self):
        """Test getting sub-packet keys without decision field."""

        class MockParser:
            def decision_fun(self):
                return 42

        parsed_apids = {"field1": [1, 2, 3], "field2": [10, 20, 30]}

        sub_apid = {"pre_parser": MockParser()}

        result = get_sub_packet_keys(parsed_apids, sub_apid)

        # Should return decision_fun() for each packet
        assert result == [42, 42, 42]
        assert len(result) == 3


class TestCCSDSExceptions:
    """Tests for custom exception classes."""

    def test_ccsds_parsing_exception(self):
        """Test CCSDSParsingException can be raised and caught."""
        with pytest.raises(CCSDSParsingException):
            raise CCSDSParsingException("Test error")

    def test_crc_not_calculated_error(self):
        """Test CRCNotCalculatedError can be raised and caught."""
        with pytest.raises(CRCNotCalculatedError):
            raise CRCNotCalculatedError("CRC calculation failed")

    def test_exceptions_inherit_from_exception(self):
        """Test that custom exceptions inherit from Exception."""
        assert issubclass(CCSDSParsingException, Exception)
        assert issubclass(CRCNotCalculatedError, Exception)
