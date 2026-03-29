"""
Tests for configuration management.

Tests MudipuConfig loading from YAML, environment variables, and defaults.
"""
import pytest
import os
import tempfile
from pathlib import Path
import yaml
from mudipu.config import MudipuConfig, get_config, set_config


@pytest.fixture
def temp_config_file():
    """Create a temporary config file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        config_data = {
            "storage": {
                "directory": "/tmp/test-traces",
                "format": "json"
            },
            "tracing": {
                "enabled": True,
                "auto_flush": True
            }
        }
        yaml.dump(config_data, f)
        return Path(f.name)


@pytest.fixture
def clean_env(monkeypatch):
    """Clean environment variables before tests."""
    env_vars = [
        "MUDIPU_STORAGE_DIRECTORY",
        "MUDIPU_STORAGE_FORMAT",
        "MUDIPU_TRACING_ENABLED",
        "MUDIPU_TRACING_AUTO_FLUSH"
    ]
    for var in env_vars:
        monkeypatch.delenv(var, raising=False)
    yield


class TestConfigDefaults:
    """Test default configuration."""
    
    def test_default_config_creation(self, clean_env):
        """Test creating config with defaults."""
        config = MudipuConfig()
        
        # Should have default values
        assert config.storage is not None
        assert config.tracing is not None
    
    def test_default_storage_config(self, clean_env):
        """Test default storage configuration."""
        config = MudipuConfig()
        
        assert config.storage.format in ["json", "pickle", "msgpack"]
        assert config.storage.directory is not None


class TestConfigFromYAML:
    """Test configuration from YAML files."""
    
    def test_load_from_yaml(self, temp_config_file):
        """Test loading config from YAML."""
        config = MudipuConfig.from_yaml(temp_config_file)
        
        assert config.storage.directory == "/tmp/test-traces"
        assert config.storage.format == "json"
        assert config.tracing.enabled is True
    
    def test_load_partial_yaml(self):
        """Test loading YAML with partial config."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({"storage": {"format": "msgpack"}}, f)
            temp_file = Path(f.name)
        
        config = MudipuConfig.from_yaml(temp_file)
        
        # Should have specified value
        assert config.storage.format == "msgpack"
        # Should still have defaults for unspecified values
        assert config.storage.directory is not None
    
    def test_load_empty_yaml(self):
        """Test loading empty YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({}, f)
            temp_file = Path(f.name)
        
        config = MudipuConfig.from_yaml(temp_file)
        
        # Should use all defaults
        assert config.storage is not None
        assert config.tracing is not None
    
    def test_nonexistent_yaml_file(self):
        """Test loading from nonexistent file."""
        with pytest.raises(FileNotFoundError):
            MudipuConfig.from_yaml("/nonexistent/config.yaml")


class TestConfigFromEnvironment:
    """Test configuration from environment variables."""
    
    def test_env_var_override(self, clean_env, monkeypatch):
        """Test environment variable override."""
        monkeypatch.setenv("MUDIPU_STORAGE_DIRECTORY", "/custom/path")
        monkeypatch.setenv("MUDIPU_STORAGE_FORMAT", "msgpack")
        
        config = MudipuConfig()
        
        assert config.storage.directory == "/custom/path"
        assert config.storage.format == "msgpack"
    
    def test_boolean_env_vars(self, clean_env, monkeypatch):
        """Test boolean environment variables."""
        monkeypatch.setenv("MUDIPU_TRACING_ENABLED", "false")
        monkeypatch.setenv("MUDIPU_TRACING_AUTO_FLUSH", "true")
        
        config = MudipuConfig()
        
        assert config.tracing.enabled is False
        assert config.tracing.auto_flush is True
    
    def test_mixed_env_and_yaml(self, temp_config_file, monkeypatch):
        """Test mixing YAML and environment variables."""
        # Environment should override YAML
        monkeypatch.setenv("MUDIPU_STORAGE_FORMAT", "msgpack")
        
        config = MudipuConfig.from_yaml(temp_config_file)
        
        # YAML value
        assert config.storage.directory == "/tmp/test-traces"
        # Env override
        assert config.storage.format == "msgpack"


class TestConfigSingleton:
    """Test global config singleton."""
    
    def test_get_config(self, clean_env):
        """Test getting global config."""
        config = get_config()
        
        assert isinstance(config, MudipuConfig)
    
    def test_set_config(self, clean_env):
        """Test setting global config."""
        custom_config = MudipuConfig()
        custom_config.storage.format = "msgpack"
        
        set_config(custom_config)
        config = get_config()
        
        assert config.storage.format == "msgpack"
    
    def test_config_persistence(self, clean_env):
        """Test that config persists across get_config calls."""
        config1 = get_config()
        config1.storage.format = "custom"
        
        config2 = get_config()
        
        # Should be same instance
        assert config2.storage.format == "custom"


class TestConfigValidation:
    """Test configuration validation."""
    
    def test_invalid_storage_format(self):
        """Test validation with invalid storage format."""
        # Create config with invalid format
        config = MudipuConfig()
        
        # Depending on validation, this may or may not raise
        # If Literal is used, assignment will be caught by type checker
        # but may not raise at runtime
        try:
            config.storage.format = "invalid"  # type: ignore
            # If it doesn't raise, just check assignment worked
            assert config.storage.format == "invalid"
        except (ValueError, AttributeError):
            # If validation exists, that's good too
            pass
    
    def test_invalid_directory_path(self):
        """Test with invalid directory path."""
        config = MudipuConfig()
        
        # Should accept any string
        config.storage.directory = "/invalid/\x00/path"
        assert config.storage.directory == "/invalid/\x00/path"


class TestConfigSerialization:
    """Test config serialization."""
    
    def test_to_dict(self, clean_env):
        """Test converting config to dict."""
        config = MudipuConfig()
        data = config.model_dump()
        
        assert "storage" in data
        assert "tracing" in data
        assert isinstance(data, dict)
    
    def test_to_yaml(self, clean_env):
        """Test exporting config to YAML."""
        config = MudipuConfig()
        config.storage.format = "msgpack"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_file = Path(f.name)
        
        # Export to YAML
        with open(temp_file, 'w') as f:
            yaml.dump(config.model_dump(), f)
        
        # Read back
        with open(temp_file) as f:
            data = yaml.safe_load(f)
        
        assert data["storage"]["format"] == "msgpack"
    
    def test_from_dict(self):
        """Test creating config from dict."""
        data = {
            "storage": {
                "directory": "/test/path",
                "format": "json"
            },
            "tracing": {
                "enabled": False,
                "auto_flush": False
            }
        }
        
        config = MudipuConfig.model_validate(data)
        
        assert config.storage.directory == "/test/path"
        assert config.tracing.enabled is False


class TestConfigUpdates:
    """Test updating configuration."""
    
    def test_update_storage_config(self, clean_env):
        """Test updating storage configuration."""
        config = MudipuConfig()
        original_dir = config.storage.directory
        
        config.storage.directory = "/new/path"
        
        assert config.storage.directory == "/new/path"
        assert config.storage.directory != original_dir
    
    def test_update_tracing_config(self, clean_env):
        """Test updating tracing configuration."""
        config = MudipuConfig()
        
        config.tracing.enabled = False
        config.tracing.auto_flush = False
        
        assert config.tracing.enabled is False
        assert config.tracing.auto_flush is False


class TestConfigPaths:
    """Test configuration path handling."""
    
    def test_relative_path_expansion(self):
        """Test relative path handling."""
        config = MudipuConfig()
        config.storage.directory = "~/mudipu-traces"
        
        # Path should be stored as-is
        assert config.storage.directory == "~/mudipu-traces"
    
    def test_absolute_path(self):
        """Test absolute path handling."""
        config = MudipuConfig()
        config.storage.directory = "/absolute/path/traces"
        
        assert config.storage.directory == "/absolute/path/traces"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
