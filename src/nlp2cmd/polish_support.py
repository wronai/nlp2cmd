
"""
Polish Language Support Module for NLP2CMD
Provides Polish language patterns and mappings
"""

import json
import re
from pathlib import Path

class PolishLanguageSupport:
    """Polish language support for NLP2CMD"""
    
    def __init__(self):
        self.patterns = {}
        self.intent_mappings = {}
        self.table_mappings = {}
        self.domain_weights = {}
        self._load_patterns()
    
    def _load_patterns(self):
        """Load Polish language patterns"""
        try:
            # Load Polish shell patterns
            patterns_file = Path("polish_shell_patterns.json")
            if patterns_file.exists():
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    self.patterns = json.load(f)
            
            # Load Polish intent mappings
            intent_file = Path("polish_intent_mappings.json")
            if intent_file.exists():
                with open(intent_file, 'r', encoding='utf-8') as f:
                    self.intent_mappings = json.load(f)
            
            # Load Polish table mappings
            table_file = Path("polish_table_mappings.json")
            if table_file.exists():
                with open(table_file, 'r', encoding='utf-8') as f:
                    self.table_mappings = json.load(f)
            
            # Load domain weights
            weights_file = Path("domain_weights.json")
            if weights_file.exists():
                with open(weights_file, 'r', encoding='utf-8') as f:
                    self.domain_weights = json.load(f)
                    
        except Exception as e:
            print(f"Error loading Polish patterns: {e}")
    
    def normalize_polish_text(self, text):
        """Normalize Polish text for better matching"""
        # Convert to lowercase
        text = text.lower()
        
        # Handle common Polish diacritics variations
        diacritic_map = {
            'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n',
            'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z',
            'Ą': 'a', 'Ć': 'c', 'Ę': 'e', 'Ł': 'l', 'Ń': 'n',
            'Ó': 'o', 'Ś': 's', 'Ź': 'z', 'Ż': 'z'
        }
        
        for polish, latin in diacritic_map.items():
            text = text.replace(polish, latin)
        
        return text
    
    def match_polish_patterns(self, text, domain):
        """Match Polish patterns for given domain"""
        if domain not in self.patterns:
            return []
        
        matches = []
        normalized_text = self.normalize_polish_text(text)
        
        for category, patterns in self.patterns.items():
            for pattern in patterns:
                try:
                    if re.search(pattern, normalized_text, re.IGNORECASE):
                        matches.append({
                            'category': category,
                            'pattern': pattern,
                            'match': True
                        })
                except re.error:
                    continue
        
        return matches
    
    def translate_polish_intent(self, text):
        """Translate Polish intent to English"""
        normalized_text = self.normalize_polish_text(text)
        
        for polish, english in self.intent_mappings.items():
            if polish in normalized_text:
                return english
        
        return None
    
    def translate_polish_table(self, text):
        """Translate Polish table name to English"""
        normalized_text = self.normalize_polish_text(text)
        
        for polish_pattern, english_table in self.table_mappings.items():
            try:
                if re.search(polish_pattern, normalized_text, re.IGNORECASE):
                    return english_table
            except re.error:
                continue
        
        return None
    
    def get_domain_weight(self, domain):
        """Get domain weight for Polish text"""
        return self.domain_weights.get(domain, {}).get("base_weight", 1.0)
    
    def enhance_domain_detection(self, text, base_domain):
        """Enhance domain detection with Polish patterns"""
        # Check if Polish patterns suggest a different domain
        polish_matches = self.match_polish_patterns(text, "shell")
        
        if polish_matches and base_domain == "sql":
            # Polish file operations detected, prefer shell
            return "shell"
        
        return base_domain
    
    def enhance_intent_detection(self, text, base_intent):
        """Enhance intent detection with Polish mappings"""
        # Try to translate Polish intent
        translated_intent = self.translate_polish_intent(text)
        
        if translated_intent:
            return translated_intent
        
        return base_intent

# Global instance
polish_support = PolishLanguageSupport()

def get_polish_support():
    """Get Polish language support instance"""
    return polish_support
