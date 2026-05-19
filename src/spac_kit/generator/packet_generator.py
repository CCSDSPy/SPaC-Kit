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
                return np.array([], dtype=self._get_numpy_dtype(data_type, bit_length))
            if isinstance(array_shape, (tuple, list)):
                return np.zeros(
                    array_shape, dtype=self._get_numpy_dtype(data_type, bit_length)
                )
            return np.zeros(
                array_shape, dtype=self._get_numpy_dtype(data_type, bit_length)
            )

        if data_type in ("uint", "int"):
            return 0
        if data_type in ("float", "double"):
            return 0.0
        if data_type == "fill":
            byte_length = bit_length // 8
            return b"\x00" * byte_length

        return 0

    def _get_numpy_dtype(self, data_type: str, bit_length: int = 8):
        """Convert CCSDSpy data type to numpy dtype based on bit length.

        Args:
            data_type: CCSDSpy data type string
            bit_length: Number of bits (used for uint/int types)

        Returns:
            Corresponding numpy dtype
        """
        if data_type == "uint":
            if bit_length <= 8:
                return np.uint8
            elif bit_length <= 16:
                return np.uint16
            elif bit_length <= 32:
                return np.uint32
            else:
                return np.uint64
        elif data_type == "int":
            if bit_length <= 8:
                return np.int8
            elif bit_length <= 16:
                return np.int16
            elif bit_length <= 32:
                return np.int32
            else:
                return np.int64
        elif data_type == "float":
            return np.float32
        elif data_type == "double":
            return np.float64
        else:
            return np.uint8

    def _generate_random_uint(self, bit_length: int, dtype, size):
        """Generate random unsigned integer array respecting bit length.

        Args:
            bit_length: Number of bits in the field
            dtype: Numpy dtype for the array
            size: Shape of the output array

        Returns:
            Random unsigned integer array

        Note:
            Generates with a larger dtype when needed to avoid overflow in the
            exclusive high bound, then casts to target dtype.
        """
        max_val = min(2**bit_length, np.iinfo(dtype).max + 1)

        # Generate with larger dtype to handle exclusive high bound
        if dtype == np.uint8:
            temp = np.random.randint(0, max_val, size=size, dtype=np.uint16)
            return temp.astype(np.uint8)
        elif dtype == np.uint16:
            temp = np.random.randint(0, max_val, size=size, dtype=np.uint32)
            return temp.astype(np.uint16)
        elif dtype == np.uint32:
            temp = np.random.randint(0, max_val, size=size, dtype=np.uint64)
            return temp.astype(np.uint32)
        else:
            # uint64 - use int64 for generation if possible
            if max_val <= np.iinfo(np.int64).max:
                temp = np.random.randint(0, max_val, size=size, dtype=np.int64)
                return temp.astype(np.uint64)
            else:
                # For very large uint64, accept the limitation
                return np.random.randint(0, max_val, size=size, dtype=np.uint64)

    def _generate_random_int(self, bit_length: int, dtype, size):
        """Generate random signed integer array respecting bit length.

        Args:
            bit_length: Number of bits in the field
            dtype: Numpy dtype for the array
            size: Shape of the output array

        Returns:
            Random signed integer array

        Note:
            Generates with a larger dtype when needed to avoid overflow in the
            exclusive high bound, then casts to target dtype.
        """
        min_val = max(-(2 ** (bit_length - 1)), np.iinfo(dtype).min)
        max_val = min(2 ** (bit_length - 1), np.iinfo(dtype).max + 1)

        # Generate with larger dtype to handle exclusive high bound
        if dtype == np.int8:
            temp = np.random.randint(min_val, max_val, size=size, dtype=np.int16)
            return temp.astype(np.int8)
        elif dtype == np.int16:
            temp = np.random.randint(min_val, max_val, size=size, dtype=np.int32)
            return temp.astype(np.int16)
        elif dtype == np.int32:
            temp = np.random.randint(min_val, max_val, size=size, dtype=np.int64)
            return temp.astype(np.int32)
        else:
            # int64 - accept the limitation at the boundary
            return np.random.randint(min_val, max_val, size=size, dtype=np.int64)

    def _generate_random_float(self, dtype, size):
        """Generate random float array.

        Args:
            dtype: Numpy dtype for the array
            size: Shape of the output array

        Returns:
            Random float array
        """
        return np.random.uniform(-1000.0, 1000.0, size=size).astype(dtype)

    def _generate_random_data(self, data_type: str, bit_length: int, dtype, size):
        """Generate random data based on data type.

        Args:
            data_type: CCSDSpy data type (uint, int, float, double)
            bit_length: Number of bits in the field
            dtype: Numpy dtype for the array
            size: Shape of the output array

        Returns:
            Random data array appropriate for the data type
        """
        if data_type == "uint":
            return self._generate_random_uint(bit_length, dtype, size)
        elif data_type == "int":
            return self._generate_random_int(bit_length, dtype, size)
        elif data_type in ("float", "double"):
            return self._generate_random_float(dtype, size)
        else:
            return np.zeros(size, dtype=dtype)

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
            dtype = self._get_numpy_dtype(data_type, bit_length)

            # Case 1: Variable-length fields (expand)
            if array_shape == "expand":
                data_dict[field_name] = self._create_variable_length_data(
                    count, data_type, bit_length, dtype, use_random
                )

            # Case 2: Fixed-size array fields
            elif array_shape is not None:
                full_shape = self._compute_array_shape(count, array_shape)
                data_dict[field_name] = self._create_array_data(
                    data_type, bit_length, dtype, full_shape, use_random
                )

            # Case 3: Scalar fields
            else:
                data_dict[field_name] = self._create_scalar_data(
                    count, data_type, bit_length, dtype, use_random
                )

        return data_dict

    def _compute_array_shape(self, count: int, array_shape):
        """Compute the full shape for a fixed-size array field.

        Args:
            count: Number of packets
            array_shape: Array shape from field definition

        Returns:
            Full shape tuple (count, *array_shape)
        """
        if isinstance(array_shape, (tuple, list)):
            return (count,) + tuple(array_shape)
        else:
            return (count, array_shape)

    def _create_variable_length_data(
        self, count: int, data_type: str, bit_length: int, dtype, use_random: bool
    ):
        """Create variable-length array data for expand fields.

        Args:
            count: Number of packets
            data_type: CCSDSpy data type
            bit_length: Number of bits in the field
            dtype: Numpy dtype
            use_random: If True, generate random data

        Returns:
            List of numpy arrays with varying lengths
        """
        if not use_random:
            return [np.array([], dtype=dtype) for _ in range(count)]

        result = []
        for _ in range(count):
            length = np.random.randint(0, 11)  # Random length 0-10
            arr = self._generate_random_data(data_type, bit_length, dtype, length)
            result.append(arr)
        return result

    def _create_array_data(
        self,
        data_type: str,
        bit_length: int,
        dtype,
        shape: tuple,
        use_random: bool,
    ):
        """Create fixed-size array data.

        Args:
            data_type: CCSDSpy data type
            bit_length: Number of bits in the field
            dtype: Numpy dtype
            shape: Full shape of the array
            use_random: If True, generate random data

        Returns:
            Numpy array with the specified shape
        """
        if not use_random:
            return np.zeros(shape, dtype=dtype)

        return self._generate_random_data(data_type, bit_length, dtype, shape)

    def _create_scalar_data(
        self, count: int, data_type: str, bit_length: int, dtype, use_random: bool
    ):
        """Create scalar field data.

        Args:
            count: Number of packets
            data_type: CCSDSpy data type
            bit_length: Number of bits in the field
            dtype: Numpy dtype
            use_random: If True, generate random data

        Returns:
            Numpy array of scalar values
        """
        if not use_random:
            return np.zeros(count, dtype=dtype)

        return self._generate_random_data(data_type, bit_length, dtype, count)

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
