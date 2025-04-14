import json
import os
import ollama
import pandas as pd
from sklearn.neighbors import KNeighborsClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

def load_extracted_keywords():
    """Load the extracted keywords data"""
    try:
        with open(os.path.join('ExtractedData', 'extracted_keywords.json'), 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading extracted keywords: {str(e)}")
        return []

def load_products():
    """Load the products from CSV"""
    try:
        csv_path = os.path.join(os.getcwd(), 'products.csv')
        print(f"Loading products from: {csv_path}")
        if not os.path.exists(csv_path):
            print(f"Error: CSV file not found at {csv_path}")
            return None
            
        df = pd.read_csv(csv_path)
        if df.empty:
            print("Error: CSV file is empty")
            return None
            
        print(f"Successfully loaded {len(df)} products")
        return df
    except Exception as e:
        print(f"Error loading products: {str(e)}")
        return None

def find_matching_keywords(product_name, extracted_data):
    """Find matching keywords from extracted data"""
    for item in extracted_data:
        if item['name'].lower() == product_name.lower():
            return item['keywords'][:5]  # Return top 5 keywords
    return []

def generate_description(product, keywords, model="llama3"):
    """Generate SEO-friendly description using LLM"""
    try:
        # Prepare the prompt
        prompt = f"""
        Generate a unique, SEO-friendly product description for the following product.
        The description should be engaging, informative, and include the provided keywords naturally.
        Make it sound professional and appealing to potential customers.
        Keep the description between 100-150 words.
        
        Product Name: {product['Product Name']}
        Product Features: {product['Product Features']}
        Target Audience: {product['Target Audience']}
        Keywords to include: {', '.join(keywords)}
        
        Write only the description, without any additional text or explanations.
        """
        
        # Generate description using Ollama
        response = ollama.generate(model=model, prompt=prompt)
        return response['response'].strip()
    except Exception as e:
        print(f"Error generating description: {str(e)}")
        return ""

def main():
    print("Starting description generation process...")
    
    # Load data
    print("Loading data...")
    products_df = load_products()
    extracted_keywords = load_extracted_keywords()
    
    if products_df is None or products_df.empty:
        print("No products found. Exiting...")
        return
        
    print(f"Loaded {len(products_df)} products")
    
    # Generate descriptions
    results = []
    print("Generating descriptions...")
    
    for index, product in products_df.iterrows():
        print(f"Processing product {index + 1}/{len(products_df)}: {product['Product Name']}")
            
        try:
            # Find matching keywords from extracted data
            keywords = find_matching_keywords(product['Product Name'], extracted_keywords)
            
            # Generate description
            description = generate_description(product, keywords)
            
            # Store results
            result = {
                'product_name': product['Product Name'],
                'features': product['Product Features'],
                'target_audience': product['Target Audience'],
                'used_keywords': keywords,
                'generated_description': description
            }
            results.append(result)
        except Exception as e:
            print(f"Error processing product {index + 1}: {str(e)}")
            continue
    
    # Save results
    output_file = os.path.join('ExtractedData', 'generated_descriptions.json')
    print(f"Saving results to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"Process completed successfully! Generated descriptions for {len(results)} products.")

if __name__ == "__main__":
    main() 