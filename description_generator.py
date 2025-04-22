import json
import os
import openai
from dotenv import load_dotenv
import pandas as pd
from textstat import textstat
import numpy as np
from seo_scorer import SEOScorer

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def call_gpt4o(prompt: str, model: str = "gpt-4o-mini", temperature: float = 0.7, max_tokens: int = 300) -> str:
    """
    Wrapper around OpenAI ChatCompletion for gpt-4o-mini
    """
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens
    )
    return response.choices[0].message.content.strip()

def improve_description(product, initial_description, keywords, scorer, all_descriptions, 
                      max_iterations=3, min_improvement=0.5):
    """
    Iteratively improve the product description until the SEO score stabilizes or
    improvement is below a set threshold.
    
    :param product: A dictionary with product details.
    :param initial_description: The first generated description.
    :param keywords: List of keywords to include.
    :param scorer: An instance of SEOScorer.
    :param all_descriptions: List of other descriptions for uniqueness evaluation.
    :param max_iterations: Maximum number of improvement iterations.
    :param min_improvement: Minimum score improvement (in percentage points) to continue refining.
    :return: The improved description.
    """
    best_description = initial_description
    score_data = scorer.score_description(best_description, keywords, all_descriptions)
    best_score = score_data['overall_score']
    print(f"Initial SEO Score: {best_score}")
    
    iteration = 0
    while iteration < max_iterations:
        iteration += 1
        
        # Construct feedback prompt using current description and score
        feedback_prompt = f"""
        The following product description currently has an SEO score of {best_score}/100.
        Identify its main shortcomings in keyword usage, readability, length, structure, and uniqueness.
        Then, produce an improved version addressing these issues.
        Make sure the description:
         - Remains between 100-150 words.
         - Includes the keywords: {', '.join(keywords)}.
         - Clearly describes the product using the provided details.
        
        Product Name: {product['Product Name']}
        Product Features: {product['Product Features']}
        Target Audience: {product['Target Audience']}
        
        Only provide the updated product description.
        """
        print(f"Improvement Iteration {iteration}: Generating improved description...")
        new_description = call_gpt4o(feedback_prompt)
        new_score_data = scorer.score_description(new_description, keywords, all_descriptions)
        new_score = new_score_data['overall_score']
        
        print(f"Iteration {iteration} SEO Score: {new_score}")

        # Check if the improvement is significant
        improvement = new_score - best_score
        if improvement < min_improvement:
            print("Improvement below threshold; stopping iterative refinement.")
            break
        else:
            best_description = new_description
            best_score = new_score
            # Optionally update the 'all_descriptions' list if uniqueness is critical
            all_descriptions.append(new_description)
    
    return best_description

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

def generate_description(product, keywords, model="gpt-4o-mini"):
    """Generate SEO-friendly description using GPT-4o-mini"""
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
        
        description = call_gpt4o(prompt, model=model)
        
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
            
            # Generate initial description
            initial_description = generate_description(product, keywords)
            if not initial_description:
                print("Failed to generate description, skipping...")
                continue
            
            # Get all other descriptions for uniqueness comparison
            all_descriptions = [d['generated_description'] for d in results]
            
            # Improve the description iteratively
            final_description = improve_description(
                product,
                initial_description,
                keywords,
                scorer,
                all_descriptions,
                max_iterations=3,
                min_improvement=0.5
            )
            
            # Calculate final SEO score
            final_score = scorer.score_description(final_description, keywords, all_descriptions)
            
            # Store results
            result = {
                'product_name': product['Product Name'],
                'features': product['Product Features'],
                'target_audience': product['Target Audience'],
                'used_keywords': keywords,
                'generated_description': final_description,
                'seo_score': final_score['overall_score'],
                'detailed_seo_scores': final_score['detailed_scores']
            }
            results.append(result)
            
            # Print SEO score for this description
            print(f"Final SEO Score: {final_score['overall_score']}/100")
            print("Detailed Scores:")
            for metric, score in final_score['detailed_scores'].items():
                print(f"  {metric}: {score}/100")
            print()
            
        except Exception as e:
            print(f"Error processing product {index + 1}: {str(e)}")
            continue
    
    # Save results
    output_file = os.path.join('GeneratedDescriptions', 'generated_descriptions.json')
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