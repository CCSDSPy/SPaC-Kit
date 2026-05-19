"""Unit tests for packet generator."""
import io
from pathlib import Path

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

    def test_write_single_packet(self, test_output_dir):
        """Test writing a single packet to file."""
        fields = [
            ccsdspy.PacketField(name="field1", data_type="uint", bit_length=8),
            ccsdspy.PacketField(name="field2", data_type="uint", bit_length=16),
        ]
        packet = ccsdspy.VariableLength(fields, apid=100, name="TestPacket")
        generator = PacketGenerator(packet)

        file_obj = io.BytesIO()
        generator.write_packet(file_obj, use_random=False)

        file_obj.seek(0)
        written_data = file_obj.read()

        # Save to output directory for review
        output_file = test_output_dir / "single_packet_zeros.bin"
        with open(output_file, "wb") as f:
            f.write(written_data)

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

    def test_write_multiple_packets(self, test_output_dir):
        """Test writing multiple packets with incrementing sequence counts."""
        fields = [ccsdspy.PacketField(name="data", data_type="uint", bit_length=8)]
        packet = ccsdspy.VariableLength(fields, apid=100, name="Test")
        generator = PacketGenerator(packet)

        file_obj = io.BytesIO()
        generator.write_packet(file_obj, count=3, use_random=False)

        file_obj.seek(0)
        written_data = file_obj.read()

        # Save to output directory for review
        output_file = test_output_dir / "multiple_packets_zeros.bin"
        with open(output_file, "wb") as f:
            f.write(written_data)

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

    def test_write_packet_with_array_fields(self, test_output_dir):
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
        generator.write_packet(file_obj, count=2, use_random=False)

        file_obj.seek(0)
        written_data = file_obj.read()

        # Save to output directory for review
        output_file = test_output_dir / "array_fields_zeros.bin"
        with open(output_file, "wb") as f:
            f.write(written_data)

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

    def test_write_packet_with_float_fields(self, test_output_dir):
        """Test writing packets with float fields."""
        fields = [
            ccsdspy.PacketField(name="temperature", data_type="float", bit_length=32),
            ccsdspy.PacketField(name="pressure", data_type="float", bit_length=32),
        ]
        packet = ccsdspy.VariableLength(fields, apid=300, name="SensorPacket")
        generator = PacketGenerator(packet)

        file_obj = io.BytesIO()
        generator.write_packet(file_obj, count=2, use_random=False)

        file_obj.seek(0)
        written_data = file_obj.read()

        # Save to output directory for review
        output_file = test_output_dir / "float_fields_zeros.bin"
        with open(output_file, "wb") as f:
            f.write(written_data)

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
            generator.write_packet(file_obj, use_random=False)

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
        generator.write_packet(file_obj, use_random=False)

        file_obj.seek(0)
        written_data = file_obj.read()

        # 6-byte header + 1 byte padding (ccsdspy requires at least 1 byte of data)
        assert len(written_data) == 7

        # Verify by parsing back with ccsdspy
        file_obj.seek(0)
        parsed = packet.load(file_obj, include_primary_header=True)

        assert len(parsed["CCSDS_APID"]) == 1
        assert parsed["CCSDS_APID"][0] == 100

    def test_create_data_dict_zeros(self):
        """Test zero-initialized data dictionary creation."""
        fields = [
            ccsdspy.PacketField(name="scalar", data_type="uint", bit_length=8),
            ccsdspy.PacketArray(
                name="fixed_array", data_type="uint", bit_length=16, array_shape=3
            ),
        ]
        packet = ccsdspy.VariableLength(fields, apid=100, name="Test")
        generator = PacketGenerator(packet)

        data_dict = generator._create_data_dict(count=2, use_random=False)

        # Check scalar field
        assert "scalar" in data_dict
        assert data_dict["scalar"].shape == (2,)
        assert np.all(data_dict["scalar"] == 0)

        # Check array field
        assert "fixed_array" in data_dict
        assert data_dict["fixed_array"].shape == (2, 3)
        assert np.all(data_dict["fixed_array"] == 0)

    def test_create_data_dict_random(self):
        """Test random data dictionary creation."""
        fields = [
            ccsdspy.PacketField(name="scalar", data_type="uint", bit_length=8),
            ccsdspy.PacketArray(
                name="fixed_array", data_type="uint", bit_length=16, array_shape=3
            ),
        ]
        packet = ccsdspy.VariableLength(fields, apid=100, name="Test")
        generator = PacketGenerator(packet)

        data_dict = generator._create_data_dict(count=2, use_random=True)

        # Check scalar field exists and has correct shape
        assert "scalar" in data_dict
        assert data_dict["scalar"].shape == (2,)
        # Very unlikely all random values are zero
        assert not np.all(data_dict["scalar"] == 0)

        # Check array field exists and has correct shape
        assert "fixed_array" in data_dict
        assert data_dict["fixed_array"].shape == (2, 3)
        # Very unlikely all random values are zero
        assert not np.all(data_dict["fixed_array"] == 0)

    def test_random_uint_range(self):
        """Test that random uint values respect bit length ranges."""
        fields = [
            ccsdspy.PacketField(name="uint8_field", data_type="uint", bit_length=8),
            ccsdspy.PacketField(name="uint16_field", data_type="uint", bit_length=16),
        ]
        packet = ccsdspy.VariableLength(fields, apid=100, name="Test")
        generator = PacketGenerator(packet)

        data_dict = generator._create_data_dict(count=100, use_random=True)

        # uint8 should be in [0, 255]
        assert np.all(data_dict["uint8_field"] >= 0)
        assert np.all(data_dict["uint8_field"] <= 255)

        # uint16 should be in [0, 65535]
        assert np.all(data_dict["uint16_field"] >= 0)
        assert np.all(data_dict["uint16_field"] <= 65535)

    def test_random_int_range(self):
        """Test that random int values respect bit length ranges."""
        fields = [
            ccsdspy.PacketField(name="int8_field", data_type="int", bit_length=8),
            ccsdspy.PacketField(name="int16_field", data_type="int", bit_length=16),
        ]
        packet = ccsdspy.VariableLength(fields, apid=100, name="Test")
        generator = PacketGenerator(packet)

        data_dict = generator._create_data_dict(count=100, use_random=True)

        # int8 should be in [-128, 127]
        assert np.all(data_dict["int8_field"] >= -128)
        assert np.all(data_dict["int8_field"] <= 127)

        # int16 should be in [-32768, 32767]
        assert np.all(data_dict["int16_field"] >= -32768)
        assert np.all(data_dict["int16_field"] <= 32767)

    def test_random_float_generation(self):
        """Test that random float values are generated."""
        fields = [
            ccsdspy.PacketField(name="temperature", data_type="float", bit_length=32),
        ]
        packet = ccsdspy.VariableLength(fields, apid=100, name="Test")
        generator = PacketGenerator(packet)

        data_dict = generator._create_data_dict(count=10, use_random=True)

        # Check that floats are not all zero
        assert not np.all(data_dict["temperature"] == 0.0)
        # Check that floats are in reasonable range
        assert np.all(np.abs(data_dict["temperature"]) <= 1000.0)

    def test_random_data_varies(self):
        """Test that consecutive packets have different random data."""
        fields = [ccsdspy.PacketField(name="data", data_type="uint", bit_length=8)]
        packet = ccsdspy.VariableLength(fields, apid=100, name="Test")
        generator = PacketGenerator(packet)

        data_dict = generator._create_data_dict(count=10, use_random=True)

        # Check that not all packets have the same value
        # (extremely unlikely with random data)
        assert not np.all(data_dict["data"] == data_dict["data"][0])

    def test_write_packet_random(self, test_output_dir):
        """Test writing packets with random data."""
        fields = [ccsdspy.PacketField(name="data", data_type="uint", bit_length=8)]
        packet = ccsdspy.VariableLength(fields, apid=100, name="Test")
        generator = PacketGenerator(packet)

        file_obj = io.BytesIO()
        generator.write_packet(file_obj, count=3, use_random=True)

        file_obj.seek(0)
        written_data = file_obj.read()

        # Save to output directory for review
        output_file = test_output_dir / "multiple_packets_random.bin"
        with open(output_file, "wb") as f:
            f.write(written_data)

        # Verify by parsing back with ccsdspy
        file_obj.seek(0)
        parsed = packet.load(file_obj, include_primary_header=True)

        # Check that data is not all zeros (very unlikely with random)
        assert not np.all(parsed["data"] == 0)
        # Check that consecutive packets have different values
        assert not np.all(parsed["data"] == parsed["data"][0])

    def test_large_array_packet_zeros(self, test_output_dir):
        """Test writing packets with large arrays (zero-initialized)."""
        fields = [
            ccsdspy.PacketField(name="counter", data_type="uint", bit_length=16),
            ccsdspy.PacketArray(
                name="large_data", data_type="uint", bit_length=16, array_shape=10000
            ),
        ]
        packet = ccsdspy.VariableLength(fields, apid=400, name="LargePacket")
        generator = PacketGenerator(packet)

        file_obj = io.BytesIO()
        generator.write_packet(file_obj, count=2, use_random=False)

        file_obj.seek(0)
        written_data = file_obj.read()

        # Save to output directory for review
        output_file = test_output_dir / "large_array_zeros.bin"
        with open(output_file, "wb") as f:
            f.write(written_data)

        # Each packet: 6-byte header + 2 bytes counter + 20000 bytes array
        # = 20008 bytes per packet, 2 packets = 40016 bytes
        assert len(written_data) == 40016

        # Verify by parsing back with ccsdspy
        file_obj.seek(0)
        parsed = packet.load(file_obj, include_primary_header=True)

        assert len(parsed["counter"]) == 2
        assert len(parsed["large_data"]) == 2
        # Verify all data is zero
        assert np.all(parsed["counter"] == 0)
        assert np.all(parsed["large_data"] == 0)
        # Verify array shape
        assert parsed["large_data"][0].shape == (10000,)

    def test_large_array_packet_random(self, test_output_dir):
        """Test writing packets with large arrays (random data)."""
        fields = [
            ccsdspy.PacketField(name="counter", data_type="uint", bit_length=16),
            ccsdspy.PacketArray(
                name="large_data", data_type="uint", bit_length=16, array_shape=10000
            ),
        ]
        packet = ccsdspy.VariableLength(fields, apid=400, name="LargePacket")
        generator = PacketGenerator(packet)

        file_obj = io.BytesIO()
        generator.write_packet(file_obj, count=2, use_random=True)

        file_obj.seek(0)
        written_data = file_obj.read()

        # Save to output directory for review
        output_file = test_output_dir / "large_array_random.bin"
        with open(output_file, "wb") as f:
            f.write(written_data)

        # Each packet: 6-byte header + 2 bytes counter + 20000 bytes array
        assert len(written_data) == 40016

        # Verify by parsing back with ccsdspy
        file_obj.seek(0)
        parsed = packet.load(file_obj, include_primary_header=True)

        assert len(parsed["counter"]) == 2
        assert len(parsed["large_data"]) == 2
        # Verify array shape
        assert parsed["large_data"][0].shape == (10000,)
        # Check that data is not all zeros (very unlikely with random)
        assert not np.all(parsed["large_data"] == 0)
        # Check that the two packets have different random data
        assert not np.array_equal(parsed["large_data"][0], parsed["large_data"][1])

    def test_many_fields_packet(self, test_output_dir):
        """Test writing packets with many fields."""
        # Create a packet with 50 fields
        fields = [
            ccsdspy.PacketField(name=f"field_{i}", data_type="uint", bit_length=16)
            for i in range(50)
        ]
        packet = ccsdspy.VariableLength(fields, apid=500, name="ManyFieldsPacket")
        generator = PacketGenerator(packet)

        file_obj = io.BytesIO()
        generator.write_packet(file_obj, count=3, use_random=True)

        file_obj.seek(0)
        written_data = file_obj.read()

        # Save to output directory for review
        output_file = test_output_dir / "many_fields_random.bin"
        with open(output_file, "wb") as f:
            f.write(written_data)

        # Each packet: 6-byte header + 100 bytes data (50 fields * 2 bytes)
        # = 106 bytes per packet, 3 packets = 318 bytes
        assert len(written_data) == 318

        # Verify by parsing back with ccsdspy
        file_obj.seek(0)
        parsed = packet.load(file_obj, include_primary_header=True)

        # Verify all fields exist and have correct length
        for i in range(50):
            field_name = f"field_{i}"
            assert field_name in parsed
            assert len(parsed[field_name]) == 3
        # Check that data is not all zeros (very unlikely with random)
        assert not np.all(parsed["field_0"] == 0)

    def test_fixed_length_packet_zeros(self, test_output_dir):
        """Test writing FixedLength packets with zero-initialized data."""
        fields = [
            ccsdspy.PacketField(name="counter", data_type="uint", bit_length=16),
            ccsdspy.PacketField(name="voltage", data_type="float", bit_length=32),
            ccsdspy.PacketArray(
                name="samples", data_type="uint", bit_length=8, array_shape=10
            ),
        ]
        packet = ccsdspy.FixedLength(fields, apid=600)
        generator = PacketGenerator(packet)

        file_obj = io.BytesIO()
        generator.write_packet(file_obj, count=3, use_random=False)

        file_obj.seek(0)
        written_data = file_obj.read()

        # Save to output directory for review
        output_file = test_output_dir / "fixed_length_zeros.bin"
        with open(output_file, "wb") as f:
            f.write(written_data)

        # Each packet: 6-byte header + 2 counter + 4 voltage + 10 samples
        # = 22 bytes per packet, 3 packets = 66 bytes
        assert len(written_data) == 66

        # Verify by parsing back with ccsdspy
        file_obj.seek(0)
        parsed = packet.load(file_obj, include_primary_header=True)

        assert len(parsed["counter"]) == 3
        assert np.all(parsed["counter"] == 0)
        assert np.all(parsed["voltage"] == 0.0)
        assert np.all(parsed["samples"] == 0)

    def test_fixed_length_packet_random(self, test_output_dir):
        """Test writing FixedLength packets with random data."""
        fields = [
            ccsdspy.PacketField(name="counter", data_type="uint", bit_length=16),
            ccsdspy.PacketField(name="voltage", data_type="float", bit_length=32),
            ccsdspy.PacketArray(
                name="samples", data_type="uint", bit_length=8, array_shape=10
            ),
        ]
        packet = ccsdspy.FixedLength(fields, apid=600)
        generator = PacketGenerator(packet)

        file_obj = io.BytesIO()
        generator.write_packet(file_obj, count=3, use_random=True)

        file_obj.seek(0)
        written_data = file_obj.read()

        # Save to output directory for review
        output_file = test_output_dir / "fixed_length_random.bin"
        with open(output_file, "wb") as f:
            f.write(written_data)

        # Each packet: 6-byte header + 2 counter + 4 voltage + 10 samples = 22 bytes
        assert len(written_data) == 66

        # Verify by parsing back with ccsdspy
        file_obj.seek(0)
        parsed = packet.load(file_obj, include_primary_header=True)

        assert len(parsed["counter"]) == 3
        # Check that data is not all zeros (very unlikely with random)
        assert not np.all(parsed["counter"] == 0)
        assert not np.all(parsed["voltage"] == 0.0)
        assert not np.all(parsed["samples"] == 0)

    def test_variable_length_expand_arrays(self, test_output_dir):
        """Test packets with variable-length expand arrays."""
        fields = [
            ccsdspy.PacketField(name="seq_num", data_type="uint", bit_length=16),
            ccsdspy.PacketArray(
                name="var_data",
                data_type="uint",
                bit_length=8,
                array_shape="expand",
                array_order="C",
            ),
        ]
        packet = ccsdspy.VariableLength(fields, apid=700, name="ExpandPacket")
        generator = PacketGenerator(packet)

        file_obj = io.BytesIO()
        generator.write_packet(file_obj, count=5, use_random=True)

        file_obj.seek(0)
        written_data = file_obj.read()

        # Save to output directory for review
        output_file = test_output_dir / "expand_arrays_random.bin"
        with open(output_file, "wb") as f:
            f.write(written_data)

        # Verify by parsing back with ccsdspy
        file_obj.seek(0)
        parsed = packet.load(file_obj, include_primary_header=True)

        assert len(parsed["seq_num"]) == 5
        assert len(parsed["var_data"]) == 5
        # Each packet should have different length arrays
        lengths = [len(parsed["var_data"][i]) for i in range(5)]
        # Very unlikely all 5 packets have the same random length
        assert len(set(lengths)) > 1

    def test_signed_integers_in_packets(self, test_output_dir):
        """Test writing packets with signed integer fields."""
        fields = [
            ccsdspy.PacketField(name="int8_val", data_type="int", bit_length=8),
            ccsdspy.PacketField(name="int16_val", data_type="int", bit_length=16),
            ccsdspy.PacketField(name="int32_val", data_type="int", bit_length=32),
        ]
        packet = ccsdspy.VariableLength(fields, apid=800, name="SignedIntPacket")
        generator = PacketGenerator(packet)

        file_obj = io.BytesIO()
        generator.write_packet(file_obj, count=10, use_random=True)

        file_obj.seek(0)
        written_data = file_obj.read()

        # Save to output directory for review
        output_file = test_output_dir / "signed_integers_random.bin"
        with open(output_file, "wb") as f:
            f.write(written_data)

        # Verify by parsing back with ccsdspy
        file_obj.seek(0)
        parsed = packet.load(file_obj, include_primary_header=True)

        assert len(parsed["int8_val"]) == 10
        # Verify ranges for signed integers
        assert np.all(parsed["int8_val"] >= -128)
        assert np.all(parsed["int8_val"] <= 127)
        assert np.all(parsed["int16_val"] >= -32768)
        assert np.all(parsed["int16_val"] <= 32767)
        # Check that we have some negative values (very likely with 10 random samples)
        assert np.any(parsed["int8_val"] < 0) or np.any(parsed["int16_val"] < 0)

    def test_multidimensional_arrays(self, test_output_dir):
        """Test packets with multi-dimensional arrays."""
        fields = [
            ccsdspy.PacketField(name="timestamp", data_type="uint", bit_length=32),
            ccsdspy.PacketArray(
                name="image_data", data_type="uint", bit_length=8, array_shape=(4, 5)
            ),
        ]
        packet = ccsdspy.VariableLength(fields, apid=1000, name="ImagePacket")
        generator = PacketGenerator(packet)

        file_obj = io.BytesIO()
        generator.write_packet(file_obj, count=2, use_random=True)

        file_obj.seek(0)
        written_data = file_obj.read()

        # Save to output directory for review
        output_file = test_output_dir / "multidimensional_arrays_random.bin"
        with open(output_file, "wb") as f:
            f.write(written_data)

        # Verify by parsing back with ccsdspy
        file_obj.seek(0)
        parsed = packet.load(file_obj, include_primary_header=True)

        assert len(parsed["timestamp"]) == 2
        assert len(parsed["image_data"]) == 2
        # Verify multi-dimensional shape
        assert parsed["image_data"][0].shape == (4, 5)
        assert parsed["image_data"][1].shape == (4, 5)
        # Check that data is not all zeros
        assert not np.all(parsed["image_data"] == 0)

    def test_large_sequence_counts(self, test_output_dir):
        """Test large sequence counts approach 14-bit boundary.

        Note: ccsdspy's encoder uses 14-bit sequence counts (0-16383).
        Generating more than 16384 packets in a single write_packet call
        will fail. For larger generation, call write_packet multiple times.
        """
        fields = [ccsdspy.PacketField(name="data", data_type="uint", bit_length=8)]
        packet = ccsdspy.VariableLength(fields, apid=1100, name="LargeSeqTest")
        generator = PacketGenerator(packet)

        # Generate packets approaching but not exceeding the 14-bit limit
        count = 1000
        file_obj = io.BytesIO()
        generator.write_packet(file_obj, count=count, use_random=False)

        file_obj.seek(0)
        written_data = file_obj.read()

        # Save to output directory for review
        output_file = test_output_dir / "large_sequence_counts.bin"
        with open(output_file, "wb") as f:
            f.write(written_data)

        # Verify by parsing back with ccsdspy
        file_obj.seek(0)
        parsed = packet.load(file_obj, include_primary_header=True)

        assert len(parsed["data"]) == count
        # Verify sequence counts increment correctly
        seq_counts = parsed["CCSDS_SEQUENCE_COUNT"]
        assert seq_counts[0] == 0
        assert seq_counts[999] == 999
        # Verify all sequence counts are sequential
        expected = np.arange(count)
        assert np.array_equal(seq_counts, expected)
