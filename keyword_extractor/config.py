from pathlib import Path

# Directories
MOCK_DATA_DIR      = Path('MockData')
EXTRACTED_DIR      = Path('ExtractedData')
PRODUCT_FILE       = MOCK_DATA_DIR / 'product.json'
CATEGORIES_FILE    = MOCK_DATA_DIR / 'categories.json'

# TF-IDF hyperparameters
TFIDF_PARAMS = {
    'max_df': 0.8,
    'min_df': 2,
    'max_features': 2000,
    'ngram_range': (1, 2),
}

# Number of keywords per document/category
TOP_N = 10

# spaCy model name
SPACY_MODEL = 'en_core_web_sm'

# Custom stopwords (domain-specific)
CUSTOM_STOPWORDS = {'item', 'sku', 'brandx'}

# Default extraction method: 'tfidf' or 'rake'
DEFAULT_METHOD = 'tfidf'