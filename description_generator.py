import json
import os
import ollama
import pandas as pd
from textstat import textstat
import numpy as np

class SEOScorer:
    def __init__(self):
        self.keyword_weight = 0.3
        self.readability_weight = 0.2
        self.length_weight = 0.15
        self.structure_weight = 0.2
        self.uniqueness_weight = 0.15

    def calculate_keyword_score(self, text, keywords):
        """Calculate score based on keyword usage and density"""
        if not keywords:
            return 0.0
            
        text_words = text.lower().split()
        keyword_count = sum(1 for word in text_words if word in [k.lower() for k in keywords])
        
        # Calculate keyword density (should be between 1-3%)
        density = (keyword_count / len(text_words)) * 100 if text_words else 0
        density_score = max(0, min(1, 1 - abs(density - 2) / 2))  # Peak at 2% density
        
        # Score for keyword distribution
        positions = [i for i, word in enumerate(text_words) if word in [k.lower() for k in keywords]]
        if positions:
            distribution = np.std(positions) / len(text_words)
            distribution_score = max(0, min(1, 1 - distribution))
        else:
            distribution_score = 0
            
        return (density_score + distribution_score) / 2

    def calculate_readability_score(self, text):
        """Calculate score based on readability metrics"""
        try:
            # Flesch Reading Ease score (higher is better, 60-70 is ideal)
            flesch_score = textstat.flesch_reading_ease(text)
            flesch_normalized = max(0, min(1, flesch_score / 100))
            
            # Flesch-Kincaid Grade Level (lower is better, 7-8 is ideal)
            grade_level = textstat.flesch_kincaid_grade(text)
            grade_normalized = max(0, min(1, 1 - (grade_level - 7) / 10))
            
            return (flesch_normalized + grade_normalized) / 2
        except:
            return 0.5  # Default score if calculation fails

    def calculate_length_score(self, text):
        """Calculate score based on text length"""
        word_count = len(text.split())
        # Ideal length between 100-150 words
        if 100 <= word_count <= 150:
            return 1.0
        elif word_count < 50:
            return 0.3
        elif word_count > 200:
            return 0.7
        else:
            return 0.8

    def calculate_structure_score(self, text):
        """Calculate score based on text structure"""
        score = 0
        
        # Check for paragraphs
        paragraphs = text.split('\n\n')
        if len(paragraphs) >= 2:
            score += 0.3
            
        # Check for bullet points or lists
        if any(char in text for char in ['•', '-', '*']):
            score += 0.2
            
        # Check for headings or subheadings
        if any(line.strip().endswith(':') for line in text.split('\n')):
            score += 0.2
            
        # Check for proper punctuation
        if text.count('.') >= 3 and text.count(',') >= 2:
            score += 0.3
            
        return score

    def calculate_uniqueness_score(self, text, all_descriptions):
        """Calculate score based on text uniqueness"""
        if not all_descriptions:
            return 1.0
            
        # Calculate similarity with other descriptions
        text_words = set(text.lower().split())
        similarities = []
        
        for other_text in all_descriptions:
            if other_text == text:
                continue
            other_words = set(other_text.lower().split())
            common_words = text_words.intersection(other_words)
            similarity = len(common_words) / max(len(text_words), len(other_words))
            similarities.append(similarity)
            
        if not similarities:
            return 1.0
            
        avg_similarity = sum(similarities) / len(similarities)
        return max(0, 1 - avg_similarity)

    def score_description(self, text, keywords, all_descriptions):
        """Calculate overall SEO score"""
        scores = {
            'keyword_score': self.calculate_keyword_score(text, keywords),
            'readability_score': self.calculate_readability_score(text),
            'length_score': self.calculate_length_score(text),
            'structure_score': self.calculate_structure_score(text),
            'uniqueness_score': self.calculate_uniqueness_score(text, all_descriptions)
        }
        
        weights = {
            'keyword_score': self.keyword_weight,
            'readability_score': self.readability_weight,
            'length_score': self.length_weight,
            'structure_score': self.structure_weight,
            'uniqueness_score': self.uniqueness_weight
        }
        
        overall_score = sum(score * weights[metric] for metric, score in scores.items())
        
        return {
            'overall_score': round(overall_score * 100, 2),
            'detailed_scores': {k: round(v * 100, 2) for k, v in scores.items()}
        }

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
    # If no extracted data, use product features as keywords
    if not extracted_data:
        return []
        
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
        Keywords to include: {', '.join(keywords) if keywords else 'None provided'}
        
        Write only the description, without any additional text or explanations.
        """
        
        print(f"Generating description for: {product['Product Name']}")
        print(f"Using keywords: {keywords}")
        
        # Generate description using Ollama
        response = ollama.generate(model=model, prompt=prompt)
        description = response['response'].strip()
        
        print(f"Generated description length: {len(description.split())} words")
        return description
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
    
    # Initialize SEO scorer
    scorer = SEOScorer()
    
    # Generate descriptions
    results = []
    print("Generating descriptions...")
    
    for index, product in products_df.iterrows():
        print(f"\nProcessing product {index + 1}/{len(products_df)}: {product['Product Name']}")
            
        try:
            # Find matching keywords from extracted data
            keywords = find_matching_keywords(product['Product Name'], extracted_keywords)
            if not keywords:
                print("No matching keywords found, using product features as keywords")
                keywords = product['Product Features'].split(', ')
            
            # Generate description
            description = generate_description(product, keywords)
            if not description:
                print("Failed to generate description, skipping...")
                continue
            
            # Calculate SEO score
            all_descriptions = [d['generated_description'] for d in results]
            seo_score = scorer.score_description(description, keywords, all_descriptions)
            
            # Store results
            result = {
                'product_name': product['Product Name'],
                'features': product['Product Features'],
                'target_audience': product['Target Audience'],
                'used_keywords': keywords,
                'generated_description': description,
                'seo_score': seo_score['overall_score'],
                'detailed_seo_scores': seo_score['detailed_scores']
            }
            results.append(result)
            
            # Print SEO score for this description
            print(f"SEO Score: {seo_score['overall_score']}/100")
            print("Detailed Scores:")
            for metric, score in seo_score['detailed_scores'].items():
                print(f"  {metric}: {score}/100")
            print()
            
        except Exception as e:
            print(f"Error processing product {index + 1}: {str(e)}")
            continue
    
    # Save results
    output_file = os.path.join('ExtractedData', 'generated_descriptions.json')
    print(f"Saving results to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Print summary
    if results:
        avg_score = sum(r['seo_score'] for r in results) / len(results)
        print(f"\nSEO Scoring Summary:")
        print(f"Average Score: {avg_score:.2f}/100")
        print(f"Highest Score: {max(r['seo_score'] for r in results):.2f}/100")
        print(f"Lowest Score: {min(r['seo_score'] for r in results):.2f}/100")
    else:
        print("\nNo descriptions were generated successfully.")

if __name__ == "__main__":
    main() 