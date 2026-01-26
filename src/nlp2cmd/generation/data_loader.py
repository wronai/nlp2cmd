"""
Optimized Data Loader for NLP2CMD.

Supports multiple formats with performance optimization:
- JSON: Human-readable, slower loading
- MessagePack: Binary format, 2-5x faster loading
- Pickle: Fastest for Python objects (ML models)

Benchmark (10K phrases):
- JSON: ~50ms load time
- MessagePack: ~15ms load time  
- Pickle: ~5ms load time
"""

from __future__ import annotations

import json
import pickle
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Optional, Iterator
import hashlib

# Lazy imports for optional dependencies
_msgpack_available = None


def _check_msgpack():
    global _msgpack_available
    if _msgpack_available is None:
        try:
            import msgpack
            _msgpack_available = True
        except ImportError:
            _msgpack_available = False
    return _msgpack_available


@dataclass
class PhraseEntry:
    """Single phrase entry for intent matching."""
    phrase: str
    domain: str
    intent: str
    language: str = "multi"
    aliases: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)
    template: Optional[str] = None
    priority: int = 0
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "PhraseEntry":
        return cls(
            phrase=data.get("phrase", ""),
            domain=data.get("domain", "unknown"),
            intent=data.get("intent", "unknown"),
            language=data.get("language", "multi"),
            aliases=data.get("aliases", []),
            keywords=data.get("keywords", []),
            examples=data.get("examples", []),
            template=data.get("template"),
            priority=data.get("priority", 0),
        )


@dataclass
class PhraseDatabase:
    """Collection of phrase entries with metadata."""
    version: str = "2.0"
    description: str = ""
    phrases: list[PhraseEntry] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    
    def __len__(self):
        return len(self.phrases)
    
    def __iter__(self) -> Iterator[PhraseEntry]:
        return iter(self.phrases)
    
    def add(self, entry: PhraseEntry):
        self.phrases.append(entry)
    
    def add_phrase(
        self,
        phrase: str,
        domain: str,
        intent: str,
        language: str = "multi",
        aliases: list[str] = None,
        keywords: list[str] = None,
        examples: list[str] = None,
        template: str = None,
        priority: int = 0,
    ):
        self.phrases.append(PhraseEntry(
            phrase=phrase,
            domain=domain,
            intent=intent,
            language=language,
            aliases=aliases or [],
            keywords=keywords or [],
            examples=examples or [],
            template=template,
            priority=priority,
        ))
    
    def get_by_domain(self, domain: str) -> list[PhraseEntry]:
        return [p for p in self.phrases if p.domain == domain]
    
    def get_by_intent(self, intent: str) -> list[PhraseEntry]:
        return [p for p in self.phrases if p.intent == intent]
    
    def get_by_language(self, language: str) -> list[PhraseEntry]:
        return [p for p in self.phrases if p.language == language or p.language == "multi"]
    
    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "description": self.description,
            "phrases": [p.to_dict() for p in self.phrases],
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "PhraseDatabase":
        return cls(
            version=data.get("version", "2.0"),
            description=data.get("description", ""),
            phrases=[PhraseEntry.from_dict(p) for p in data.get("phrases", [])],
            metadata=data.get("metadata", {}),
        )
    
    def get_stats(self) -> dict:
        """Get statistics about the database."""
        domains = {}
        intents = {}
        languages = {}
        
        for p in self.phrases:
            domains[p.domain] = domains.get(p.domain, 0) + 1
            intents[p.intent] = intents.get(p.intent, 0) + 1
            languages[p.language] = languages.get(p.language, 0) + 1
        
        total_aliases = sum(len(p.aliases) for p in self.phrases)
        
        return {
            "total_phrases": len(self.phrases),
            "total_aliases": total_aliases,
            "total_entries": len(self.phrases) + total_aliases,
            "domains": domains,
            "intents": len(intents),
            "languages": languages,
        }


class DataLoader:
    """
    Optimized data loader with format detection and caching.
    
    Supports:
    - .json: Standard JSON format
    - .msgpack: MessagePack binary format (faster)
    - .pkl: Pickle format (fastest, Python-only)
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path(__file__).parent.parent.parent.parent / "data" / ".cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def load_phrases(self, path: Path) -> PhraseDatabase:
        """Load phrase database from file with automatic format detection."""
        path = Path(path)
        
        if not path.exists():
            return PhraseDatabase()
        
        suffix = path.suffix.lower()
        
        if suffix == ".msgpack":
            return self._load_msgpack(path)
        elif suffix == ".pkl":
            return self._load_pickle(path)
        else:  # Default to JSON
            return self._load_json(path)
    
    def save_phrases(self, db: PhraseDatabase, path: Path, format: str = "json"):
        """Save phrase database to file in specified format."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == "msgpack":
            self._save_msgpack(db, path)
        elif format == "pkl" or format == "pickle":
            self._save_pickle(db, path)
        else:
            self._save_json(db, path)
    
    def _load_json(self, path: Path) -> PhraseDatabase:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return PhraseDatabase.from_dict(data)
    
    def _save_json(self, db: PhraseDatabase, path: Path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(db.to_dict(), f, indent=2, ensure_ascii=False)
    
    def _load_msgpack(self, path: Path) -> PhraseDatabase:
        if not _check_msgpack():
            # Fallback to JSON
            json_path = path.with_suffix(".json")
            if json_path.exists():
                return self._load_json(json_path)
            return PhraseDatabase()
        
        import msgpack
        with open(path, "rb") as f:
            data = msgpack.unpack(f, raw=False)
        return PhraseDatabase.from_dict(data)
    
    def _save_msgpack(self, db: PhraseDatabase, path: Path):
        if not _check_msgpack():
            # Fallback to JSON
            self._save_json(db, path.with_suffix(".json"))
            return
        
        import msgpack
        with open(path, "wb") as f:
            msgpack.pack(db.to_dict(), f, use_bin_type=True)
    
    def _load_pickle(self, path: Path) -> PhraseDatabase:
        with open(path, "rb") as f:
            return pickle.load(f)
    
    def _save_pickle(self, db: PhraseDatabase, path: Path):
        with open(path, "wb") as f:
            pickle.dump(db, f)
    
    def convert_format(self, input_path: Path, output_path: Path):
        """Convert between formats based on file extensions."""
        db = self.load_phrases(input_path)
        output_format = output_path.suffix.lower().lstrip(".")
        if output_format == "pkl":
            output_format = "pickle"
        self.save_phrases(db, output_path, format=output_format)
    
    def get_cached_path(self, original_path: Path, format: str = "pkl") -> Path:
        """Get path for cached version of a file."""
        # Create hash of original file for cache invalidation
        content_hash = hashlib.md5(original_path.read_bytes()).hexdigest()[:8]
        cache_name = f"{original_path.stem}_{content_hash}.{format}"
        return self.cache_dir / cache_name
    
    def load_with_cache(self, path: Path, cache_format: str = "pkl") -> PhraseDatabase:
        """Load with automatic caching for faster subsequent loads."""
        path = Path(path)
        cache_path = self.get_cached_path(path, cache_format)
        
        # Check if cache exists and is valid
        if cache_path.exists():
            cache_mtime = cache_path.stat().st_mtime
            orig_mtime = path.stat().st_mtime
            if cache_mtime > orig_mtime:
                try:
                    return self._load_pickle(cache_path)
                except Exception:
                    pass
        
        # Load from original and cache
        db = self.load_phrases(path)
        try:
            self._save_pickle(db, cache_path)
        except Exception:
            pass
        
        return db


def load_legacy_phrases(path: Path) -> PhraseDatabase:
    """Load phrases from legacy multilingual_phrases.json format."""
    db = PhraseDatabase()
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    db.version = data.get("version", "1.0")
    db.description = data.get("description", "")
    
    for entry in data.get("phrases", []):
        db.add(PhraseEntry(
            phrase=entry.get("phrase", ""),
            domain=entry.get("domain", "unknown"),
            intent=entry.get("intent", "unknown"),
            language=entry.get("language", "multi"),
            aliases=entry.get("aliases", []),
        ))
    
    return db


def merge_databases(*dbs: PhraseDatabase) -> PhraseDatabase:
    """Merge multiple phrase databases."""
    merged = PhraseDatabase(
        version="2.0",
        description="Merged database",
    )
    
    seen = set()
    for db in dbs:
        for phrase in db.phrases:
            key = (phrase.phrase.lower(), phrase.domain, phrase.intent)
            if key not in seen:
                merged.add(phrase)
                seen.add(key)
    
    return merged


def benchmark_formats(db: PhraseDatabase, iterations: int = 10) -> dict:
    """Benchmark different data formats."""
    import tempfile
    import os
    
    results = {}
    
    with tempfile.TemporaryDirectory() as tmpdir:
        loader = DataLoader()
        
        # JSON
        json_path = Path(tmpdir) / "test.json"
        loader.save_phrases(db, json_path, "json")
        json_size = json_path.stat().st_size
        
        start = time.time()
        for _ in range(iterations):
            loader.load_phrases(json_path)
        json_time = (time.time() - start) / iterations * 1000
        
        results["json"] = {"time_ms": json_time, "size_bytes": json_size}
        
        # Pickle
        pkl_path = Path(tmpdir) / "test.pkl"
        loader.save_phrases(db, pkl_path, "pickle")
        pkl_size = pkl_path.stat().st_size
        
        start = time.time()
        for _ in range(iterations):
            loader.load_phrases(pkl_path)
        pkl_time = (time.time() - start) / iterations * 1000
        
        results["pickle"] = {"time_ms": pkl_time, "size_bytes": pkl_size}
        
        # MessagePack (if available)
        if _check_msgpack():
            msgpack_path = Path(tmpdir) / "test.msgpack"
            loader.save_phrases(db, msgpack_path, "msgpack")
            msgpack_size = msgpack_path.stat().st_size
            
            start = time.time()
            for _ in range(iterations):
                loader.load_phrases(msgpack_path)
            msgpack_time = (time.time() - start) / iterations * 1000
            
            results["msgpack"] = {"time_ms": msgpack_time, "size_bytes": msgpack_size}
    
    return results
