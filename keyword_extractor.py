import json
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import KNeighborsClassifier
import numpy as np
import os

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

def preprocess_text(text):
    """
    Preprocess text by:
    1. Converting to lowercase
    2. Tokenizing
    3. Removing stopwords
    4. Lemmatizing
    """
    if not isinstance(text, str):
        return ""
        
    # Convert to lowercase
    text = text.lower()
    
    # Tokenize
    tokens = word_tokenize(text)
    
    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    tokens = [token for token in tokens if token not in stop_words]
    
    # Lemmatize
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(token) for token in tokens]
    
    # Remove any remaining empty strings or single characters
    tokens = [token for token in tokens if len(token) > 1]
    
    return ' '.join(tokens)

def extract_keywords(text, top_n=10):
    """
    Extract top keywords using TF-IDF
    Returns list of (keyword, score) tuples
    """
    if not text.strip():
        return []
        
    try:
        vectorizer = TfidfVectorizer(max_features=1000, min_df=1)
        tfidf_matrix = vectorizer.fit_transform([text])
        feature_names = vectorizer.get_feature_names_out()
        
        if len(feature_names) == 0:
            return []
            
        # Get top keywords
        tfidf_scores = tfidf_matrix.toarray()[0]
        top_indices = np.argsort(tfidf_scores)[-top_n:][::-1]
        keywords = [(feature_names[i], tfidf_scores[i]) for i in top_indices]
        
        return keywords
    except Exception as e:
        print(f"Error extracting keywords: {str(e)}")
        return []

def load_json_data(file_path):
    """
    Load and parse JSON file
    Returns the parsed data or empty list if error
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error loading {file_path}: {str(e)}")
        return []

def main():
    """
    Main function to:
    1. Load JSON files
    2. Process text
    3. Extract keywords
    4. Save results
    """
    print("Starting keyword extraction process...")
    
    # Define file paths
    mock_data_dir = 'MockData'
    extracted_data_dir = 'ExtractedData'
    
    # Ensure directories exist
    os.makedirs(mock_data_dir, exist_ok=True)
    os.makedirs(extracted_data_dir, exist_ok=True)
    
    # Load JSON files
    print("Loading JSON files...")
    products = load_json_data(os.path.join(mock_data_dir, 'product.json'))
    categories = load_json_data(os.path.join(mock_data_dir, 'categories.json'))
    
    if not products:
        print("No product data found. Exiting...")
        return
        
    print(f"Loaded {len(products)} products")
    
    # Process products
    results = []
    print("Processing products...")
    
    for i, product in enumerate(products):
        if i % 100 == 0:
            print(f"Processing product {i+1}/{len(products)}")
            
        try:
            # Combine relevant text fields
            text = f"{product.get('name', '')} {product.get('description', '')}"
            processed_text = preprocess_text(text)
            
            # Skip if text is empty after preprocessing
            if not processed_text.strip():
                print(f"Skipping product {i+1} - no valid text after preprocessing")
                continue
                
            # Extract keywords
            keywords = extract_keywords(processed_text)
            
            # Store results
            result = {
                'product_id': product.get('id', ''),
                'name': product.get('name', ''),
                'keywords': [kw[0] for kw in keywords],
                'keyword_scores': [float(kw[1]) for kw in keywords]
            }
            results.append(result)
        except Exception as e:
            print(f"Error processing product {i+1}: {str(e)}")
            continue
    
    # Save results
    output_file = os.path.join(extracted_data_dir, 'extracted_keywords.json')
    print(f"Saving results to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"Process completed successfully! Processed {len(results)} products.")

if __name__ == "__main__":
    main()