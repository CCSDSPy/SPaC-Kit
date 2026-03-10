"""Unit tests for SpacDocsDirective formatting methods."""


class TestFormatDataType:
    """Tests for _format_data_type method."""

    def test_simple_data_type(self, mock_directive, mock_packet_field):
        """Test formatting a simple data type without arrays."""
        field = mock_packet_field(name="test", data_type="uint", bit_length=16)

        result = mock_directive._format_data_type(field)
        assert result == "uint"

    def test_expand_array_notation(self, mock_directive, mock_packet_field):
        """Test formatting an expandable array."""
        field = mock_packet_field(
            name="test", data_type="uint", bit_length=8, array_shape="expand"
        )

        result = mock_directive._format_data_type(field)
        assert result == "uint[]"

    def test_fixed_array_notation_1d(self, mock_directive, mock_packet_field):
        """Test formatting a 1D fixed-size array."""
        field = mock_packet_field(
            name="test", data_type="int", bit_length=16, array_shape=(10,)
        )

        result = mock_directive._format_data_type(field)
        assert result == "int[10]"

    def test_fixed_array_notation_2d(self, mock_directive, mock_packet_field):
        """Test formatting a 2D fixed-size array."""
        field = mock_packet_field(
            name="test", data_type="float", bit_length=32, array_shape=(3, 4)
        )

        result = mock_directive._format_data_type(field)
        assert result == "float[3,4]"

    def test_fixed_array_notation_3d(self, mock_directive, mock_packet_field):
        """Test formatting a 3D fixed-size array."""
        field = mock_packet_field(
            name="test", data_type="uint", bit_length=8, array_shape=(2, 3, 4)
        )

        result = mock_directive._format_data_type(field)
        assert result == "uint[2,3,4]"


class TestCalculateBitOffset:
    """Tests for _calculate_bit_offset method."""

    def test_explicit_offset(self, mock_directive, mock_packet_field):
        """Test that explicit offset is used when set."""
        field = mock_packet_field(
            name="test", data_type="uint", bit_length=16, bit_offset=100
        )

        result = mock_directive._calculate_bit_offset(field, running_offset=50)
        assert result == 100

    def test_running_offset_when_none(self, mock_directive, mock_packet_field):
        """Test that running offset is used when bit_offset is None."""
        field = mock_packet_field(
            name="test", data_type="uint", bit_length=16, bit_offset=None
        )

        result = mock_directive._calculate_bit_offset(field, running_offset=50)
        assert result == 50

    def test_running_offset_when_empty_string(self, mock_directive, mock_packet_field):
        """Test running offset is used when bit_offset is empty string."""
        field = mock_packet_field(
            name="test", data_type="uint", bit_length=16, bit_offset=""
        )

        result = mock_directive._calculate_bit_offset(field, running_offset=75)
        assert result == 75

    def test_zero_offset_is_valid(self, mock_directive, mock_packet_field):
        """Test that explicit zero offset is preserved."""
        field = mock_packet_field(
            name="test", data_type="uint", bit_length=16, bit_offset=0
        )

        result = mock_directive._calculate_bit_offset(field, running_offset=100)
        assert result == 0


class TestFormatBitOffset:
    """Tests for _format_bit_offset method."""

    def test_format_explicit_offset(self, mock_directive, mock_packet_field):
        """Test formatting an explicit bit offset."""
        field = mock_packet_field(
            name="test", data_type="uint", bit_length=16, bit_offset=256
        )

        result = mock_directive._format_bit_offset(field, running_offset=100)
        assert result == "256"

    def test_format_running_offset(self, mock_directive, mock_packet_field):
        """Test formatting with running offset."""
        field = mock_packet_field(
            name="test", data_type="uint", bit_length=16, bit_offset=None
        )

        result = mock_directive._format_bit_offset(field, running_offset=128)
        assert result == "128"


class TestFormatFieldValue:
    """Tests for _format_field_value method."""

    def test_format_string_value(self, mock_directive, mock_packet_field):
        """Test formatting a string attribute."""
        field = mock_packet_field(name="test", data_type="uint", byte_order="big")

        result = mock_directive._format_field_value(field, "_byte_order")
        assert result == "big"

    def test_format_numeric_value(self, mock_directive, mock_packet_field):
        """Test formatting a numeric attribute."""
        field = mock_packet_field(name="test", data_type="uint", bit_length=32)

        result = mock_directive._format_field_value(field, "_bit_length")
        assert result == "32"

    def test_format_none_value(self, mock_directive, mock_packet_field):
        """Test formatting a None value returns empty string."""
        field = mock_packet_field(
            name="test", data_type="uint", bit_length=16, description=None
        )

        result = mock_directive._format_field_value(field, "_description")
        assert result == ""

    def test_format_missing_attribute(self, mock_directive):
        """Test formatting a missing attribute returns empty string."""

        # Create a simple object with limited attributes
        class SimpleField:
            def __init__(self):
                self._name = "test"

        field = SimpleField()

        # The field doesn't have _nonexistent attribute, so getattr returns ""
        result = mock_directive._format_field_value(field, "_nonexistent")
        assert result == ""


class TestGetFormattedValue:
    """Tests for _get_formatted_value method (router)."""

    def test_routes_to_data_type_formatter(self, mock_directive, mock_packet_field):
        """Test data_type attribute routes to specialized formatter."""
        field = mock_packet_field(
            name="test", data_type="uint", bit_length=8, array_shape="expand"
        )

        result = mock_directive._get_formatted_value(
            field, "_data_type", running_offset=0
        )
        assert result == "uint[]"

    def test_routes_to_bit_offset_formatter(self, mock_directive, mock_packet_field):
        """Test bit_offset attribute routes to specialized formatter."""
        field = mock_packet_field(
            name="test", data_type="uint", bit_length=16, bit_offset=None
        )

        result = mock_directive._get_formatted_value(
            field, "_bit_offset", running_offset=64
        )
        assert result == "64"

    def test_routes_to_generic_formatter(self, mock_directive, mock_packet_field):
        """Test that other attributes route to generic formatter."""
        field = mock_packet_field(name="test", data_type="uint", byte_order="little")

        result = mock_directive._get_formatted_value(
            field, "_byte_order", running_offset=0
        )
        assert result == "little"
