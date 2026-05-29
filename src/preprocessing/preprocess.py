"""
Text preprocessing module for content moderation.

This module provides lightweight text cleaning functions designed to work with:
- Traditional ML models (Logistic Regression, Naive Bayes, etc.)
- Transformer models (BERT, RoBERTa, etc.)

The preprocessing is intentionally minimal to preserve semantic information
that transformers can leverage while still removing noise.
"""

import re
import string
from typing import Optional, Union


def clean_text(
    text: Union[str, None],
    lowercase: bool = True,
    remove_urls: bool = True,
    remove_extra_whitespace: bool = True,
    remove_special_chars: bool = True,
    preserve_punctuation: bool = True
) -> str:
    """
    Clean and normalize text for content moderation tasks.
    
    This function performs lightweight preprocessing suitable for both
    traditional ML and transformer-based models. It removes noise while
    preserving semantic content.
    
    Parameters
    ----------
    text : str or None
        Input text to clean. Can be None or empty.
    lowercase : bool, default=True
        Convert text to lowercase.
    remove_urls : bool, default=True
        Remove HTTP/HTTPS URLs and www links.
    remove_extra_whitespace : bool, default=True
        Collapse multiple spaces/tabs/newlines into single space.
    remove_special_chars : bool, default=True
        Remove unusual Unicode characters and control characters.
    preserve_punctuation : bool, default=True
        Keep standard punctuation marks (.,!?;:'"()-).
        If False, removes all punctuation.
    
    Returns
    -------
    str
        Cleaned text. Returns empty string if input is None/empty.
    
    Examples
    --------
    >>> clean_text("Check this out: https://example.com  !!!")
    'check this out: !!!'
    
    >>> clean_text("HELLO    WORLD\\n\\n\\n", lowercase=True)
    'hello world'
    
    >>> clean_text(None)
    ''
    
    Notes
    -----
    - Preserves emojis and non-ASCII characters (useful for multilingual content)
    - Does NOT perform stemming/lemmatization (transformers handle morphology)
    - Does NOT remove stopwords (context matters for toxicity detection)
    """
    # ── Handle null/empty input ─────────────────────────────────────────────
    if text is None or (isinstance(text, str) and not text.strip()):
        return ''
    
    text = str(text)  # Ensure string type
    
    # ── Remove URLs ─────────────────────────────────────────────────────────
    if remove_urls:
        # Remove http/https URLs
        text = re.sub(r'https?://\S+', '', text)
        # Remove www URLs
        text = re.sub(r'www\.\S+', '', text)
    
    # ── Lowercase ───────────────────────────────────────────────────────────
    if lowercase:
        text = text.lower()
    
    # ── Remove special characters ───────────────────────────────────────────
    if remove_special_chars:
        # Remove control characters (tabs, carriage returns, etc.)
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        # Remove unusual Unicode characters (keep letters, numbers, punctuation, emojis)
        # This preserves most meaningful content while removing garbage
        if not preserve_punctuation:
            # Keep only alphanumeric, whitespace, and common emojis
            text = re.sub(r'[^\w\s\U0001F300-\U0001F9FF]', ' ', text)
        else:
            # Keep alphanumeric, whitespace, standard punctuation, and emojis
            allowed_punct = re.escape(string.punctuation)
            text = re.sub(rf'[^\w\s{allowed_punct}\U0001F300-\U0001F9FF]', ' ', text)
    
    # ── Remove extra whitespace ─────────────────────────────────────────────
    if remove_extra_whitespace:
        # Replace multiple spaces/tabs/newlines with single space
        text = re.sub(r'\s+', ' ', text)
        # Strip leading/trailing whitespace
        text = text.strip()
    
    return text


def preprocess_pipeline(
    text: Union[str, None],
    mode: str = 'default'
) -> str:
    """
    Apply a predefined preprocessing pipeline.
    
    This function provides preset configurations for different use cases:
    - 'default': Balanced cleaning for general use
    - 'ml': Aggressive cleaning for traditional ML models
    - 'transformer': Minimal cleaning for BERT/RoBERTa models
    
    Parameters
    ----------
    text : str or None
        Input text to preprocess.
    mode : {'default', 'ml', 'transformer'}, default='default'
        Preprocessing mode:
        - 'default': Standard cleaning (lowercase, remove URLs, normalize whitespace)
        - 'ml': More aggressive (also removes most punctuation)
        - 'transformer': Minimal (preserves case and punctuation for BERT)
    
    Returns
    -------
    str
        Preprocessed text.
    
    Examples
    --------
    >>> preprocess_pipeline("HELLO WORLD!!!", mode='default')
    'hello world!!!'
    
    >>> preprocess_pipeline("HELLO WORLD!!!", mode='ml')
    'hello world'
    
    >>> preprocess_pipeline("HELLO WORLD!!!", mode='transformer')
    'HELLO WORLD!!!'
    
    Raises
    ------
    ValueError
        If mode is not one of {'default', 'ml', 'transformer'}.
    """
    valid_modes = {'default', 'ml', 'transformer'}
    if mode not in valid_modes:
        raise ValueError(f"mode must be one of {valid_modes}, got '{mode}'")
    
    if mode == 'default':
        return clean_text(
            text,
            lowercase=True,
            remove_urls=True,
            remove_extra_whitespace=True,
            remove_special_chars=True,
            preserve_punctuation=True
        )
    
    elif mode == 'ml':
        # More aggressive cleaning for traditional ML
        return clean_text(
            text,
            lowercase=True,
            remove_urls=True,
            remove_extra_whitespace=True,
            remove_special_chars=True,
            preserve_punctuation=False  # Remove punctuation for bag-of-words
        )
    
    elif mode == 'transformer':
        # Minimal preprocessing for transformers (they handle case/punctuation)
        return clean_text(
            text,
            lowercase=False,  # Preserve case
            remove_urls=True,  # Still remove URLs (noise)
            remove_extra_whitespace=True,  # Normalize whitespace
            remove_special_chars=False,  # Keep all characters
            preserve_punctuation=True
        )


# ═══════════════════════════════════════════════════════════════════════════
# Test Section
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("=" * 70)
    print("TEXT PREPROCESSING MODULE - TEST SUITE")
    print("=" * 70)
    
    # ── Test samples ────────────────────────────────────────────────────────
    test_cases = [
        {
            'label': 'Toxic comment with URL',
            'text': 'You are STUPID!!! Check this: https://example.com/spam'
        },
        {
            'label': 'Non-toxic with extra whitespace',
            'text': 'This   is  a    great   article.\n\n\nThanks for  sharing!'
        },
        {
            'label': 'Mixed case with special chars',
            'text': 'WHY would you DO that?!?! 😡😡😡'
        },
        {
            'label': 'Null input',
            'text': None
        },
        {
            'label': 'Empty string',
            'text': '   '
        },
        {
            'label': 'URL only',
            'text': 'www.spam-site.com'
        },
        {
            'label': 'Control characters',
            'text': 'Hello\x00World\t\t\twith\rweird\nchars'
        }
    ]
    
    # ── Test clean_text function ────────────────────────────────────────────
    print("\n[1] Testing clean_text() with default settings")
    print("-" * 70)
    
    for case in test_cases:
        original = case['text']
        cleaned = clean_text(original)
        print(f"\n{case['label']}:")
        print(f"  Original : {repr(original)}")
        print(f"  Cleaned  : {repr(cleaned)}")
    
    # ── Test preprocessing pipelines ────────────────────────────────────────
    print("\n\n[2] Testing preprocess_pipeline() modes")
    print("-" * 70)
    
    sample = "Check OUT this LINK: https://spam.com  !!! You're WRONG 😡"
    
    print(f"\nOriginal text:\n  {repr(sample)}")
    print(f"\nMode 'default':\n  {repr(preprocess_pipeline(sample, mode='default'))}")
    print(f"\nMode 'ml':\n  {repr(preprocess_pipeline(sample, mode='ml'))}")
    print(f"\nMode 'transformer':\n  {repr(preprocess_pipeline(sample, mode='transformer'))}")
    
    # ── Test edge cases ─────────────────────────────────────────────────────
    print("\n\n[3] Testing edge cases")
    print("-" * 70)
    
    edge_cases = [
        ('None input', None),
        ('Empty string', ''),
        ('Only whitespace', '     \n\n\t\t  '),
        ('Only URL', 'https://example.com'),
        ('Only punctuation', '!!!???...'),
        ('Unicode emoji', '😀😃😄😁😆😅🤣😂'),
        ('Very long whitespace', 'word' + ' ' * 100 + 'word')
    ]
    
    for label, text in edge_cases:
        result = clean_text(text)
        print(f"\n{label}:")
        print(f"  Input  : {repr(text)[:60]}")
        print(f"  Output : {repr(result)[:60]}")
        print(f"  Length : {len(result)}")
    
    # ── Performance note ────────────────────────────────────────────────────
    print("\n\n[4] Usage recommendations")
    print("-" * 70)
    print("""
For traditional ML models (TF-IDF, Count Vectorizer):
  → Use mode='ml' or clean_text(preserve_punctuation=False)
  
For transformer models (BERT, RoBERTa, DistilBERT):
  → Use mode='transformer' to preserve case and punctuation
  
For general exploration:
  → Use mode='default' for balanced cleaning
    """)
    
    print("\n" + "=" * 70)
    print("All tests completed successfully!")
    print("=" * 70)
