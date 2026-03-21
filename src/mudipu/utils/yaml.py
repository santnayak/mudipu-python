"""
YAML utilities for configuration management.
"""
import yaml
from pathlib import Path
from typing import Any, Optional


def load_yaml(path: Path) -> dict:
    """
    Load YAML file.
    
    Args:
        path: Path to YAML file
        
    Returns:
        Parsed YAML data
    """
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def save_yaml(data: dict, path: Path, **kwargs: Any) -> None:
    """
    Save data to YAML file.
    
    Args:
        data: Data to save
        path: Path to save to
        **kwargs: Additional arguments passed to yaml.dump
    """
    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Default kwargs
    default_kwargs = {
        'default_flow_style': False,
        'sort_keys': False,
        'allow_unicode': True,
    }
    default_kwargs.update(kwargs)
    
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, **default_kwargs)


def yaml_string(data: dict, **kwargs: Any) -> str:
    """
    Convert data to YAML string.
    
    Args:
        data: Data to convert
        **kwargs: Additional arguments passed to yaml.dump
        
    Returns:
        YAML string
    """
    default_kwargs = {
        'default_flow_style': False,
        'sort_keys': False,
        'allow_unicode': True,
    }
    default_kwargs.update(kwargs)
    
    return yaml.dump(data, **default_kwargs)


def merge_yaml_configs(*configs: dict) -> dict:
    """
    Merge multiple YAML configurations.
    
    Later configs override earlier ones.
    
    Args:
        *configs: Configuration dictionaries to merge
        
    Returns:
        Merged configuration
    """
    result = {}
    
    for config in configs:
        _deep_merge(result, config)
    
    return result


def _deep_merge(base: dict, update: dict) -> None:
    """
    Deep merge update dict into base dict.
    
    Args:
        base: Base dictionary (modified in place)
        update: Update dictionary
    """
    for key, value in update.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
