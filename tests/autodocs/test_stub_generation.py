"""Unit tests for stub generation and file operations."""
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

from ccsdspy.packet_types import _BasePacket
from spac_kit.autodocs import copy_static_css
from spac_kit.autodocs import generate_packet_stubs


class TestGeneratePacketStubs:
    """Tests for generate_packet_stubs function."""

    def test_no_modules_configured(self, mock_sphinx_app, caplog):
        """Test behavior when no packet modules are configured."""
        mock_sphinx_app.config.spacdocs_packet_modules = []

        generate_packet_stubs(mock_sphinx_app)

        # Should log warning and return early
        assert "No PACKET_MODULES configured" in caplog.text

    @patch("spac_kit.autodocs.importlib.import_module")
    def test_creates_stub_directory(self, mock_import, mock_sphinx_app, tmp_path):
        """Test that stub directory is created if it doesn't exist."""
        mock_sphinx_app.srcdir = str(tmp_path)
        mock_sphinx_app.config.spacdocs_packet_modules = ["test.module"]

        # Create a mock module with a packet
        mock_module = MagicMock()
        mock_packet = Mock(spec=_BasePacket)
        mock_packet.name = "TestPacket"
        mock_packet._fields = []
        mock_module.test_packet = mock_packet
        mock_module.__dir__ = lambda self: ["test_packet"]
        mock_import.return_value = mock_module

        generate_packet_stubs(mock_sphinx_app)

        # Directory should be created
        stub_dir = tmp_path / "_autopackets"
        assert stub_dir.exists()
        assert stub_dir.is_dir()

    @patch("spac_kit.autodocs.importlib.import_module")
    def test_module_import_failure(self, mock_import, mock_sphinx_app, caplog):
        """Test handling of module import failures."""
        mock_sphinx_app.config.spacdocs_packet_modules = ["nonexistent.module"]
        mock_import.side_effect = ImportError("Module not found")

        generate_packet_stubs(mock_sphinx_app)

        # Should log error
        assert "Failed to import" in caplog.text
        assert "nonexistent.module" in caplog.text

    @patch("spac_kit.autodocs.importlib.import_module")
    def test_creates_stub_for_packet(self, mock_import, mock_sphinx_app, tmp_path):
        """Test that stub file is created for a packet."""
        mock_sphinx_app.srcdir = str(tmp_path)
        mock_sphinx_app.config.spacdocs_packet_modules = ["test.packets"]

        # Create a mock module with a packet
        mock_module = MagicMock()
        mock_packet = Mock(spec=_BasePacket)
        mock_packet.name = "TestPacket"
        mock_module.test_packet = mock_packet
        mock_module.__dir__ = lambda self: ["test_packet"]
        mock_import.return_value = mock_module

        generate_packet_stubs(mock_sphinx_app)

        # Stub file should be created
        stub_dir = tmp_path / "_autopackets"
        stub_files = list(stub_dir.glob("*.rst"))
        assert len(stub_files) > 0

        # Read stub content
        stub_content = stub_files[0].read_text()
        assert "spacdocs::" in stub_content
        assert "test.packets.test_packet" in stub_content

    @patch("spac_kit.autodocs.importlib.import_module")
    def test_does_not_overwrite_unchanged_stub(
        self, mock_import, mock_sphinx_app, tmp_path
    ):
        """Test that stub file is not rewritten if content hasn't changed."""
        mock_sphinx_app.srcdir = str(tmp_path)
        mock_sphinx_app.config.spacdocs_packet_modules = ["test.packets"]

        # Create a mock module with a packet
        mock_module = MagicMock()
        mock_packet = Mock(spec=_BasePacket)
        mock_packet.name = "TestPacket"
        mock_module.test_packet = mock_packet
        mock_module.__dir__ = lambda self: ["test_packet"]
        mock_import.return_value = mock_module

        # First generation
        generate_packet_stubs(mock_sphinx_app)

        stub_dir = tmp_path / "_autopackets"
        stub_files = list(stub_dir.glob("*.rst"))
        first_mtime = stub_files[0].stat().st_mtime

        # Second generation (should not overwrite)
        import time

        time.sleep(0.01)  # Ensure time difference would be detectable
        generate_packet_stubs(mock_sphinx_app)

        second_mtime = stub_files[0].stat().st_mtime
        # File should not have been modified
        assert first_mtime == second_mtime

    @patch("spac_kit.autodocs.importlib.import_module")
    def test_creates_toctree_file(self, mock_import, mock_sphinx_app, tmp_path):
        """Test that toctree index file is created."""
        mock_sphinx_app.srcdir = str(tmp_path)
        mock_sphinx_app.config.spacdocs_packet_modules = ["test.packets"]

        # Create a mock module with a packet
        mock_module = MagicMock()
        mock_packet = Mock(spec=_BasePacket)
        mock_packet.name = "TestPacket"
        mock_module.test_packet = mock_packet
        mock_module.__dir__ = lambda self: ["test_packet"]
        mock_import.return_value = mock_module

        generate_packet_stubs(mock_sphinx_app)

        # Toctree file should be created
        toctree_file = tmp_path / "_packet_index.rst"
        assert toctree_file.exists()

        # Should contain toctree directive
        content = toctree_file.read_text()
        assert ".. toctree::" in content

    @patch("spac_kit.autodocs.importlib.import_module")
    def test_hierarchical_grouping(self, mock_import, mock_sphinx_app, tmp_path):
        """Test that packets are grouped hierarchically in toctree."""
        mock_sphinx_app.srcdir = str(tmp_path)
        mock_sphinx_app.config.spacdocs_packet_modules = [
            "ccsds.mission1.instrument1",
            "ccsds.mission1.instrument2",
            "ccsds.mission2.instrument1",
        ]

        # Create mock modules with packets
        for modpath in mock_sphinx_app.config.spacdocs_packet_modules:
            mock_module = MagicMock()
            mock_packet = Mock(spec=_BasePacket)
            mock_packet.name = f"Packet_{modpath.split('.')[-1]}"
            mock_module.test_packet = mock_packet
            mock_module.__dir__ = lambda self: ["test_packet"]

            def side_effect(name):
                mock_mod = MagicMock()
                mock_pkt = Mock(spec=_BasePacket)
                mock_pkt.name = f"Packet_{name.split('.')[-1]}"
                mock_mod.test_packet = mock_pkt
                mock_mod.__dir__ = lambda self: ["test_packet"]
                return mock_mod

            mock_import.side_effect = side_effect

        generate_packet_stubs(mock_sphinx_app)

        # Toctree should group by parent module
        toctree_file = tmp_path / "_packet_index.rst"
        content = toctree_file.read_text()

        # Should have parent module headers
        assert "ccsds.mission1" in content
        assert "ccsds.mission2" in content

    @patch("spac_kit.autodocs.importlib.import_module")
    def test_skips_non_packet_attributes(self, mock_import, mock_sphinx_app, tmp_path):
        """Test that non-packet attributes are skipped."""
        mock_sphinx_app.srcdir = str(tmp_path)
        mock_sphinx_app.config.spacdocs_packet_modules = ["test.packets"]

        # Create a mock module with mixed attributes
        mock_module = MagicMock()
        mock_packet = Mock(spec=_BasePacket)
        mock_packet.name = "TestPacket"
        mock_module.real_packet = mock_packet
        mock_module.not_a_packet = "just a string"
        mock_module.also_not_packet = 42
        mock_module.__dir__ = lambda self: [
            "real_packet",
            "not_a_packet",
            "also_not_packet",
        ]
        mock_import.return_value = mock_module

        generate_packet_stubs(mock_sphinx_app)

        # Should only create one stub
        stub_dir = tmp_path / "_autopackets"
        stub_files = list(stub_dir.glob("*.rst"))
        assert len(stub_files) == 1

    @patch("spac_kit.autodocs.importlib.import_module")
    def test_handles_packet_name_matches_module(
        self, mock_import, mock_sphinx_app, tmp_path
    ):
        """Test stub naming when packet name matches module name."""
        mock_sphinx_app.srcdir = str(tmp_path)
        mock_sphinx_app.config.spacdocs_packet_modules = ["ccsds.packets"]

        # Create a mock module where packet name matches module name
        mock_module = MagicMock()
        mock_packet = Mock(spec=_BasePacket)
        mock_packet.name = "PacketsPacket"
        mock_module.packets = mock_packet  # Attribute name matches module name
        mock_module.__dir__ = lambda self: ["packets"]
        mock_import.return_value = mock_module

        generate_packet_stubs(mock_sphinx_app)

        # Stub filename should not duplicate the module name
        stub_dir = tmp_path / "_autopackets"
        stub_files = list(stub_dir.glob("*.rst"))
        assert len(stub_files) == 1

        # Filename should be reasonable
        filename = stub_files[0].name
        assert "ccsds_packets" in filename


class TestCopyStaticCSS:
    """Tests for copy_static_css function."""

    def test_creates_static_directory(self, mock_sphinx_app, tmp_path):
        """Test that static directory is created if it doesn't exist."""
        mock_sphinx_app.srcdir = str(tmp_path)
        mock_sphinx_app.config.html_static_path = ["_static"]

        copy_static_css(mock_sphinx_app, None)

        # Directory should be created
        static_dir = tmp_path / "_static"
        assert static_dir.exists()
        assert static_dir.is_dir()

    def test_sets_default_static_path(self, mock_sphinx_app, tmp_path):
        """Test that default static path is set if none configured."""
        mock_sphinx_app.srcdir = str(tmp_path)
        mock_sphinx_app.config.html_static_path = []

        copy_static_css(mock_sphinx_app, None)

        # Should set default path
        assert mock_sphinx_app.config.html_static_path == ["_static"]

        # Directory should be created
        static_dir = tmp_path / "_static"
        assert static_dir.exists()

    @patch("pkg_resources.resource_filename")
    def test_copies_css_files(
        self, mock_resource_filename, mock_sphinx_app, tmp_path, temp_resources_dir
    ):
        """Test that CSS files are copied to static directory."""
        mock_sphinx_app.srcdir = str(tmp_path)
        mock_sphinx_app.config.html_static_path = ["_static"]
        mock_resource_filename.return_value = str(temp_resources_dir)

        copy_static_css(mock_sphinx_app, None)

        # CSS file should be copied
        static_dir = tmp_path / "_static"
        css_file = static_dir / "spac-kit.css"
        assert css_file.exists()
        assert "color: blue" in css_file.read_text()

    @patch("pkg_resources.resource_filename")
    def test_copies_svg_files(
        self, mock_resource_filename, mock_sphinx_app, tmp_path, temp_resources_dir
    ):
        """Test that SVG files are copied to static directory."""
        mock_sphinx_app.srcdir = str(tmp_path)
        mock_sphinx_app.config.html_static_path = ["_static"]
        mock_resource_filename.return_value = str(temp_resources_dir)

        copy_static_css(mock_sphinx_app, None)

        # SVG file should be copied
        static_dir = tmp_path / "_static"
        svg_file = static_dir / "circle-info.svg"
        assert svg_file.exists()
        assert "svg" in svg_file.read_text()

    @patch("pkg_resources.resource_filename")
    def test_does_not_overwrite_unchanged_files(
        self, mock_resource_filename, mock_sphinx_app, tmp_path, temp_resources_dir
    ):
        """Test that files are not copied if content is identical."""
        mock_sphinx_app.srcdir = str(tmp_path)
        mock_sphinx_app.config.html_static_path = ["_static"]
        mock_resource_filename.return_value = str(temp_resources_dir)

        # First copy
        copy_static_css(mock_sphinx_app, None)

        static_dir = tmp_path / "_static"
        css_file = static_dir / "spac-kit.css"
        first_mtime = css_file.stat().st_mtime

        # Second copy
        import time

        time.sleep(0.01)
        copy_static_css(mock_sphinx_app, None)

        second_mtime = css_file.stat().st_mtime
        # File should not have been modified
        assert first_mtime == second_mtime

    @patch("pkg_resources.resource_filename")
    def test_overwrites_changed_files(
        self, mock_resource_filename, mock_sphinx_app, tmp_path, temp_resources_dir
    ):
        """Test that files are overwritten if content has changed."""
        mock_sphinx_app.srcdir = str(tmp_path)
        mock_sphinx_app.config.html_static_path = ["_static"]
        mock_resource_filename.return_value = str(temp_resources_dir)

        # First copy
        copy_static_css(mock_sphinx_app, None)

        # Modify the destination file
        static_dir = tmp_path / "_static"
        css_file = static_dir / "spac-kit.css"
        css_file.write_text(".different { color: red; }")

        # Second copy should overwrite
        copy_static_css(mock_sphinx_app, None)

        # Content should be back to original
        assert "color: blue" in css_file.read_text()

    def test_handles_missing_resources_directory(
        self, mock_sphinx_app, tmp_path, caplog
    ):
        """Test handling when resources directory doesn't exist."""
        mock_sphinx_app.srcdir = str(tmp_path)
        mock_sphinx_app.config.html_static_path = ["_static"]

        with patch(
            "pkg_resources.resource_filename",
            return_value="/nonexistent/path",
        ):
            copy_static_css(mock_sphinx_app, None)

        # Should log warning
        assert "Could not find resources directory" in caplog.text

    def test_fallback_to_local_resources_directory(
        self, mock_sphinx_app, tmp_path, temp_resources_dir
    ):
        """Test fallback to local resources directory when pkg_resources fails."""
        mock_sphinx_app.srcdir = str(tmp_path)
        mock_sphinx_app.config.html_static_path = ["_static"]

        # Mock pkg_resources to raise exception
        with patch(
            "pkg_resources.resource_filename",
            side_effect=Exception("pkg_resources failed"),
        ):
            # Mock os.path.dirname to return our temp resources parent
            with patch(
                "spac_kit.autodocs.os.path.dirname",
                return_value=str(temp_resources_dir.parent),
            ):
                with patch("spac_kit.autodocs.os.path.isdir", return_value=True):
                    with patch("spac_kit.autodocs.os.listdir", return_value=[]):
                        # Should not raise, uses fallback
                        copy_static_css(mock_sphinx_app, None)
