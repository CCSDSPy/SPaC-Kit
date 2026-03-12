"""Integration tests for autodocs module.

These tests verify the end-to-end functionality of the autodocs extension.
"""
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

from ccsdspy.packet_types import _BasePacket
from spac_kit.autodocs import generate_packet_stubs
from spac_kit.autodocs import setup
from spac_kit.autodocs import SpacDocsDirective


class TestEndToEndDocGeneration:
    """Integration tests for complete documentation generation."""

    def test_full_directive_execution(self, mock_directive, mock_simple_packet):
        """Test complete execution of spacdocs directive."""
        # Mock the packet loading to return our fixture
        with patch.object(
            mock_directive, "_load_packet", return_value=mock_simple_packet
        ):
            result = mock_directive.run()

        # Should return a list of nodes
        assert isinstance(result, list)
        assert len(result) > 0

        # First node should be a desc node
        from sphinx import addnodes

        assert isinstance(result[0], addnodes.desc)

    def test_packet_with_all_field_types(
        self,
        mock_directive,
        mock_packet_field,
        mock_array_packet,
        mock_packet_with_descriptions,
    ):
        """Test handling packet with diverse field types."""

        # Create a complex packet with various field types
        complex_packet = Mock(spec=_BasePacket)
        complex_packet.name = "ComplexPacket"
        complex_packet._fields = [
            mock_packet_field(
                name="simple_uint",
                data_type="uint",
                bit_length=8,
                description="Simple unsigned integer",
            ),
            mock_packet_field(
                name="signed_int",
                data_type="int",
                bit_length=16,
                bit_offset=None,
            ),
            mock_packet_field(
                name="float_field",
                data_type="float",
                bit_length=32,
                array_shape=None,
            ),
            mock_packet_field(
                name="expand_array",
                data_type="uint",
                bit_length=8,
                array_shape="expand",
                description="Variable length array",
            ),
            mock_packet_field(
                name="fixed_array_2d",
                data_type="int",
                bit_length=16,
                array_shape=(3, 4),
                array_order="C",
            ),
            mock_packet_field(
                name="explicit_offset_field",
                data_type="uint",
                bit_length=8,
                bit_offset=1000,
            ),
        ]

        with patch.object(mock_directive, "_load_packet", return_value=complex_packet):
            result = mock_directive.run()

        # Should successfully generate documentation
        assert len(result) > 0

        # Extract the content node
        desc_node = result[0]
        content = desc_node.children[1]

        # Content should have summary table and detail sections
        assert len(content.children) > 0

    @patch("spac_kit.autodocs.importlib.import_module")
    def test_full_stub_generation_workflow(self, mock_import, tmp_path):
        """Test complete stub generation workflow."""
        # Create mock Sphinx app
        mock_app = MagicMock()
        mock_app.srcdir = str(tmp_path)
        mock_app.config = MagicMock()
        mock_app.config.spacdocs_packet_modules = ["test.packets", "test.more_packets"]

        # Create mock modules with packets
        def create_mock_module(modname):
            mock_module = MagicMock()
            mock_packet = Mock(spec=_BasePacket)
            mock_packet.name = f"Packet_{modname.split('.')[-1]}"
            mock_packet._fields = []
            setattr(mock_module, f"pkt_{modname.split('.')[-1]}", mock_packet)
            mock_module.__dir__ = lambda self: [f"pkt_{modname.split('.')[-1]}"]
            return mock_module

        mock_import.side_effect = lambda name: create_mock_module(name)

        # Run stub generation
        generate_packet_stubs(mock_app)

        # Verify stub files were created
        stub_dir = tmp_path / "_autopackets"
        assert stub_dir.exists()

        stub_files = list(stub_dir.glob("*.rst"))
        assert len(stub_files) == 2

        # Verify toctree file was created
        toctree_file = tmp_path / "_packet_index.rst"
        assert toctree_file.exists()

        toctree_content = toctree_file.read_text()
        assert ".. toctree::" in toctree_content
        assert "_autopackets/" in toctree_content

    def test_setup_and_directive_integration(self):
        """Test that setup properly configures the directive."""
        mock_app = MagicMock()

        # Run setup
        result = setup(mock_app)

        # Verify setup completed successfully
        assert result["version"] is not None

        # Verify directive was registered
        mock_app.add_directive.assert_called_once()
        directive_name, directive_class = mock_app.add_directive.call_args[0]

        assert directive_name == "spacdocs"
        assert directive_class == SpacDocsDirective


class TestEdgeCases:
    """Integration tests for edge cases and error handling."""

    def test_empty_packet_no_fields(self, mock_directive):
        """Test handling packet with no fields."""
        # Create empty packet
        empty_packet = Mock(spec=_BasePacket)
        empty_packet.name = "EmptyPacket"
        empty_packet._fields = []

        with patch.object(mock_directive, "_load_packet", return_value=empty_packet):
            result = mock_directive.run()

        # Should still generate basic documentation
        assert len(result) > 0

    def test_packet_with_none_values(self, mock_directive, mock_packet_field):
        """Test handling fields with None values."""
        # Create packet with fields having None values
        packet = Mock(spec=_BasePacket)
        packet.name = "NonePacket"
        packet._fields = [
            mock_packet_field(
                name="field1",
                data_type="uint",
                bit_length=8,
                bit_offset=None,
                description=None,
                array_shape=None,
            ),
        ]

        with patch.object(mock_directive, "_load_packet", return_value=packet):
            result = mock_directive.run()

        # Should handle None values gracefully
        assert len(result) > 0

    def test_packet_with_zero_bit_length(self, mock_directive, mock_packet_field):
        """Test handling fields with zero bit length."""
        packet = Mock(spec=_BasePacket)
        packet.name = "ZeroBitPacket"
        packet._fields = [
            mock_packet_field(name="zero_field", data_type="uint", bit_length=0),
        ]

        with patch.object(mock_directive, "_load_packet", return_value=packet):
            result = mock_directive.run()

        # Should handle gracefully
        assert len(result) > 0

    def test_running_offset_accumulation(self, mock_directive, mock_packet_field):
        """Test that running offset accumulates correctly across fields."""
        # Create packet with multiple fields
        packet = Mock(spec=_BasePacket)
        packet.name = "OffsetPacket"
        packet._fields = [
            mock_packet_field(
                name="field1", data_type="uint", bit_length=8, bit_offset=None
            ),
            mock_packet_field(
                name="field2", data_type="uint", bit_length=16, bit_offset=None
            ),
            mock_packet_field(
                name="field3", data_type="uint", bit_length=32, bit_offset=None
            ),
        ]

        with patch.object(mock_directive, "_load_packet", return_value=packet):
            # Create summary and detail content
            (
                summary_table,
                detail_sections,
            ) = mock_directive._create_summary_and_detail_content(packet)

        # Verify that detail sections were created
        assert len(detail_sections) == 3

        # Running offsets should be: 0, 8, 24
        # (field1: 0-7, field2: 8-23, field3: 24-55)

    @patch("spac_kit.autodocs.importlib.import_module")
    def test_module_with_no_packets(self, mock_import, mock_sphinx_app, caplog):
        """Test handling module that has no packet definitions."""
        mock_sphinx_app.config.spacdocs_packet_modules = ["test.empty_module"]

        # Create module with no packets
        mock_module = MagicMock()
        mock_module.some_var = "not a packet"
        mock_module.another_var = 42
        mock_module.__dir__ = lambda self: ["some_var", "another_var"]
        mock_import.return_value = mock_module

        generate_packet_stubs(mock_sphinx_app)

        # Should log warning
        assert "No _BasePacket instances found" in caplog.text


class TestRealWorldScenarios:
    """Integration tests simulating real-world usage scenarios."""

    @patch("spac_kit.autodocs.importlib.import_module")
    def test_multi_mission_packet_organization(self, mock_import, tmp_path):
        """Test organizing packets from multiple missions."""
        mock_app = MagicMock()
        mock_app.srcdir = str(tmp_path)
        mock_app.config = MagicMock()
        mock_app.config.spacdocs_packet_modules = [
            "ccsds.europa.mag",
            "ccsds.europa.eis",
            "ccsds.europa.maspex",
            "ccsds.mars2020.pixl",
            "ccsds.mars2020.sherloc",
        ]

        # Create mock modules
        def create_mission_module(modpath):
            mock_module = MagicMock()
            mock_packet = Mock(spec=_BasePacket)
            instrument = modpath.split(".")[-1]
            mock_packet.name = f"{instrument}_telemetry"
            mock_packet._fields = []
            setattr(mock_module, f"{instrument}_pkt", mock_packet)
            mock_module.__dir__ = lambda self: [f"{instrument}_pkt"]
            return mock_module

        mock_import.side_effect = lambda name: create_mission_module(name)

        generate_packet_stubs(mock_app)

        # Verify hierarchical organization
        toctree_file = tmp_path / "_packet_index.rst"
        content = toctree_file.read_text()

        # Should have mission-level grouping
        assert "ccsds.europa" in content
        assert "ccsds.mars2020" in content

        # Should have instrument-level grouping
        assert "mag" in content or "eis" in content or "maspex" in content
        assert "pixl" in content or "sherloc" in content

    def test_documented_packet_with_special_characters(
        self, mock_directive, mock_packet_field
    ):
        """Test handling descriptions with special characters."""
        packet = Mock(spec=_BasePacket)
        packet.name = "SpecialCharsPacket"
        packet._fields = [
            mock_packet_field(
                name="field1",
                data_type="uint",
                bit_length=8,
                description='Field with "quotes" and <html> & special chars',
            ),
        ]

        with patch.object(mock_directive, "_load_packet", return_value=packet):
            result = mock_directive.run()

        # Should handle special characters without errors
        assert len(result) > 0
