"""Pytest fixtures for autodocs tests."""
import tempfile
from unittest.mock import MagicMock
from unittest.mock import Mock

import pytest
from ccsdspy.packet_types import _BasePacket
from spac_kit.autodocs import SpacDocsDirective


@pytest.fixture
def mock_packet_field():
    """Create a mock PacketField with common attributes."""

    def _make_field(
        name="test_field",
        data_type="uint",
        bit_length=16,
        bit_offset=None,
        byte_order="big",
        field_type=None,
        array_shape=None,
        array_order=None,
        description=None,
    ):
        field = Mock()
        field._name = name
        field._data_type = data_type
        field._bit_length = bit_length
        field._bit_offset = bit_offset
        field._byte_order = byte_order
        field._field_type = field_type
        field._array_shape = array_shape
        field._array_order = array_order
        field._description = description
        return field

    return _make_field


@pytest.fixture
def mock_simple_packet(mock_packet_field):
    """Create a simple mock packet with a few fields."""
    packet = Mock(spec=_BasePacket)
    packet.name = "TestPacket"
    packet._fields = [
        mock_packet_field(name="field1", data_type="uint", bit_length=8),
        mock_packet_field(name="field2", data_type="int", bit_length=16),
        mock_packet_field(name="field3", data_type="float", bit_length=32),
    ]
    return packet


@pytest.fixture
def mock_array_packet(mock_packet_field):
    """Create a mock packet with array fields."""
    packet = Mock(spec=_BasePacket)
    packet.name = "ArrayPacket"
    packet._fields = [
        mock_packet_field(
            name="expandable_array",
            data_type="uint",
            bit_length=8,
            array_shape="expand",
        ),
        mock_packet_field(
            name="fixed_array",
            data_type="int",
            bit_length=16,
            array_shape=(3, 4),
        ),
        mock_packet_field(
            name="simple_field",
            data_type="float",
            bit_length=32,
        ),
    ]
    return packet


@pytest.fixture
def mock_packet_with_descriptions(mock_packet_field):
    """Create a mock packet with field descriptions."""
    packet = Mock(spec=_BasePacket)
    packet.name = "DocumentedPacket"
    packet._fields = [
        mock_packet_field(
            name="status",
            data_type="uint",
            bit_length=8,
            description="Status code indicating system health",
        ),
        mock_packet_field(
            name="temperature",
            data_type="float",
            bit_length=32,
            description="Temperature in Kelvin",
        ),
    ]
    return packet


@pytest.fixture
def mock_packet_with_explicit_offsets(mock_packet_field):
    """Create a mock packet with explicitly set bit offsets."""
    packet = Mock(spec=_BasePacket)
    packet.name = "ExplicitOffsetPacket"
    packet._fields = [
        mock_packet_field(name="field1", data_type="uint", bit_length=8, bit_offset=0),
        mock_packet_field(
            name="field2", data_type="uint", bit_length=16, bit_offset=100
        ),
        mock_packet_field(
            name="field3", data_type="uint", bit_length=8, bit_offset=200
        ),
    ]
    return packet


@pytest.fixture
def mock_sphinx_app():
    """Create a mock Sphinx application object."""
    app = MagicMock()
    app.srcdir = tempfile.mkdtemp()
    app.config = MagicMock()
    app.config.spacdocs_packet_modules = []
    app.config.html_static_path = []
    return app


@pytest.fixture
def mock_sphinx_config():
    """Create a mock Sphinx config object."""
    config = MagicMock()
    config.spacdocs_packet_modules = []
    config.html_static_path = []
    return config


@pytest.fixture
def temp_resources_dir(tmp_path):
    """Create a temporary resources directory with test files."""
    resources = tmp_path / "resources"
    resources.mkdir()

    # Create a dummy CSS file
    css_file = resources / "spac-kit.css"
    css_file.write_text(".test { color: blue; }")

    # Create a dummy SVG file
    svg_file = resources / "circle-info.svg"
    svg_file.write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>')

    return resources


@pytest.fixture
def temp_test_module(tmp_path, mock_simple_packet):
    """Create a temporary Python module with a mock packet for testing."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()

    # Create __init__.py
    init_file = module_dir / "__init__.py"
    init_file.write_text(
        """from ccsdspy import VariableLength, PacketField

# This would normally be a real packet definition
test_packet = None  # Will be replaced with mock in tests
"""
    )

    return module_dir


@pytest.fixture
def mock_directive():
    """Create a properly mocked SpacDocsDirective instance.

    This fixture creates a directive with all the necessary Sphinx internals
    mocked, allowing us to test the directive's methods without a full
    Sphinx environment.
    """
    # Mock state_machine and state
    mock_state_machine = MagicMock()
    mock_state_machine.reporter = MagicMock()
    mock_state = MagicMock()

    # Create the directive with mocked Sphinx components
    directive = SpacDocsDirective(
        name="spacdocs",
        arguments=["test.module.packet"],
        options={},
        content="",
        lineno=0,
        content_offset=0,
        block_text="",
        state=mock_state,
        state_machine=mock_state_machine,
    )

    return directive
