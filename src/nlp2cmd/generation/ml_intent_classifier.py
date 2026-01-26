"""
ML-based Intent Classification using TF-IDF + SVM.

Fast, lightweight intent classifier with <1ms inference time.
Supports Polish and English commands with lemmatization.
"""

from __future__ import annotations

import json
import pickle
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

# Lazy imports for optional ML dependencies
_sklearn_available = None
_spacy_available = None


def _check_sklearn():
    global _sklearn_available
    if _sklearn_available is None:
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.svm import LinearSVC
            from sklearn.pipeline import Pipeline
            _sklearn_available = True
        except ImportError:
            _sklearn_available = False
    return _sklearn_available


def _check_spacy():
    global _spacy_available
    if _spacy_available is None:
        try:
            import spacy
            _spacy_available = True
        except ImportError:
            _spacy_available = False
    return _spacy_available


@dataclass
class IntentPrediction:
    """Result of intent classification."""
    intent: str
    domain: str
    confidence: float
    alternatives: list[tuple[str, str, float]] = field(default_factory=list)
    method: str = "ml_svm"


@dataclass 
class TrainingSample:
    """Single training sample."""
    text: str
    intent: str
    domain: str
    language: str = "multi"


class MLIntentClassifier:
    """
    Fast ML-based intent classifier using TF-IDF + SVM.
    
    Features:
    - Sub-millisecond inference
    - Polish/English support with lemmatization
    - Trainable on custom datasets
    - Model persistence for fast loading
    
    Example:
        classifier = MLIntentClassifier()
        classifier.train(training_data)
        result = classifier.predict("uruchom serwer nginx")
        # result.intent = "service_start", result.confidence = 0.95
    """
    
    def __init__(self, model_path: Optional[Path] = None):
        self.model_path = model_path
        self.pipeline = None
        self.label_to_intent = {}
        self.intent_to_domain = {}
        self.nlp = None
        self._is_trained = False
        
        if model_path and model_path.exists():
            self.load(model_path)
    
    def _get_nlp(self):
        """Lazy load spaCy model for lemmatization."""
        if self.nlp is None and _check_spacy():
            import spacy
            try:
                self.nlp = spacy.load("pl_core_news_sm")
            except OSError:
                try:
                    self.nlp = spacy.load("en_core_web_sm")
                except OSError:
                    self.nlp = None
        return self.nlp
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text: lowercase, remove diacritics, lemmatize."""
        text = text.lower().strip()
        
        # Remove diacritics for better matching
        text_normalized = unicodedata.normalize('NFKD', text)
        text_ascii = ''.join(c for c in text_normalized if not unicodedata.combining(c))
        
        # Lemmatize if spaCy available
        nlp = self._get_nlp()
        if nlp:
            doc = nlp(text_ascii)
            text_ascii = ' '.join(token.lemma_ for token in doc if not token.is_punct)
        
        return text_ascii
    
    def _extract_features(self, text: str) -> str:
        """Extract features from text for classification."""
        normalized = self._normalize_text(text)
        
        # Add n-grams by keeping original + normalized
        features = f"{text.lower()} {normalized}"
        
        # Add character n-grams for typo tolerance
        words = normalized.split()
        for word in words:
            if len(word) > 3:
                # Add character trigrams
                for i in range(len(word) - 2):
                    features += f" _{word[i:i+3]}_"
        
        return features
    
    def train(self, samples: list[TrainingSample], save_path: Optional[Path] = None):
        """
        Train the classifier on labeled samples.
        
        Args:
            samples: List of TrainingSample with text, intent, domain
            save_path: Optional path to save trained model
        """
        if not _check_sklearn():
            raise ImportError("scikit-learn required for ML classifier: pip install scikit-learn")
        
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.svm import LinearSVC
        from sklearn.pipeline import Pipeline
        from sklearn.calibration import CalibratedClassifierCV
        
        # Prepare data
        texts = [self._extract_features(s.text) for s in samples]
        labels = [f"{s.domain}/{s.intent}" for s in samples]
        
        # Build label mappings
        unique_labels = sorted(set(labels))
        self.label_to_intent = {i: label for i, label in enumerate(unique_labels)}
        
        for sample in samples:
            key = f"{sample.domain}/{sample.intent}"
            self.intent_to_domain[key] = sample.domain
        
        # Count samples per class for CV fold calculation
        from collections import Counter
        label_counts = Counter(labels)
        min_samples = min(label_counts.values())
        
        # Use calibrated SVM only if we have enough samples, otherwise plain SVM
        if min_samples >= 2:
            cv_folds = min(3, min_samples)
            classifier = CalibratedClassifierCV(
                LinearSVC(C=1.0, max_iter=10000, class_weight='balanced'),
                cv=cv_folds
            )
        else:
            # Fall back to plain LinearSVC without calibration
            classifier = LinearSVC(C=1.0, max_iter=10000, class_weight='balanced')
        
        # Create pipeline with TF-IDF + SVM
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(
                ngram_range=(1, 3),
                max_features=10000,
                sublinear_tf=True,
                min_df=1,
                analyzer='char_wb',  # Character n-grams for typo tolerance
            )),
            ('clf', classifier)
        ])
        
        # Train
        self.pipeline.fit(texts, labels)
        self._is_trained = True
        
        if save_path:
            self.save(save_path)
        
        return self
    
    def predict(self, text: str, top_k: int = 3) -> Optional[IntentPrediction]:
        """
        Predict intent for given text.
        
        Args:
            text: Input query text
            top_k: Number of alternative predictions to return
            
        Returns:
            IntentPrediction with intent, domain, confidence, alternatives
        """
        if not self._is_trained or self.pipeline is None:
            return None
        
        features = self._extract_features(text)
        
        # Check if we have predict_proba (calibrated) or just predict
        if hasattr(self.pipeline, 'predict_proba'):
            # Get probabilities
            probs = self.pipeline.predict_proba([features])[0]
            classes = self.pipeline.classes_
            
            # Sort by probability
            sorted_idx = probs.argsort()[::-1]
            
            # Top prediction
            top_idx = sorted_idx[0]
            top_label = classes[top_idx]
            top_prob = probs[top_idx]
            
            # Alternatives
            alternatives = []
            for idx in sorted_idx[1:top_k]:
                label = classes[idx]
                prob = probs[idx]
                d, i = label.split('/', 1) if '/' in label else ('unknown', label)
                alternatives.append((d, i, float(prob)))
        else:
            # Plain prediction without probabilities
            top_label = self.pipeline.predict([features])[0]
            # Use decision function for confidence estimation
            try:
                decision = self.pipeline.decision_function([features])[0]
                if hasattr(decision, '__len__'):
                    top_prob = min(1.0, max(0.5, 0.5 + 0.1 * max(decision)))
                else:
                    top_prob = min(1.0, max(0.5, 0.5 + 0.1 * decision))
            except Exception:
                top_prob = 0.8  # Default confidence
            alternatives = []
        
        domain, intent = top_label.split('/', 1) if '/' in top_label else ('unknown', top_label)
        
        return IntentPrediction(
            intent=intent,
            domain=domain,
            confidence=float(top_prob),
            alternatives=alternatives,
            method="ml_tfidf_svm"
        )
    
    def save(self, path: Path):
        """Save trained model to disk."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'wb') as f:
            pickle.dump({
                'pipeline': self.pipeline,
                'label_to_intent': self.label_to_intent,
                'intent_to_domain': self.intent_to_domain,
            }, f)
    
    def load(self, path: Path) -> bool:
        """Load trained model from disk."""
        path = Path(path)
        if not path.exists():
            return False
        
        try:
            with open(path, 'rb') as f:
                data = pickle.load(f)
            
            self.pipeline = data['pipeline']
            self.label_to_intent = data['label_to_intent']
            self.intent_to_domain = data['intent_to_domain']
            self._is_trained = True
            return True
        except Exception:
            return False
    
    @property
    def is_trained(self) -> bool:
        return self._is_trained


def generate_training_data_from_phrases(phrases_path: Path) -> list[TrainingSample]:
    """
    Generate training data from multilingual_phrases.json.
    
    Expands each phrase and its aliases into training samples.
    """
    samples = []
    
    with open(phrases_path) as f:
        data = json.load(f)
    
    for phrase_entry in data.get('phrases', []):
        phrase = phrase_entry.get('phrase', '')
        domain = phrase_entry.get('domain', 'unknown')
        intent = phrase_entry.get('intent', 'unknown')
        language = phrase_entry.get('language', 'multi')
        aliases = phrase_entry.get('aliases', [])
        
        # Add main phrase
        samples.append(TrainingSample(
            text=phrase,
            intent=intent,
            domain=domain,
            language=language
        ))
        
        # Add aliases
        for alias in aliases:
            samples.append(TrainingSample(
                text=alias,
                intent=intent,
                domain=domain,
                language=language
            ))
        
        # Generate variations with common entities
        variations = _generate_variations(phrase, domain, intent, language)
        samples.extend(variations)
    
    return samples


def _generate_variations(phrase: str, domain: str, intent: str, language: str) -> list[TrainingSample]:
    """Generate variations of a phrase with entity placeholders filled."""
    variations = []
    
    # Common entity values for shell domain
    shell_entities = {
        'service': ['nginx', 'apache2', 'mysql', 'postgresql', 'redis', 'docker', 'ssh', 'cron'],
        'application': ['app', 'server', 'webapp', 'api', 'backend', 'frontend'],
        'file': ['config.json', 'app.py', 'index.js', 'data.csv', 'log.txt'],
        'directory': ['src', 'build', 'dist', 'tmp', 'logs', 'backup'],
        'process': ['node', 'python', 'java', 'nginx', 'mysql'],
        'container': ['webapp', 'db', 'redis', 'nginx', 'api'],
        'image': ['ubuntu', 'alpine', 'node', 'python', 'nginx'],
    }
    
    # SQL entities
    sql_entities = {
        'table': ['users', 'orders', 'products', 'customers', 'logs'],
        'column': ['id', 'name', 'email', 'created_at', 'status'],
    }
    
    entities = shell_entities if domain in ['shell', 'docker'] else sql_entities
    
    # Generate variations by appending entity values
    for entity_type, values in entities.items():
        for value in values[:3]:  # Limit to 3 values per entity
            variation = f"{phrase} {value}"
            variations.append(TrainingSample(
                text=variation,
                intent=intent,
                domain=domain,
                language=language
            ))
    
    return variations


def create_default_training_data() -> list[TrainingSample]:
    """Create default training dataset for shell commands."""
    samples = []
    
    # Shell commands - English
    shell_en = [
        # File operations
        ("list files", "shell", "list"),
        ("show files", "shell", "list"),
        ("ls", "shell", "list"),
        ("dir", "shell", "list"),
        ("list directory", "shell", "list"),
        ("copy file", "shell", "copy"),
        ("cp", "shell", "copy"),
        ("duplicate file", "shell", "copy"),
        ("move file", "shell", "move"),
        ("mv", "shell", "move"),
        ("rename file", "shell", "move"),
        ("delete file", "shell", "delete"),
        ("rm", "shell", "delete"),
        ("remove file", "shell", "delete"),
        ("create directory", "shell", "mkdir"),
        ("mkdir", "shell", "mkdir"),
        ("make folder", "shell", "mkdir"),
        ("find file", "shell", "find"),
        ("search file", "shell", "find"),
        ("locate file", "shell", "find"),
        
        # Process management
        ("show processes", "shell", "list_processes"),
        ("ps aux", "shell", "list_processes"),
        ("list processes", "shell", "list_processes"),
        ("kill process", "shell", "process_kill"),
        ("terminate process", "shell", "process_kill"),
        ("stop process", "shell", "process_kill"),
        ("monitor processes", "shell", "process_monitor"),
        ("top", "shell", "process_monitor"),
        ("htop", "shell", "process_monitor"),
        
        # Service management
        ("start service", "shell", "service_start"),
        ("systemctl start", "shell", "service_start"),
        ("stop service", "shell", "service_stop"),
        ("systemctl stop", "shell", "service_stop"),
        ("restart service", "shell", "service_restart"),
        ("systemctl restart", "shell", "service_restart"),
        
        # System operations
        ("shutdown system", "shell", "system_shutdown"),
        ("reboot system", "shell", "system_reboot"),
        ("restart system", "shell", "system_restart"),
        ("system update", "shell", "system_update"),
        ("check disk space", "shell", "disk_usage"),
        ("disk usage", "shell", "disk_usage"),
        ("memory usage", "shell", "memory_usage"),
        ("free memory", "shell", "memory_usage"),
        
        # Network
        ("ping", "shell", "network_ping"),
        ("check connection", "shell", "network_ping"),
        ("show ip", "shell", "network_ip"),
        ("network status", "shell", "network_connections"),
        
        # Application launch
        ("run application", "shell", "run_application"),
        ("start app", "shell", "run_application"),
        ("launch application", "shell", "run_application"),
        ("npm start", "shell", "npm_start"),
        ("run npm", "shell", "npm_start"),
        ("python script", "shell", "run_python"),
        ("run python", "shell", "run_python"),
    ]
    
    # Shell commands - Polish
    shell_pl = [
        # File operations
        ("lista plików", "shell", "list"),
        ("pokaż pliki", "shell", "list"),
        ("wyświetl pliki", "shell", "list"),
        ("kopiuj plik", "shell", "copy"),
        ("skopiuj plik", "shell", "copy"),
        ("przenieś plik", "shell", "move"),
        ("zmień nazwę", "shell", "move"),
        ("usuń plik", "shell", "delete"),
        ("skasuj plik", "shell", "delete"),
        ("utwórz katalog", "shell", "mkdir"),
        ("stwórz folder", "shell", "mkdir"),
        ("znajdź plik", "shell", "find"),
        ("szukaj pliku", "shell", "find"),
        
        # Process management
        ("pokaż procesy", "shell", "list_processes"),
        ("lista procesów", "shell", "list_processes"),
        ("zabij proces", "shell", "process_kill"),
        ("zatrzymaj proces", "shell", "process_kill"),
        ("monitoruj procesy", "shell", "process_monitor"),
        ("pokaż procesy pamięci", "shell", "process_memory"),
        
        # Service management
        ("uruchom usługę", "shell", "service_start"),
        ("start serwis", "shell", "service_start"),
        ("zatrzymaj usługę", "shell", "service_stop"),
        ("stop serwis", "shell", "service_stop"),
        ("zrestartuj usługę", "shell", "service_restart"),
        ("restart serwis", "shell", "service_restart"),
        
        # System operations
        ("wyłącz system", "shell", "system_shutdown"),
        ("zrestartuj system", "shell", "system_reboot"),
        ("restart systemu", "shell", "system_restart"),
        ("aktualizuj system", "shell", "system_update"),
        ("sprawdź dysk", "shell", "disk_usage"),
        ("użycie dysku", "shell", "disk_usage"),
        ("użycie pamięci", "shell", "memory_usage"),
        ("wolna pamięć", "shell", "memory_usage"),
        
        # Application launch
        ("uruchom aplikację", "shell", "run_application"),
        ("urucham aplikację", "shell", "run_application"),
        ("start aplikacji", "shell", "run_application"),
        ("uruchom serwer", "shell", "start_server"),
        ("start serwera", "shell", "start_server"),
        ("uruchom npm", "shell", "npm_start"),
        ("uruchom skrypt python", "shell", "run_python"),
    ]
    
    # Docker commands
    docker = [
        ("docker run", "docker", "docker_run"),
        ("run container", "docker", "docker_run"),
        ("start container", "docker", "docker_run"),
        ("uruchom kontener", "docker", "docker_run"),
        ("docker stop", "docker", "docker_stop"),
        ("stop container", "docker", "docker_stop"),
        ("zatrzymaj kontener", "docker", "docker_stop"),
        ("docker build", "docker", "docker_build"),
        ("build image", "docker", "docker_build"),
        ("zbuduj obraz", "docker", "docker_build"),
        ("docker compose up", "docker", "docker_compose_up"),
        ("compose up", "docker", "docker_compose_up"),
        ("docker compose down", "docker", "docker_compose_down"),
        ("compose down", "docker", "docker_compose_down"),
        ("docker ps", "docker", "list"),
        ("list containers", "docker", "list"),
        ("pokaż kontenery", "docker", "list"),
        ("docker images", "docker", "images"),
        ("list images", "docker", "images"),
        ("pokaż obrazy", "docker", "images"),
        ("docker logs", "docker", "logs"),
        ("container logs", "docker", "logs"),
        ("logi kontenera", "docker", "logs"),
    ]
    
    # SQL commands
    sql = [
        ("select from", "sql", "select"),
        ("wybierz z tabeli", "sql", "select"),
        ("pokaż dane", "sql", "select"),
        ("insert into", "sql", "insert"),
        ("wstaw do tabeli", "sql", "insert"),
        ("dodaj rekord", "sql", "insert"),
        ("update table", "sql", "update"),
        ("zaktualizuj tabelę", "sql", "update"),
        ("zmień dane", "sql", "update"),
        ("delete from", "sql", "delete"),
        ("usuń z tabeli", "sql", "delete"),
        ("skasuj rekord", "sql", "delete"),
        ("create table", "sql", "create_table"),
        ("utwórz tabelę", "sql", "create_table"),
        ("drop table", "sql", "drop_table"),
        ("usuń tabelę", "sql", "drop_table"),
        ("count records", "sql", "count"),
        ("policz rekordy", "sql", "count"),
        ("join tables", "sql", "join"),
        ("połącz tabele", "sql", "join"),
    ]
    
    # Build samples
    for text, domain, intent in shell_en + shell_pl:
        samples.append(TrainingSample(text=text, intent=intent, domain=domain, language="en" if text.isascii() else "pl"))
    
    for text, domain, intent in docker:
        samples.append(TrainingSample(text=text, intent=intent, domain=domain, language="multi"))
    
    for text, domain, intent in sql:
        samples.append(TrainingSample(text=text, intent=intent, domain=domain, language="multi"))
    
    return samples


# Singleton instance
_classifier_instance: Optional[MLIntentClassifier] = None


def get_ml_classifier(force_retrain: bool = False) -> Optional[MLIntentClassifier]:
    """
    Get or create ML intent classifier singleton.
    
    Trains on first call if no saved model exists.
    """
    global _classifier_instance
    
    if not _check_sklearn():
        return None
    
    if _classifier_instance is not None and _classifier_instance.is_trained and not force_retrain:
        return _classifier_instance
    
    _classifier_instance = MLIntentClassifier()
    
    # Try to load saved model
    model_path = Path(__file__).parent.parent.parent.parent / "data" / "ml_intent_model.pkl"
    if model_path.exists() and not force_retrain:
        if _classifier_instance.load(model_path):
            return _classifier_instance
    
    # Train on default + phrases data
    training_data = create_default_training_data()
    
    # Also load from multilingual_phrases.json if available
    phrases_path = Path(__file__).parent.parent.parent.parent / "data" / "multilingual_phrases.json"
    if phrases_path.exists():
        try:
            phrase_samples = generate_training_data_from_phrases(phrases_path)
            training_data.extend(phrase_samples)
        except Exception:
            pass
    
    # Train classifier
    try:
        _classifier_instance.train(training_data, save_path=model_path)
    except Exception as e:
        # If training fails, return None
        return None
    
    return _classifier_instance
