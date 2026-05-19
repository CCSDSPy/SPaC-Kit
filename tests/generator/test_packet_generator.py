"""Unit tests for packet generator."""
import io

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

        # Verify packet was written (6-byte header + 3 bytes data)
        assert len(written_data) == 6 + 3

        # Verify by parsing back with ccsdspy
        file_obj.seek(0)
        parsed = packet.load(file_obj, include_primary_header=True)

        assert len(parsed["field1"]) == 1
        assert parsed["field1"][0] == 0
        assert parsed["field2"][0] == 0
        assert parsed["CCSDS_APID"][0] == 100
        assert parsed["CCSDS_SEQUENCE_COUNT"][0] == 0

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

        # Verify by parsing back with ccsdspy
        file_obj.seek(0)
        parsed = packet.load(file_obj, include_primary_header=True)

        assert len(parsed["data"]) == 3
        # Verify all data is zero
        assert np.all(parsed["data"] == 0)
        # Verify sequence counts
        assert np.array_equal(parsed["CCSDS_SEQUENCE_COUNT"], [0, 1, 2])
        # Verify APID
        assert np.all(parsed["CCSDS_APID"] == 100)

    def test_write_packet_with_array_fields(self):
        """Test writing packets with array fields."""
        fields = [
            ccsdspy.PacketField(name="header", data_type="uint", bit_length=8),
            ccsdspy.PacketArray(
                name="array_data", data_type="uint", bit_length=8, array_shape=5
            ),
            ccsdspy.PacketField(name="footer", data_type="uint", bit_length=16),
        ]
        packet = ccsdspy.VariableLength(fields, apid=200, name="ArrayPacket")
        generator = PacketGenerator(packet)

        file_obj = io.BytesIO()
        generator.write_packet(file_obj, count=2)

        # Verify by parsing back with ccsdspy
        file_obj.seek(0)
        parsed = packet.load(file_obj, include_primary_header=True)

        assert len(parsed["header"]) == 2
        assert len(parsed["array_data"]) == 2
        assert len(parsed["footer"]) == 2
        # Verify all data is zero
        assert np.all(parsed["header"] == 0)
        assert np.all(parsed["array_data"] == 0)
        assert np.all(parsed["footer"] == 0)
        # Verify array shape
        assert parsed["array_data"][0].shape == (5,)

    def test_write_packet_with_float_fields(self):
        """Test writing packets with float fields."""
        fields = [
            ccsdspy.PacketField(name="temperature", data_type="float", bit_length=32),
            ccsdspy.PacketField(name="pressure", data_type="float", bit_length=32),
        ]
        packet = ccsdspy.VariableLength(fields, apid=300, name="SensorPacket")
        generator = PacketGenerator(packet)

        file_obj = io.BytesIO()
        generator.write_packet(file_obj, count=2)

        # Verify by parsing back with ccsdspy
        file_obj.seek(0)
        parsed = packet.load(file_obj, include_primary_header=True)

        assert len(parsed["temperature"]) == 2
        assert len(parsed["pressure"]) == 2
        # Verify all data is zero
        assert np.all(parsed["temperature"] == 0.0)
        assert np.all(parsed["pressure"] == 0.0)

    def test_different_apids(self):
        """Test packet generation for different APIDs."""
        for apid in [0, 100, 500, 2047]:
            fields = [ccsdspy.PacketField(name="data", data_type="uint", bit_length=8)]
            packet = ccsdspy.VariableLength(fields, apid=apid, name=f"Test{apid}")
            generator = PacketGenerator(packet)

            file_obj = io.BytesIO()
            generator.write_packet(file_obj)

            # Verify by parsing back with ccsdspy
            file_obj.seek(0)
            parsed = packet.load(file_obj, include_primary_header=True)

            assert parsed["CCSDS_APID"][0] == apid

    def test_empty_packet(self):
        """Test writing packets with no data fields."""
        fields = []
        packet = ccsdspy.VariableLength(fields, apid=100, name="EmptyPacket")
        generator = PacketGenerator(packet)

        file_obj = io.BytesIO()
        generator.write_packet(file_obj)

        file_obj.seek(0)
        written_data = file_obj.read()

        # 6-byte header + 1 byte padding (ccsdspy requires at least 1 byte of data)
        assert len(written_data) == 7

        # Verify by parsing back with ccsdspy
        file_obj.seek(0)
        parsed = packet.load(file_obj, include_primary_header=True)

        assert len(parsed["CCSDS_APID"]) == 1
        assert parsed["CCSDS_APID"][0] == 100

    def test_create_zero_data_dict(self):
        """Test zero data dictionary creation."""
        fields = [
            ccsdspy.PacketField(name="scalar", data_type="uint", bit_length=8),
            ccsdspy.PacketArray(
                name="fixed_array", data_type="uint", bit_length=16, array_shape=3
            ),
        ]
        packet = ccsdspy.VariableLength(fields, apid=100, name="Test")
        generator = PacketGenerator(packet)

        data_dict = generator._create_zero_data_dict(count=2)

        # Check scalar field
        assert "scalar" in data_dict
        assert data_dict["scalar"].shape == (2,)
        assert np.all(data_dict["scalar"] == 0)

        # Check array field
        assert "fixed_array" in data_dict
        assert data_dict["fixed_array"].shape == (2, 3)
        assert np.all(data_dict["fixed_array"] == 0)
