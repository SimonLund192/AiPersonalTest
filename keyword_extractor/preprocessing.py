import logging
import spacy
from spacy.cli import download as spacy_download

class TextPreprocessor:
    def __init__(self, model_name: str, custom_stops=None):
        self.nlp = self._load_spacy_model(model_name)
        self.stopwords = set(self.nlp.Defaults.stop_words)
        if custom_stops:
            self.stopwords |= set(custom_stops)

    def _load_spacy_model(self, name: str):
        try:
            return spacy.load(name, disable=['parser', 'ner'])
        except OSError:
            logging.info(f"Downloading spaCy model '{name}'…")
            spacy_download(name)
            return spacy.load(name, disable=['parser', 'ner'])

    def __call__(self, text: str) -> str:
        if not isinstance(text, str) or not text.strip():
            return ''
        doc = self.nlp(text.lower())
        tokens = [
            token.lemma_
            for token in doc
            if token.is_alpha
               and token.lemma_ not in self.stopwords
               and token.pos_ in {'NOUN', 'PROPN', 'ADJ'}
        ]
        return ' '.join(tokens)