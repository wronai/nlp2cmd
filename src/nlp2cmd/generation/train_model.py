"""
Training script for NLP2CMD ML models.

Combines all available data sources:
1. expanded_phrases.json - Main phrase database
2. patterns.json - Intent patterns
3. command_schemas/ - Command definitions
4. Default training data

Outputs:
- ml_intent_model.pkl - TF-IDF + SVM classifier
- phrase_database.pkl - Fast-loading phrase cache
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional
from collections import Counter

from nlp2cmd.generation.ml_intent_classifier import (
    MLIntentClassifier,
    TrainingSample,
    create_default_training_data,
)
from nlp2cmd.generation.data_loader import (
    DataLoader,
    PhraseDatabase,
    PhraseEntry,
    load_legacy_phrases,
    merge_databases,
    benchmark_formats,
)


def load_expanded_phrases(path: Path) -> list[TrainingSample]:
    """Load samples from expanded_phrases.json."""
    samples = []
    
    if not path.exists():
        return samples
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    for entry in data.get("phrases", []):
        phrase = entry.get("phrase", "")
        domain = entry.get("domain", "unknown")
        intent = entry.get("intent", "unknown")
        language = entry.get("language", "multi")
        aliases = entry.get("aliases", [])
        
        # Add main phrase
        samples.append(TrainingSample(
            text=phrase,
            intent=intent,
            domain=domain,
            language=language
        ))
        
        # Add all aliases
        for alias in aliases:
            samples.append(TrainingSample(
                text=alias,
                intent=intent,
                domain=domain,
                language=language
            ))
    
    return samples


def load_patterns(path: Path) -> list[TrainingSample]:
    """Load samples from patterns.json."""
    samples = []
    
    if not path.exists():
        return samples
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    for domain, intents in data.items():
        if domain.startswith("$"):
            continue
            
        if isinstance(intents, dict):
            for intent, patterns in intents.items():
                if isinstance(patterns, list):
                    for pattern in patterns:
                        if isinstance(pattern, str) and len(pattern) > 1:
                            samples.append(TrainingSample(
                                text=pattern,
                                intent=intent,
                                domain=domain,
                                language="multi"
                            ))
    
    return samples


def load_command_schemas(schemas_dir: Path) -> list[TrainingSample]:
    """Load samples from command schema files."""
    samples = []
    
    if not schemas_dir.exists():
        return samples
    
    for schema_file in schemas_dir.glob("*.json"):
        try:
            with open(schema_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            command = data.get("command", schema_file.stem)
            category = data.get("category", "shell")
            
            # Add command name
            samples.append(TrainingSample(
                text=command,
                intent=command,
                domain=category,
                language="en"
            ))
            
            # Add patterns if available
            for pattern in data.get("patterns", []):
                if isinstance(pattern, str) and len(pattern) > 2:
                    # Extract meaningful parts from pattern
                    clean_pattern = pattern.split("[")[0].strip()
                    if clean_pattern:
                        samples.append(TrainingSample(
                            text=clean_pattern,
                            intent=command,
                            domain=category,
                            language="en"
                        ))
            
            # Add examples
            for example in data.get("examples", []):
                if isinstance(example, str) and len(example) > 2:
                    samples.append(TrainingSample(
                        text=example.split()[0] if " " in example else example,
                        intent=command,
                        domain=category,
                        language="en"
                    ))
                    
        except (json.JSONDecodeError, KeyError):
            continue
    
    return samples


def generate_augmented_samples(samples: list[TrainingSample]) -> list[TrainingSample]:
    """Generate augmented training samples with variations."""
    augmented = []
    
    # Common variations
    prefixes_en = ["please ", "can you ", "i want to ", "i need to ", ""]
    prefixes_pl = ["proszę ", "czy możesz ", "chcę ", "muszę ", ""]
    
    # Entity values for augmentation
    entities = {
        "service": ["nginx", "apache2", "mysql", "postgresql", "redis", "mongodb", "docker"],
        "file": ["config.json", "app.py", "index.js", "data.csv", "main.go", "Dockerfile"],
        "directory": ["src", "build", "dist", "tmp", "logs", "backup", "data"],
        "process": ["node", "python", "java", "nginx", "mysql", "postgres"],
        "container": ["webapp", "api", "db", "redis", "nginx", "frontend", "backend"],
        "branch": ["main", "master", "develop", "feature", "bugfix", "release"],
        "table": ["users", "orders", "products", "customers", "logs", "sessions"],
    }
    
    for sample in samples:
        # Add with prefixes (limited to avoid explosion)
        if sample.language == "en":
            for prefix in prefixes_en[:2]:  # Just first 2 prefixes
                if prefix:
                    augmented.append(TrainingSample(
                        text=f"{prefix}{sample.text}",
                        intent=sample.intent,
                        domain=sample.domain,
                        language=sample.language
                    ))
        elif sample.language == "pl":
            for prefix in prefixes_pl[:2]:
                if prefix:
                    augmented.append(TrainingSample(
                        text=f"{prefix}{sample.text}",
                        intent=sample.intent,
                        domain=sample.domain,
                        language=sample.language
                    ))
        
        # Add with entity values
        for entity_type, values in entities.items():
            for value in values[:2]:  # Just first 2 values
                augmented.append(TrainingSample(
                    text=f"{sample.text} {value}",
                    intent=sample.intent,
                    domain=sample.domain,
                    language=sample.language
                ))
    
    return augmented


def deduplicate_samples(samples: list[TrainingSample]) -> list[TrainingSample]:
    """Remove duplicate samples."""
    seen = set()
    unique = []
    
    for sample in samples:
        key = (sample.text.lower().strip(), sample.domain, sample.intent)
        if key not in seen and len(sample.text.strip()) > 0:
            seen.add(key)
            unique.append(sample)
    
    return unique


def train_all_models(
    data_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    augment: bool = True,
    verbose: bool = True
) -> dict:
    """
    Train ML models on all available data.
    
    Args:
        data_dir: Directory containing training data
        output_dir: Directory to save trained models
        augment: Whether to augment training data
        verbose: Print progress information
        
    Returns:
        Dictionary with training statistics
    """
    if data_dir is None:
        data_dir = Path(__file__).parent.parent.parent.parent / "data"
    if output_dir is None:
        output_dir = data_dir
    
    start_time = time.time()
    stats = {"sources": {}}
    
    # Collect samples from all sources
    all_samples = []
    
    # 1. Default training data
    if verbose:
        print("Loading default training data...")
    default_samples = create_default_training_data()
    all_samples.extend(default_samples)
    stats["sources"]["default"] = len(default_samples)
    
    # 2. Expanded phrases
    expanded_path = data_dir / "expanded_phrases.json"
    if expanded_path.exists():
        if verbose:
            print(f"Loading expanded phrases from {expanded_path}...")
        expanded_samples = load_expanded_phrases(expanded_path)
        all_samples.extend(expanded_samples)
        stats["sources"]["expanded_phrases"] = len(expanded_samples)
    
    # 3. Legacy multilingual phrases
    legacy_path = data_dir / "multilingual_phrases.json"
    if legacy_path.exists():
        if verbose:
            print(f"Loading legacy phrases from {legacy_path}...")
        from nlp2cmd.generation.ml_intent_classifier import generate_training_data_from_phrases
        legacy_samples = generate_training_data_from_phrases(legacy_path)
        all_samples.extend(legacy_samples)
        stats["sources"]["multilingual_phrases"] = len(legacy_samples)
    
    # 4. Patterns
    patterns_path = data_dir / "patterns.json"
    if patterns_path.exists():
        if verbose:
            print(f"Loading patterns from {patterns_path}...")
        pattern_samples = load_patterns(patterns_path)
        all_samples.extend(pattern_samples)
        stats["sources"]["patterns"] = len(pattern_samples)
    
    # 5. Command schemas
    schemas_dir = data_dir.parent / "command_schemas" / "commands"
    if schemas_dir.exists():
        if verbose:
            print(f"Loading command schemas from {schemas_dir}...")
        schema_samples = load_command_schemas(schemas_dir)
        all_samples.extend(schema_samples)
        stats["sources"]["command_schemas"] = len(schema_samples)
    
    # Deduplicate
    if verbose:
        print(f"Total raw samples: {len(all_samples)}")
    all_samples = deduplicate_samples(all_samples)
    stats["unique_samples"] = len(all_samples)
    if verbose:
        print(f"Unique samples: {len(all_samples)}")
    
    # Augment
    if augment:
        if verbose:
            print("Generating augmented samples...")
        augmented = generate_augmented_samples(all_samples)
        all_samples.extend(augmented)
        all_samples = deduplicate_samples(all_samples)
        stats["augmented_samples"] = len(all_samples)
        if verbose:
            print(f"After augmentation: {len(all_samples)}")
    
    # Statistics
    domains = Counter(s.domain for s in all_samples)
    intents = Counter(f"{s.domain}/{s.intent}" for s in all_samples)
    languages = Counter(s.language for s in all_samples)
    
    stats["domains"] = dict(domains)
    stats["total_intents"] = len(intents)
    stats["languages"] = dict(languages)
    
    if verbose:
        print(f"\nDomains: {dict(domains)}")
        print(f"Total intents: {len(intents)}")
        print(f"Languages: {dict(languages)}")
    
    # Train classifier
    if verbose:
        print("\nTraining ML classifier...")
    
    classifier = MLIntentClassifier()
    model_path = output_dir / "ml_intent_model.pkl"
    
    train_start = time.time()
    classifier.train(all_samples, save_path=model_path)
    train_time = time.time() - train_start
    
    stats["training_time_s"] = train_time
    stats["model_path"] = str(model_path)
    stats["model_size_bytes"] = model_path.stat().st_size
    
    if verbose:
        print(f"Training completed in {train_time:.2f}s")
        print(f"Model saved to {model_path} ({model_path.stat().st_size / 1024:.1f} KB)")
    
    # Create phrase database cache
    if verbose:
        print("\nCreating phrase database cache...")
    
    loader = DataLoader()
    db = PhraseDatabase(
        version="2.0",
        description="Combined phrase database",
        metadata={"trained_at": time.strftime("%Y-%m-%d %H:%M:%S")}
    )
    
    for sample in all_samples:
        db.add(PhraseEntry(
            phrase=sample.text,
            domain=sample.domain,
            intent=sample.intent,
            language=sample.language,
        ))
    
    # Save in multiple formats
    db_json_path = output_dir / "phrase_database.json"
    db_pkl_path = output_dir / "phrase_database.pkl"
    
    loader.save_phrases(db, db_json_path, "json")
    loader.save_phrases(db, db_pkl_path, "pickle")
    
    stats["phrase_db_json_size"] = db_json_path.stat().st_size
    stats["phrase_db_pkl_size"] = db_pkl_path.stat().st_size
    
    if verbose:
        print(f"JSON database: {db_json_path} ({db_json_path.stat().st_size / 1024:.1f} KB)")
        print(f"Pickle database: {db_pkl_path} ({db_pkl_path.stat().st_size / 1024:.1f} KB)")
    
    # Benchmark
    if verbose:
        print("\nBenchmarking data formats...")
        bench_results = benchmark_formats(db, iterations=5)
        print(f"  JSON: {bench_results['json']['time_ms']:.2f}ms, {bench_results['json']['size_bytes']/1024:.1f}KB")
        print(f"  Pickle: {bench_results['pickle']['time_ms']:.2f}ms, {bench_results['pickle']['size_bytes']/1024:.1f}KB")
        if "msgpack" in bench_results:
            print(f"  MessagePack: {bench_results['msgpack']['time_ms']:.2f}ms, {bench_results['msgpack']['size_bytes']/1024:.1f}KB")
        stats["benchmark"] = bench_results
    
    total_time = time.time() - start_time
    stats["total_time_s"] = total_time
    
    if verbose:
        print(f"\n✅ Training completed in {total_time:.2f}s")
        print(f"   Total samples: {len(all_samples)}")
        print(f"   Total intents: {len(intents)}")
    
    return stats


def quick_test(data_dir: Optional[Path] = None):
    """Quick test of trained model."""
    if data_dir is None:
        data_dir = Path(__file__).parent.parent.parent.parent / "data"
    
    model_path = data_dir / "ml_intent_model.pkl"
    if not model_path.exists():
        print("Model not found. Training first...")
        train_all_models(data_dir)
    
    classifier = MLIntentClassifier(model_path=model_path)
    
    test_cases = [
        "list files",
        "pokaż procesy pamięci",
        "docker compose up",
        "git status",
        "uruchom serwer nginx",
        "znajdź plik config",
        "kubectl get pods",
        "select from users",
        "npm start",
        "zatrzymaj usługę apache2",
    ]
    
    print("\n=== Quick Test ===")
    for text in test_cases:
        result = classifier.predict(text)
        if result:
            print(f"{text:30} -> {result.domain}/{result.intent} ({result.confidence:.2f})")
        else:
            print(f"{text:30} -> NO PREDICTION")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        quick_test()
    else:
        stats = train_all_models(verbose=True)
        print(f"\nStats: {json.dumps(stats, indent=2, default=str)}")
        quick_test()
