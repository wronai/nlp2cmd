# Polish Lemmatization Support

This document explains how to enable Polish lemmatization support in nlp2cmd using spaCy models.

## Overview

Lemmatization helps improve intent detection by reducing Polish words to their base form:
- `uruchomienie` → `uruchomić` 
- `uruchamianie` → `uruchamiać`
- `pokaz` → `pokazać`
- `restartowanie` → `restartować`

This allows the system to match more variations of Polish words without manually adding every inflection to the patterns.

## Installation

### Option 1: spaCy Small Polish Model (Recommended)

```bash
# Install spaCy
pip install spacy

# Download and install the small Polish model
python -m spacy download pl_core_news_sm
```

### Option 2: CLARIN Polish Model (Alternative)

```bash
# Install spaCy
pip install spacy

# Download CLARIN model (larger, more accurate)
python -m spacy download spacy_pl_model
```

## Usage

Once installed, lemmatization will be automatically enabled. The system will:

1. Load the Polish model on startup
2. Apply lemmatization before keyword matching
3. Fall back gracefully if the model is not available

## Performance Impact

- **Startup time**: +1-3 seconds (model loading)
- **Memory usage**: +20-50MB (model in memory)
- **Runtime**: Minimal impact (fast processing)
- **Accuracy**: Significant improvement for Polish variations

## Verification

To check if lemmatization is working:

```python
from nlp2cmd.generation.keywords import KeywordIntentDetector

det = KeywordIntentDetector()

# These should now work better with lemmatization
tests = [
    "uruchomienie usługi nginx",
    "restartowanie systemu", 
    "pokaz foldery",
    "usuwanie pliku"
]

for test in tests:
    result = det.detect(test)
    print(f"{test} -> {result.domain}/{result.intent}")
```

## Troubleshooting

### Model Not Found

If you see warnings about missing models:

```bash
# Check available models
python -m spacy download pl_core_news_sm

# Or verify installation
python -c "import spacy; nlp = spacy.load('pl_core_news_sm'); print('Model loaded successfully')"
```

### Performance Issues

If startup is too slow:

1. Use the smaller model: `pl_core_news_sm`
2. Disable lemmatization by uninstalling spaCy or the model
3. Consider using only rapidfuzz for typo correction

## Fallback Behavior

The system is designed to work without lemmatization:
- If spaCy is not installed → no lemmatization
- If Polish model is missing → no lemmatization  
- If lemmatization fails → continues with original text
- Existing regex-based normalization still applies

This ensures the system remains functional in all environments.
