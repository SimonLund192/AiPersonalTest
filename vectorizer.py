from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import List, Dict, Union
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

class Vectorizer:
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize the vectorizer with a sentence transformer model.
        
        Args:
            model_name (str): Name of the sentence transformer model to use
        """
        self.model = SentenceTransformer(model_name)
        # Download required NLTK data
        nltk.download('punkt')
        nltk.download('stopwords')
        self.stop_words = set(stopwords.words('english'))
        
    def get_embeddings(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        Get embeddings for one or more texts.
        
        Args:
            texts: Single text string or list of text strings
            
        Returns:
            numpy.ndarray: Array of embeddings
        """
        if isinstance(texts, str):
            texts = [texts]
        return self.model.encode(texts)
        
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate cosine similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            float: Cosine similarity score between 0 and 1
        """
        embeddings = self.get_embeddings([text1, text2])
        return cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        
    def find_similar_keywords(self, keyword: str, existing_keywords: List[str], 
                            threshold: float = 0.7) -> List[str]:
        """
        Find semantically similar keywords from a list of existing keywords.
        
        Args:
            keyword: Target keyword
            existing_keywords: List of existing keywords to compare against
            threshold: Minimum similarity score to consider keywords similar
            
        Returns:
            List[str]: List of similar keywords
        """
        if not existing_keywords:
            return []
            
        # Get embeddings for all keywords
        all_keywords = [keyword] + existing_keywords
        embeddings = self.get_embeddings(all_keywords)
        
        # Calculate similarities with target keyword
        similarities = cosine_similarity([embeddings[0]], embeddings[1:])[0]
        
        # Return keywords above threshold
        similar_keywords = []
        for i, sim in enumerate(similarities):
            if sim >= threshold:
                similar_keywords.append(existing_keywords[i])
                
        return similar_keywords
        
    def calculate_semantic_density(self, text: str, keywords: List[str]) -> float:
        """
        Calculate semantic keyword density in text.
        
        Args:
            text: Input text
            keywords: List of keywords to look for
            
        Returns:
            float: Semantic density score between 0 and 1
        """
        if not keywords:
            return 0.0
            
        # Tokenize text and remove stopwords
        words = word_tokenize(text.lower())
        words = [w for w in words if w not in self.stop_words and len(w) > 1]
        
        if not words:
            return 0.0
            
        # Get embeddings for text segments and keywords
        text_segments = [' '.join(words[i:i+5]) for i in range(0, len(words), 5)]
        text_embeddings = self.get_embeddings(text_segments)
        keyword_embeddings = self.get_embeddings(keywords)
        
        # Calculate similarities between text segments and keywords
        similarities = cosine_similarity(text_embeddings, keyword_embeddings)
        
        # Calculate density score
        max_similarities = np.max(similarities, axis=1)
        density_score = np.mean(max_similarities)
        
        return float(density_score)
        
    def get_keyword_expansion(self, keywords: List[str], 
                            existing_descriptions: List[str] = None) -> Dict[str, List[str]]:
        """
        Expand keywords with semantically similar terms from existing descriptions.
        
        Args:
            keywords: List of base keywords
            existing_descriptions: Optional list of existing descriptions to mine for terms
            
        Returns:
            Dict[str, List[str]]: Dictionary mapping each keyword to its expanded terms
        """
        expanded = {}
        
        for keyword in keywords:
            # Find similar keywords from existing descriptions
            similar_terms = []
            if existing_descriptions:
                # Extract potential terms from descriptions
                all_terms = set()
                for desc in existing_descriptions:
                    words = word_tokenize(desc.lower())
                    words = [w for w in words if w not in self.stop_words and len(w) > 1]
                    all_terms.update(words)
                    
                # Find similar terms
                similar_terms = self.find_similar_keywords(keyword, list(all_terms))
                
            expanded[keyword] = similar_terms
            
        return expanded 