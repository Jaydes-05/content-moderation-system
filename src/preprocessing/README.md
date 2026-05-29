# Preprocessing Module

Lightweight text preprocessing for content moderation.

## Quick Start

```python
from preprocessing import clean_text, preprocess_pipeline

# Basic usage
text = "Check this OUT: https://spam.com !!! 😡"
cleaned = clean_text(text)
# → "check this out: !!! 😡"

# Use predefined pipelines
preprocess_pipeline(text, mode='default')      # General use
preprocess_pipeline(text, mode='ml')           # Traditional ML
preprocess_pipeline(text, mode='transformer')  # BERT/RoBERTa
```

## Functions

### `clean_text(text, **kwargs)`

Core cleaning function with configurable options.

**Parameters:**
- `text` (str | None): Input text
- `lowercase` (bool): Convert to lowercase (default: True)
- `remove_urls` (bool): Remove HTTP/HTTPS/www links (default: True)
- `remove_extra_whitespace` (bool): Normalize whitespace (default: True)
- `remove_special_chars` (bool): Remove control chars (default: True)
- `preserve_punctuation` (bool): Keep punctuation (default: True)

**Returns:** Cleaned string (empty string if input is None)

**Examples:**
```python
# Remove URLs
clean_text("Visit https://example.com")
# → "visit"

# Keep uppercase
clean_text("HELLO", lowercase=False)
# → "HELLO"

# Remove punctuation
clean_text("Hello!!!", preserve_punctuation=False)
# → "hello"
```

### `preprocess_pipeline(text, mode='default')`

Predefined preprocessing configurations.

**Modes:**

| Mode | Use Case | Lowercase | Punctuation | Description |
|------|----------|-----------|-------------|-------------|
| `default` | General | ✓ | Keep | Balanced cleaning |
| `ml` | TF-IDF, Count Vectorizer | ✓ | Remove | Aggressive cleaning |
| `transformer` | BERT, RoBERTa | ✗ | Keep | Minimal (preserve context) |

**Examples:**
```python
text = "HELLO World!!!"

preprocess_pipeline(text, mode='default')
# → "hello world!!!"

preprocess_pipeline(text, mode='ml')
# → "hello world"

preprocess_pipeline(text, mode='transformer')
# → "HELLO World!!!"
```

## Design Philosophy

### Why Minimal Preprocessing?

1. **Transformers handle morphology** — No need for stemming/lemmatization
2. **Context matters** — Punctuation and case carry semantic meaning
3. **Multilingual support** — Preserve non-ASCII characters
4. **Emoji signals** — Emojis convey sentiment (😡 vs 😊)

### What Gets Removed?

✓ URLs (noise, privacy)  
✓ Control characters (tabs, null bytes)  
✓ Extra whitespace (normalization)  
✗ Stopwords (context-dependent)  
✗ Emojis (sentiment signals)  
✗ Non-ASCII (multilingual support)

## Usage Patterns

### For Traditional ML Models

```python
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

df['text_clean'] = df['text'].apply(lambda x: preprocess_pipeline(x, mode='ml'))

vectorizer = TfidfVectorizer(max_features=10000)
X = vectorizer.fit_transform(df['text_clean'])
```

### For Transformer Models

```python
from transformers import BertTokenizer

df['text_clean'] = df['text'].apply(lambda x: preprocess_pipeline(x, mode='transformer'))

tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
tokens = tokenizer(df['text_clean'].tolist(), padding=True, truncation=True)
```

### Batch Processing

```python
# Apply to entire DataFrame column
df['comment_cleaned'] = df['comment_text'].apply(
    lambda x: preprocess_pipeline(x, mode='default')
)

# Handle nulls safely (clean_text returns empty string)
df['comment_cleaned'] = df['comment_text'].apply(clean_text)
```

## Testing

Run unit tests:
```bash
# With pytest
pytest tests/test_preprocess.py -v

# Without pytest
python tests/test_preprocess.py
```

Run built-in demo:
```bash
python src/preprocessing/preprocess.py
```

## Performance Notes

- **Speed:** Regex-based, ~10k comments/sec on typical hardware
- **Memory:** Processes one text at a time (no batch overhead)
- **Thread-safe:** Pure functions, no global state

## Edge Cases Handled

✓ `None` input → returns `""`  
✓ Empty string → returns `""`  
✓ Whitespace-only → returns `""`  
✓ URL-only text → returns `""`  
✓ Very long text → no truncation (handle in tokenizer)  
✓ Unicode emojis → preserved  
✓ Control characters → removed  

## Future Enhancements

Potential additions (not yet implemented):
- Language detection
- Profanity masking (for privacy)
- HTML entity decoding
- Spell correction (optional)
- Custom stopword removal

For now, keep it simple and let the models learn from clean but rich text.
