"""Generate CCSDS packets with zero/blank values from packet definitions."""
import struct
from typing import BinaryIO

import ccsdspy
import numpy as np


class PacketGenerator:
    """Generate CCSDS packets from packet definitions."""

    def __init__(self, packet: ccsdspy.packet_types._BasePacket):
        """Initialize the generator with a packet definition.

        Args:
            packet: A CCSDSpy packet definition (FixedLength or VariableLength)
        """
        self.packet = packet
        self.name = getattr(packet, "name", "UnnamedPacket")
        self.apid = getattr(packet, "apid", 0)

    def _get_default_value(self, field):
        """Get default zero/blank value for a field based on its data type.

        Args:
            field: A CCSDSpy PacketField or PacketArray

        Returns:
            Default value appropriate for the field's data type
        """
        data_type = getattr(field, "_data_type", "uint")
        bit_length = getattr(field, "_bit_length", 8)
        array_shape = getattr(field, "_array_shape", None)

        if array_shape is not None:
            if array_shape == "expand":
                return np.array([], dtype=self._get_numpy_dtype(data_type))
            if isinstance(array_shape, (tuple, list)):
                return np.zeros(array_shape, dtype=self._get_numpy_dtype(data_type))
            return np.zeros(array_shape, dtype=self._get_numpy_dtype(data_type))

        if data_type in ("uint", "int"):
            return 0
        if data_type in ("float", "double"):
            return 0.0
        if data_type == "fill":
            byte_length = bit_length // 8
            return b"\x00" * byte_length

        return 0

    def _get_numpy_dtype(self, data_type: str):
        """Convert CCSDSpy data type to numpy dtype.

        Args:
            data_type: CCSDSpy data type string

        Returns:
            Corresponding numpy dtype
        """
        type_map = {
            "uint": np.uint8,
            "int": np.int8,
            "float": np.float32,
            "double": np.float64,
        }
        return type_map.get(data_type, np.uint8)

    def _calculate_field_bytes(self, field):
        """Calculate the number of bytes needed for a field.

        Args:
            field: A CCSDSpy PacketField or PacketArray

        Returns:
            Number of bytes needed for the field
        """
        bit_length = getattr(field, "_bit_length", 8)
        array_shape = getattr(field, "_array_shape", None)

        if array_shape == "expand":
            return 0

        if array_shape is not None:
            if isinstance(array_shape, (tuple, list)):
                total_elements = np.prod(array_shape)
            else:
                total_elements = array_shape
            return int(total_elements * bit_length // 8)

        return int((bit_length + 7) // 8)

    def _generate_ccsds_header(
        self,
        apid: int,
        sequence_count: int = 0,
        data_length: int = 0,
        packet_type: int = 0,
        secondary_header_flag: int = 0,
    ) -> bytes:
        """Generate a CCSDS primary header.

        Args:
            apid: Application Process Identifier (11 bits)
            sequence_count: Packet sequence count (14 bits)
            data_length: Length of data field in bytes minus 1 (16 bits)
            packet_type: 0 for telemetry, 1 for command (1 bit)
            secondary_header_flag: 1 if secondary header present (1 bit)

        Returns:
            6-byte CCSDS primary header
        """
        version = 0
        sequence_flags = 3

        word1 = (
            (version << 13) | (packet_type << 12) | (secondary_header_flag << 11) | apid
        )
        word2 = (sequence_flags << 14) | sequence_count
        word3 = data_length

        return struct.pack(">HHH", word1, word2, word3)

    def generate_packet_data(self) -> bytes:
        """Generate packet data with zero/blank values for all fields.

        Returns:
            Binary data for packet fields (without CCSDS header)
        """
        data_parts = []

        for field in self.packet._fields:
            field_bytes = self._calculate_field_bytes(field)

            if field_bytes > 0:
                data_parts.append(b"\x00" * field_bytes)

        return b"".join(data_parts)

    def generate_packet(self, sequence_count: int = 0) -> bytes:
        """Generate a complete CCSDS packet with header and zero-filled data.

        Args:
            sequence_count: Packet sequence count (default: 0)

        Returns:
            Complete binary CCSDS packet (header + data)
        """
        data = self.generate_packet_data()
        data_length = len(data) - 1 if len(data) > 0 else 0

        header = self._generate_ccsds_header(
            apid=self.apid, sequence_count=sequence_count, data_length=data_length
        )

        return header + data

    def write_packet(self, file_obj: BinaryIO, sequence_count: int = 0, count: int = 1):
        """Write one or more packets to a file.

        Args:
            file_obj: Binary file object to write to
            sequence_count: Starting sequence count (default: 0)
            count: Number of packets to write (default: 1)
        """
        for i in range(count):
            packet = self.generate_packet(sequence_count=sequence_count + i)
            file_obj.write(packet)


def generate_packets_from_definitions(packets: list, output_path: str):
    """Generate packets from a list of packet definitions and write to file.

    Args:
        packets: List of CCSDSpy packet definitions
        output_path: Path to output binary file
    """
    with open(output_path, "wb") as f:
        for packet_def in packets:
            generator = PacketGenerator(packet_def)
            generator.write_packet(f)
