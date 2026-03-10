"""Unit tests for Sphinx extension setup."""
from unittest.mock import MagicMock

from spac_kit.autodocs import setup


class TestSetup:
    """Tests for the setup function."""

    def test_setup_returns_metadata(self):
        """Test that setup returns proper extension metadata."""
        mock_app = MagicMock()

        result = setup(mock_app)

        # Should return a dictionary with metadata
        assert isinstance(result, dict)
        assert "version" in result
        assert "parallel_read_safe" in result
        assert "parallel_write_safe" in result

    def test_setup_parallel_safe_flags(self):
        """Test that parallel processing is enabled."""
        mock_app = MagicMock()

        result = setup(mock_app)

        # Should be safe for parallel processing
        assert result["parallel_read_safe"] is True
        assert result["parallel_write_safe"] is True

    def test_setup_adds_directive(self):
        """Test that setup registers the spacdocs directive."""
        mock_app = MagicMock()

        setup(mock_app)

        # Should register directive
        mock_app.add_directive.assert_called_once()
        call_args = mock_app.add_directive.call_args
        assert call_args[0][0] == "spacdocs"

    def test_setup_adds_config_value(self):
        """Test that setup adds configuration value."""
        mock_app = MagicMock()

        setup(mock_app)

        # Should add config value
        mock_app.add_config_value.assert_called_once()
        call_args = mock_app.add_config_value.call_args
        assert call_args[0][0] == "spacdocs_packet_modules"
        assert call_args[0][1] == []  # Default value
        assert call_args[0][2] == "env"  # Rebuild type

    def test_setup_adds_css_file(self):
        """Test that setup adds CSS file reference."""
        mock_app = MagicMock()

        setup(mock_app)

        # Should add CSS file
        mock_app.add_css_file.assert_called_once()
        call_args = mock_app.add_css_file.call_args
        assert call_args[0][0] == "spac-kit.css"

    def test_setup_connects_builder_inited(self):
        """Test that setup connects to builder-inited event."""
        mock_app = MagicMock()

        setup(mock_app)

        # Should connect to builder-inited event
        event_names = [call[0][0] for call in mock_app.connect.call_args_list]
        assert "builder-inited" in event_names

        # Should connect generate_packet_stubs to the event
        for call in mock_app.connect.call_args_list:
            if call[0][0] == "builder-inited":
                # Second argument should be the callback function
                callback = call[0][1]
                assert callable(callback)
                assert callback.__name__ == "generate_packet_stubs"

    def test_setup_connects_config_inited(self):
        """Test that setup connects to config-inited event."""
        mock_app = MagicMock()

        setup(mock_app)

        # Should connect to config-inited event
        event_names = [call[0][0] for call in mock_app.connect.call_args_list]
        assert "config-inited" in event_names

        # Should connect copy_static_css to the event
        for call in mock_app.connect.call_args_list:
            if call[0][0] == "config-inited":
                callback = call[0][1]
                assert callable(callback)
                assert callback.__name__ == "copy_static_css"

    def test_setup_call_sequence(self):
        """Test the order of setup operations."""
        mock_app = MagicMock()

        setup(mock_app)

        # Verify all setup calls were made
        assert mock_app.add_directive.called
        assert mock_app.add_config_value.called
        assert mock_app.add_css_file.called
        assert mock_app.connect.called

        # Should have two connect calls
        assert mock_app.connect.call_count == 2
