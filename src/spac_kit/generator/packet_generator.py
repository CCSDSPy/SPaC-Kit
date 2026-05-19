"""Generate CCSDS packets with zero/blank values from packet definitions."""
from typing import BinaryIO

import ccsdspy
import numpy as np
from ccsdspy.encode import _encode_fixed_length
from ccsdspy.encode import _encode_variable_length
from ccsdspy.packet_types import _expand_array_fields


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

    def _create_data_dict(self, count: int, use_random: bool = True) -> dict:
        """Create a dictionary of arrays for packet generation.

        Args:
            count: Number of packets to generate
            use_random: If True, generate random data; if False, use zeros
                (default: True)

        Returns:
            Dictionary mapping field names to numpy arrays
        """
        data_dict = {}

        for field in self.packet._fields:
            field_name = field._name
            data_type = field._data_type
            bit_length = field._bit_length
            array_shape = getattr(field, "_array_shape", None)
            dtype = self._get_numpy_dtype(data_type)

            # Handle variable-length fields (expand)
            if array_shape == "expand":
                if use_random:
                    # Create list of random-length arrays with random data
                    data_dict[field_name] = []
                    for _ in range(count):
                        length = np.random.randint(0, 11)  # Random length 0-10
                        if data_type in ("uint", "int"):
                            if data_type == "uint":
                                max_val = min(2**bit_length, np.iinfo(dtype).max + 1)
                                arr = np.random.randint(
                                    0, max_val, size=length, dtype=dtype
                                )
                            else:
                                min_val = max(
                                    -(2 ** (bit_length - 1)), np.iinfo(dtype).min
                                )
                                max_val = min(
                                    2 ** (bit_length - 1), np.iinfo(dtype).max + 1
                                )
                                arr = np.random.randint(
                                    min_val, max_val, size=length, dtype=dtype
                                )
                        elif data_type in ("float", "double"):
                            arr = np.random.uniform(
                                -1000.0, 1000.0, size=length
                            ).astype(dtype)
                        else:
                            arr = np.array([], dtype=dtype)
                        data_dict[field_name].append(arr)
                else:
                    # Create list of empty arrays
                    data_dict[field_name] = [
                        np.array([], dtype=dtype) for _ in range(count)
                    ]

            # Handle fixed-size array fields
            elif array_shape is not None:
                if isinstance(array_shape, (tuple, list)):
                    # Multi-dimensional array: shape is (count, *array_shape)
                    full_shape = (count,) + tuple(array_shape)
                else:
                    # 1D array: shape is (count, array_shape)
                    full_shape = (count, array_shape)

                if use_random:
                    if data_type in ("uint", "int"):
                        if data_type == "uint":
                            max_val = min(2**bit_length, np.iinfo(dtype).max + 1)
                            data_dict[field_name] = np.random.randint(
                                0, max_val, size=full_shape, dtype=dtype
                            )
                        else:
                            min_val = max(-(2 ** (bit_length - 1)), np.iinfo(dtype).min)
                            max_val = min(
                                2 ** (bit_length - 1), np.iinfo(dtype).max + 1
                            )
                            data_dict[field_name] = np.random.randint(
                                min_val, max_val, size=full_shape, dtype=dtype
                            )
                    elif data_type in ("float", "double"):
                        data_dict[field_name] = np.random.uniform(
                            -1000.0, 1000.0, size=full_shape
                        ).astype(dtype)
                    else:
                        data_dict[field_name] = np.zeros(full_shape, dtype=dtype)
                else:
                    data_dict[field_name] = np.zeros(full_shape, dtype=dtype)

            # Handle regular scalar fields
            else:
                if use_random:
                    if data_type in ("uint", "int"):
                        if data_type == "uint":
                            max_val = min(2**bit_length, np.iinfo(dtype).max + 1)
                            data_dict[field_name] = np.random.randint(
                                0, max_val, size=count, dtype=dtype
                            )
                        else:
                            min_val = max(-(2 ** (bit_length - 1)), np.iinfo(dtype).min)
                            max_val = min(
                                2 ** (bit_length - 1), np.iinfo(dtype).max + 1
                            )
                            data_dict[field_name] = np.random.randint(
                                min_val, max_val, size=count, dtype=dtype
                            )
                    elif data_type in ("float", "double"):
                        data_dict[field_name] = np.random.uniform(
                            -1000.0, 1000.0, size=count
                        ).astype(dtype)
                    else:
                        data_dict[field_name] = np.zeros(count, dtype=dtype)
                else:
                    data_dict[field_name] = np.zeros(count, dtype=dtype)

        return data_dict

    def write_packet(self, file_obj: BinaryIO, count: int = 1, use_random: bool = True):
        """Write one or more packets to a file using ccsdspy's encoder.

        Args:
            file_obj: Binary file object to write to
            count: Number of packets to write (default: 1)
            use_random: If True, generate random data; if False, use zeros
                (default: True)

        Note:
            Sequence count starts from 0 and increments automatically.
        """
        # Create data dictionary (random or zeros)
        data = self._create_data_dict(count, use_random=use_random)

        # Handle empty packets (no fields)
        # ccsdspy expects at least 1 byte of data (packet_nbytes = data_length + 7)
        # For truly empty packets, we write data_length = 0 and 1 byte of padding
        if not self.packet._fields:
            # For empty packets, manually encode headers
            import struct

            for i in range(count):
                version = 0
                packet_type = 0
                sec_header_flag = 0
                sequence_flags = 3
                data_length = (
                    0  # Per CCSDS: data_length = num_data_bytes - 1, so 0 means 1 byte
                )

                word1 = (
                    (version << 13)
                    | (packet_type << 12)
                    | (sec_header_flag << 11)
                    | (self.apid & 0x7FF)  # Mask APID to 11 bits
                )
                word2 = (sequence_flags << 14) | (
                    i & 0x3FFF
                )  # Mask sequence count to 14 bits
                word3 = data_length

                header = struct.pack(">HHH", word1, word2, word3)
                file_obj.write(header)
                file_obj.write(b"\x00")  # Add 1 byte of padding for ccsdspy
            return

        # Expand array fields for encoding
        expand_fields, _ = _expand_array_fields(self.packet._fields)

        # Determine packet type (FixedLength or VariableLength)
        is_variable = isinstance(self.packet, ccsdspy.VariableLength)

        # Use ccsdspy's encode functions directly
        if is_variable:
            packet_bytes = _encode_variable_length(
                fields=self.packet._fields,
                expand_fields=expand_fields,
                field_arrays=data,
                pkt_type=0,  # 0 for telemetry
                apid=self.apid,
                sec_header_flag=0,  # No secondary header
                seq_flag=3,  # Complete data in packet
            )
        else:
            packet_bytes = _encode_fixed_length(
                fields=self.packet._fields,
                expand_fields=expand_fields,
                field_arrays=data,
                pkt_type=0,  # 0 for telemetry
                apid=self.apid,
                sec_header_flag=0,  # No secondary header
                seq_flag=3,  # Complete data in packet
            )

        # Write the encoded packets to the file
        file_obj.write(packet_bytes)


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
