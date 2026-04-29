"""Agentmark manifest validator utility."""

import re
from datetime import datetime
from typing import Dict, List, Tuple, Any


def validate_manifest(manifest: dict) -> Tuple[bool, List[str]]:
    """
    Validate an agentmark manifest JSON object.
    
    Args:
        manifest: Dictionary containing manifest data
        
    Returns:
        Tuple of (is_valid, list_of_errors)
        - (True, []) if valid
        - (False, [list of errors]) if invalid
    """
    errors = []
    
    # Required fields
    required_fields = [
        'version',
        'provider', 
        'model',
        'output_hash',
        'challenge_token',
        'pipeline_key',
        'timestamp',
        'signature'
    ]
    
    # Check for missing required fields
    for field in required_fields:
        if field not in manifest:
            errors.append(f"Missing required field: {field}")
        elif manifest[field] is None:
            errors.append(f"Field '{field}' cannot be null")
        elif not isinstance(manifest[field], str):
            errors.append(f"Field '{field}' must be a string")
        elif not manifest[field].strip():
            errors.append(f"Field '{field}' cannot be empty")
    
    # Validate output_hash format
    if 'output_hash' in manifest and isinstance(manifest['output_hash'], str):
        if not manifest['output_hash'].startswith('sha256:'):
            errors.append("Field 'output_hash' must start with 'sha256:'")
        else:
            # Check if the hash part after 'sha256:' is valid hex
            hash_part = manifest['output_hash'][7:]  # Remove 'sha256:' prefix
            if not re.match(r'^[a-fA-F0-9]{64}$', hash_part):
                errors.append("Field 'output_hash' must contain a valid 64-character hex hash after 'sha256:'")
    
    # Validate timestamp format (ISO 8601)
    if 'timestamp' in manifest and isinstance(manifest['timestamp'], str):
        try:
            # Try to parse as ISO 8601 format
            datetime.fromisoformat(manifest['timestamp'].replace('Z', '+00:00'))
        except ValueError:
            errors.append("Field 'timestamp' must be in valid ISO 8601 format")
    
    return len(errors) == 0, errors
