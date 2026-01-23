"""
Form data loader from .env and data/*.json files.

Loads form field values from environment variables and JSON configuration files.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional


class FormDataLoader:
    """
    Loads form field data from multiple sources:
    1. .env file (for sensitive data like email, name, phone)
    2. data/*.json files (for field mappings and default values)
    """
    
    # Common field name mappings to env variables
    FIELD_ENV_MAPPINGS = {
        # Name fields
        'imię': 'FORM_NAME',
        'imie': 'FORM_NAME',
        'name': 'FORM_NAME',
        'first_name': 'FORM_NAME',
        'firstname': 'FORM_NAME',
        'your-name': 'FORM_NAME',
        'nazwa': 'FORM_NAME',
        
        # Last name
        'nazwisko': 'FORM_LASTNAME',
        'surname': 'FORM_LASTNAME',
        'last_name': 'FORM_LASTNAME',
        'lastname': 'FORM_LASTNAME',
        
        # Email fields
        'email': 'FORM_EMAIL',
        'e-mail': 'FORM_EMAIL',
        'adres e-mail': 'FORM_EMAIL',
        'your-email': 'FORM_EMAIL',
        'mail': 'FORM_EMAIL',
        
        # Phone fields
        'telefon': 'FORM_PHONE',
        'phone': 'FORM_PHONE',
        'numer telefonu': 'FORM_PHONE',
        'tel': 'FORM_PHONE',
        'mobile': 'FORM_PHONE',
        
        # Message fields
        'wiadomość': 'FORM_MESSAGE',
        'wiadomosc': 'FORM_MESSAGE',
        'message': 'FORM_MESSAGE',
        'your-message': 'FORM_MESSAGE',
        'treść': 'FORM_MESSAGE',
        'tresc': 'FORM_MESSAGE',
        'komentarz': 'FORM_MESSAGE',
        'comment': 'FORM_MESSAGE',
        
        # Subject
        'temat': 'FORM_SUBJECT',
        'subject': 'FORM_SUBJECT',
        
        # Company
        'firma': 'FORM_COMPANY',
        'company': 'FORM_COMPANY',
        'organization': 'FORM_COMPANY',
        
        # Address
        'adres': 'FORM_ADDRESS',
        'address': 'FORM_ADDRESS',
        
        # City
        'miasto': 'FORM_CITY',
        'city': 'FORM_CITY',
        
        # Website
        'strona': 'FORM_WEBSITE',
        'website': 'FORM_WEBSITE',
        'url': 'FORM_WEBSITE',
    }
    
    def __init__(self, data_dir: str = "./data", env_file: str = ".env"):
        self.data_dir = Path(data_dir)
        self.env_file = Path(env_file)
        self._env_data: dict[str, str] = {}
        self._json_data: dict[str, Any] = {}
        self._field_values: dict[str, str] = {}
        
        self._load_env()
        self._load_json_files()
        self._build_field_values()
    
    def _load_env(self) -> None:
        """Load environment variables from .env file."""
        # First, load from .env file if it exists
        if self.env_file.exists():
            with open(self.env_file) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        key, _, value = line.partition('=')
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        self._env_data[key] = value
        
        # Also check current environment variables
        for key in os.environ:
            if key.startswith('FORM_'):
                self._env_data[key] = os.environ[key]
    
    def _load_json_files(self) -> None:
        """Load all JSON files from data directory."""
        if not self.data_dir.exists():
            return
        
        # Load form_data.json specifically if it exists
        form_data_file = self.data_dir / "form_data.json"
        if form_data_file.exists():
            try:
                with open(form_data_file) as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self._json_data.update(data)
            except Exception:
                pass
        
        # Load any other JSON files that might contain form data
        for json_file in self.data_dir.glob("*.json"):
            if json_file.name == "form_data.json":
                continue  # Already loaded
            try:
                with open(json_file) as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        # Check if it has form-related keys
                        if any(k.lower() in ['forms', 'form_fields', 'fields', 'defaults'] for k in data.keys()):
                            self._json_data[json_file.stem] = data
            except Exception:
                continue
    
    def _build_field_values(self) -> None:
        """Build field values dictionary from all sources."""
        # Priority: .env > form_data.json > other json files
        
        # Load from JSON first (lower priority)
        if 'defaults' in self._json_data:
            for key, value in self._json_data['defaults'].items():
                self._field_values[key.lower()] = str(value)
        
        if 'fields' in self._json_data:
            for key, value in self._json_data['fields'].items():
                self._field_values[key.lower()] = str(value)
        
        # Load from env (higher priority)
        for field_name, env_key in self.FIELD_ENV_MAPPINGS.items():
            if env_key in self._env_data:
                self._field_values[field_name.lower()] = self._env_data[env_key]
    
    def get_value_for_field(
        self,
        field_name: Optional[str] = None,
        field_id: Optional[str] = None,
        field_label: Optional[str] = None,
        field_placeholder: Optional[str] = None,
        field_type: Optional[str] = None,
    ) -> Optional[str]:
        """
        Get value for a form field based on its attributes.
        
        Tries to match field by:
        1. Exact field name/id/label match
        2. Partial match in mappings
        3. Field type defaults
        """
        # Try exact matches first
        candidates = [
            field_name,
            field_id,
            field_label,
            field_placeholder,
        ]
        
        for candidate in candidates:
            if not candidate:
                continue
            candidate_lower = candidate.lower().strip()
            
            # Direct match in field values
            if candidate_lower in self._field_values:
                return self._field_values[candidate_lower]
            
            # Check env mappings
            if candidate_lower in self.FIELD_ENV_MAPPINGS:
                env_key = self.FIELD_ENV_MAPPINGS[candidate_lower]
                if env_key in self._env_data:
                    return self._env_data[env_key]
        
        # Try partial matching
        for candidate in candidates:
            if not candidate:
                continue
            candidate_lower = candidate.lower().strip()
            
            for mapping_key, env_key in self.FIELD_ENV_MAPPINGS.items():
                if mapping_key in candidate_lower or candidate_lower in mapping_key:
                    if env_key in self._env_data:
                        return self._env_data[env_key]
        
        # Type-based defaults
        if field_type == 'email':
            return self._env_data.get('FORM_EMAIL')
        elif field_type == 'tel':
            return self._env_data.get('FORM_PHONE')
        
        return None
    
    def get_all_values(self) -> dict[str, str]:
        """Get all loaded form values."""
        return self._field_values.copy()
    
    def get_env_value(self, key: str) -> Optional[str]:
        """Get specific env value."""
        return self._env_data.get(key)
    
    def has_data(self) -> bool:
        """Check if any form data is available."""
        return bool(self._env_data) or bool(self._field_values)


def create_example_env_file(path: str = ".env.example") -> None:
    """Create example .env file with form field templates."""
    content = """# Form Data Configuration
# Uncomment and fill in values for automatic form filling

# Personal Information
FORM_NAME=Jan Kowalski
FORM_LASTNAME=Kowalski
FORM_EMAIL=jan.kowalski@example.com
FORM_PHONE=+48 123 456 789

# Message Content
FORM_MESSAGE=Dzień dobry, chciałbym uzyskać więcej informacji.
FORM_SUBJECT=Zapytanie

# Business Information
# FORM_COMPANY=Moja Firma Sp. z o.o.
# FORM_ADDRESS=ul. Przykładowa 1
# FORM_CITY=Warszawa
# FORM_WEBSITE=https://example.com
"""
    with open(path, 'w') as f:
        f.write(content)


def create_example_form_data_json(path: str = "./data/form_data.json") -> None:
    """Create example form_data.json file."""
    data = {
        "defaults": {
            "imię": "Jan",
            "email": "jan@example.com",
            "telefon": "+48 123 456 789",
            "wiadomość": "Dzień dobry, proszę o kontakt."
        },
        "sites": {
            "prototypowanie.pl": {
                "Imię": "Jan Kowalski",
                "Adres e-mail": "kontakt@example.com",
                "Wiadomość": "Dzień dobry, jestem zainteresowany współpracą."
            }
        }
    }
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
