"""Unit tests for packet generator."""
import io
import struct

import ccsdspy
import numpy as np
import pytest
from spac_kit.generator.packet_generator import PacketGenerator


class TestPacketGenerator:
    """Tests for PacketGenerator class."""

    def test_initialization(self):
        """Test basic initialization of PacketGenerator."""
        fields = [
            ccsdspy.PacketField(name="field1", data_type="uint", bit_length=8),
            ccsdspy.PacketField(name="field2", data_type="uint", bit_length=16),
        ]
        packet = ccsdspy.VariableLength(fields, apid=100, name="TestPacket")
        generator = PacketGenerator(packet)

        assert generator.name == "TestPacket"
        assert generator.apid == 100

    def test_get_default_value_uint(self):
        """Test default value generation for uint fields."""
        fields = [ccsdspy.PacketField(name="data", data_type="uint", bit_length=8)]
        packet = ccsdspy.VariableLength(fields, apid=100, name="Test")
        generator = PacketGenerator(packet)

        field = fields[0]
        default = generator._get_default_value(field)
        assert default == 0

    def test_get_default_value_float(self):
        """Test default value generation for float fields."""
        fields = [ccsdspy.PacketField(name="data", data_type="float", bit_length=32)]
        packet = ccsdspy.VariableLength(fields, apid=100, name="Test")
        generator = PacketGenerator(packet)

        field = fields[0]
        default = generator._get_default_value(field)
        assert default == 0.0

    def test_get_default_value_array(self):
        """Test default value generation for array fields."""
        fields = [
            ccsdspy.PacketArray(
                name="data", data_type="uint", bit_length=8, array_shape=(3, 4)
            )
        ]
        packet = ccsdspy.VariableLength(fields, apid=100, name="Test")
        generator = PacketGenerator(packet)

        field = fields[0]
        default = generator._get_default_value(field)
        assert isinstance(default, np.ndarray)
        assert default.shape == (3, 4)
        assert np.all(default == 0)

    def test_generate_ccsds_header(self):
        """Test CCSDS header generation."""
        fields = [ccsdspy.PacketField(name="data", data_type="uint", bit_length=8)]
        packet = ccsdspy.VariableLength(fields, apid=100, name="Test")
        generator = PacketGenerator(packet)

        header = generator._generate_ccsds_header(
            apid=100, sequence_count=5, data_length=7
        )

        assert len(header) == 6
        word1, word2, word3 = struct.unpack(">HHH", header)

        version = (word1 >> 13) & 0x7
        packet_type = (word1 >> 12) & 0x1
        sec_hdr_flag = (word1 >> 11) & 0x1
        apid = word1 & 0x7FF

        assert version == 0
        assert packet_type == 0
        assert sec_hdr_flag == 0
        assert apid == 100

        seq_flags = (word2 >> 14) & 0x3
        seq_count = word2 & 0x3FFF
        assert seq_flags == 3
        assert seq_count == 5

        assert word3 == 7

    def test_generate_packet_simple(self):
        """Test packet generation with simple fields."""
        fields = [
            ccsdspy.PacketField(name="field1", data_type="uint", bit_length=8),
            ccsdspy.PacketField(name="field2", data_type="uint", bit_length=16),
        ]
        packet = ccsdspy.VariableLength(fields, apid=100, name="TestPacket")
        generator = PacketGenerator(packet)

        packet_bytes = generator.generate_packet()

        assert len(packet_bytes) == 6 + 3
        header = packet_bytes[:6]
        data = packet_bytes[6:]

        assert len(header) == 6
        assert len(data) == 3
        assert data == b"\x00\x00\x00"

    def test_generate_packet_with_sequence_count(self):
        """Test packet generation with specific sequence count."""
        fields = [ccsdspy.PacketField(name="data", data_type="uint", bit_length=8)]
        packet = ccsdspy.VariableLength(fields, apid=100, name="Test")
        generator = PacketGenerator(packet)

        packet_bytes = generator.generate_packet(sequence_count=42)

        header = packet_bytes[:6]
        word1, word2, word3 = struct.unpack(">HHH", header)

        seq_count = word2 & 0x3FFF
        assert seq_count == 42

    def test_write_single_packet(self):
        """Test writing a single packet to file."""
        fields = [
            ccsdspy.PacketField(name="field1", data_type="uint", bit_length=8),
            ccsdspy.PacketField(name="field2", data_type="uint", bit_length=16),
        ]
        packet = ccsdspy.VariableLength(fields, apid=100, name="TestPacket")
        generator = PacketGenerator(packet)

        file_obj = io.BytesIO()
        generator.write_packet(file_obj)

        file_obj.seek(0)
        written_data = file_obj.read()

        assert len(written_data) == 6 + 3

    def test_write_multiple_packets(self):
        """Test writing multiple packets with incrementing sequence counts."""
        fields = [ccsdspy.PacketField(name="data", data_type="uint", bit_length=8)]
        packet = ccsdspy.VariableLength(fields, apid=100, name="Test")
        generator = PacketGenerator(packet)

        file_obj = io.BytesIO()
        generator.write_packet(file_obj, count=3)

        file_obj.seek(0)
        written_data = file_obj.read()

        packet_size = 6 + 1
        assert len(written_data) == packet_size * 3

        for i in range(3):
            offset = i * packet_size
            header = written_data[offset : offset + 6]
            word1, word2, word3 = struct.unpack(">HHH", header)
            seq_count = word2 & 0x3FFF
            assert seq_count == i

    def test_calculate_field_bytes(self):
        """Test byte calculation for different field types."""
        fields = [ccsdspy.PacketField(name="data", data_type="uint", bit_length=8)]
        packet = ccsdspy.VariableLength(fields, apid=100, name="Test")
        generator = PacketGenerator(packet)

        field_8bit = ccsdspy.PacketField(name="f1", data_type="uint", bit_length=8)
        assert generator._calculate_field_bytes(field_8bit) == 1

        field_16bit = ccsdspy.PacketField(name="f2", data_type="uint", bit_length=16)
        assert generator._calculate_field_bytes(field_16bit) == 2

        field_32bit = ccsdspy.PacketField(name="f3", data_type="uint", bit_length=32)
        assert generator._calculate_field_bytes(field_32bit) == 4

    def test_calculate_field_bytes_array(self):
        """Test byte calculation for array fields."""
        fields = [
            ccsdspy.PacketArray(
                name="data", data_type="uint", bit_length=8, array_shape=(2, 3)
            )
        ]
        packet = ccsdspy.VariableLength(fields, apid=100, name="Test")
        generator = PacketGenerator(packet)

        assert generator._calculate_field_bytes(fields[0]) == 6

    def test_packet_with_array_fields(self):
        """Test packet generation with array fields."""
        fields = [
            ccsdspy.PacketField(name="header", data_type="uint", bit_length=8),
            ccsdspy.PacketArray(
                name="array_data", data_type="uint", bit_length=8, array_shape=5
            ),
            ccsdspy.PacketField(name="footer", data_type="uint", bit_length=16),
        ]
        packet = ccsdspy.VariableLength(fields, apid=200, name="ArrayPacket")
        generator = PacketGenerator(packet)

        packet_bytes = generator.generate_packet()

        header = packet_bytes[:6]
        data = packet_bytes[6:]

        assert len(data) == 1 + 5 + 2
        assert data == b"\x00" * 8

    def test_packet_with_float_fields(self):
        """Test packet generation with float fields."""
        fields = [
            ccsdspy.PacketField(name="temperature", data_type="float", bit_length=32),
            ccsdspy.PacketField(name="pressure", data_type="float", bit_length=32),
        ]
        packet = ccsdspy.VariableLength(fields, apid=300, name="SensorPacket")
        generator = PacketGenerator(packet)

        packet_bytes = generator.generate_packet()

        data = packet_bytes[6:]
        assert len(data) == 8
        assert data == b"\x00" * 8

    def test_different_apids(self):
        """Test packet generation for different APIDs."""
        for apid in [0, 100, 500, 2047]:
            fields = [ccsdspy.PacketField(name="data", data_type="uint", bit_length=8)]
            packet = ccsdspy.VariableLength(fields, apid=apid, name=f"Test{apid}")
            generator = PacketGenerator(packet)

            packet_bytes = generator.generate_packet()
            header = packet_bytes[:6]
            word1, word2, word3 = struct.unpack(">HHH", header)

            extracted_apid = word1 & 0x7FF
            assert extracted_apid == apid

    def test_packet_length_field(self):
        """Test that packet length field is correctly calculated."""
        fields = [
            ccsdspy.PacketField(name="data1", data_type="uint", bit_length=8),
            ccsdspy.PacketField(name="data2", data_type="uint", bit_length=16),
            ccsdspy.PacketField(name="data3", data_type="uint", bit_length=32),
        ]
        packet = ccsdspy.VariableLength(fields, apid=100, name="Test")
        generator = PacketGenerator(packet)

        packet_bytes = generator.generate_packet()

        header = packet_bytes[:6]
        word1, word2, word3 = struct.unpack(">HHH", header)

        data_length = len(packet_bytes) - 6 - 1
        assert word3 == data_length

    def test_empty_packet(self):
        """Test packet generation with no data fields."""
        fields = []
        packet = ccsdspy.VariableLength(fields, apid=100, name="EmptyPacket")
        generator = PacketGenerator(packet)

        packet_bytes = generator.generate_packet()

        assert len(packet_bytes) == 6

        header = packet_bytes[:6]
        word1, word2, word3 = struct.unpack(">HHH", header)
        assert word3 == 0
