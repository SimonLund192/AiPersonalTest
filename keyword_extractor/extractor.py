import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from rake_nltk import Rake

class KeywordExtractor:
    def __init__(self, method='tfidf', top_n=10, **vectorizer_kwargs):
        self.method = method
        self.top_n = top_n
        if method == 'tfidf':
            self.vectorizer = TfidfVectorizer(**vectorizer_kwargs)
        elif method == 'rake':
            self.rake = Rake(min_length=2, max_length=4)
        else:
            raise ValueError(f"Unknown extraction method: {method}")

    def fit(self, corpus):
        if self.method == 'tfidf':
            logging.info("Fitting TF–IDF vectorizer…")
            self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
            self.features = self.vectorizer.get_feature_names_out()

    def extract(self, text, doc_index=None):
        if self.method == 'tfidf':
            if doc_index is None:
                raise ValueError("doc_index required for TF–IDF extraction")
            row = self.tfidf_matrix[doc_index].toarray()[0]
            top_idxs = row.argsort()[-self.top_n:][::-1]
            return [(self.features[i], float(row[i]))
                    for i in top_idxs if row[i] > 0]
        else:
            self.rake.extract_keywords_from_text(text)
            return self.rake.get_ranked_phrases_with_scores()[:self.top_n]