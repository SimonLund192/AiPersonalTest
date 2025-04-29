import json
import os
import openai
from dotenv import load_dotenv
import pandas as pd
from textstat import textstat
import numpy as np
from seo_scorer import SEOScorer
import logging

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

logger = logging.getLogger(__name__)

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
    Iteratively improve the product description, focusing on the weakest SEO metric each time.
    
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
    logger.warning(f"Initial SEO Score: {best_score}")

    iteration = 0
    while iteration < max_iterations:
        iteration += 1

        # Find weakest metric
        weakest_metric = min(score_data['detailed_scores'], key=score_data['detailed_scores'].get)
        weakest_score = score_data['detailed_scores'][weakest_metric]

        logger.warning(f"[Iteration {iteration}] Targeting weakest metric: {weakest_metric} ({weakest_score}/100)")

        # Build focused improvement prompt
        feedback_prompt = f"""
We are improving the following product description, which currently scores {best_score}/100 on SEO.
Its weakest area is **{weakest_metric}**, scoring only {weakest_score}/100.

Revise the description to specifically improve {weakest_metric}.
Keep structure, tone, and strong parts intact. Do not completely rewrite unless necessary.

Requirements:
- Maintain 100-150 words.
- Use the keywords: {', '.join(keywords)}.
- Stay accurate to the product's details.

Product Name: {product['Product Name']}
Product Features: {product['Product Features']}
Target Audience: {product['Target Audience']}

Current Description:
\"\"\"{best_description}\"\"\"

New improved version (only the description, no extra comments):
"""

        logger.warning(f"[Iteration {iteration}] Generating improved description...")

        # Generate improved version
        new_description = call_gpt4o(feedback_prompt)

        # Score new version
        new_score_data = scorer.score_description(new_description, keywords, all_descriptions)
        new_score = new_score_data['overall_score']

        # After improvement: show metrics
        new_weakest_metric = min(new_score_data['detailed_scores'], key=new_score_data['detailed_scores'].get)
        new_weakest_score = new_score_data['detailed_scores'][new_weakest_metric]

        logger.warning(f"[Iteration {iteration}] New overall SEO Score: {new_score}")
        logger.warning(f"[Iteration {iteration}] After improvement: new weakest metric is {new_weakest_metric} ({new_weakest_score}/100)")

        if new_score_data['detailed_scores'][weakest_metric] > score_data['detailed_scores'][weakest_metric]:
            logger.warning(f"[Iteration {iteration}] ✅ Targeted metric '{weakest_metric}' improved from {weakest_score} to {new_score_data['detailed_scores'][weakest_metric]}")
        else:
            logger.warning(f"[Iteration {iteration}] ❌ Targeted metric '{weakest_metric}' did NOT improve (still {new_score_data['detailed_scores'][weakest_metric]})")

        # Compare overall improvement
        improvement = new_score - best_score
        if improvement < min_improvement:
            logger.warning(f"[Iteration {iteration}] Improvement below threshold; stopping iterative refinement.")
            break
        else:
            best_description = new_description
            best_score = new_score
            score_data = new_score_data
            all_descriptions.append(new_description)

        # Optional: Early stop if all metrics are >80
        if all(v >= 80 for v in new_score_data['detailed_scores'].values()):
            logger.warning(f"[Iteration {iteration}] 🚀 All metrics above 80 — stopping early.")
            break

    logger.warning(f"Final SEO Score after refinements: {best_score}")
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

def find_matching_keywords(product_data, extracted_data):
    """
    Find matching keywords from extracted_data by product_id or name fallback.
    :param product_data: dict, the product info (must include either 'product_id' or 'Product Name')
    :param extracted_data: list of dicts loaded from ExtractedData/extracted_keywords.json
    :return: list of up to 5 keywords
    """
    # 1) Try matching by product_id
    pid = product_data.get('product_id')
    if pid:
        for item in extracted_data:
            if item.get('product_id') == pid:
                return item.get('keywords', [])[:5]
    # 2) Fallback: match by name if present
    name = product_data.get('Product Name', '').lower()
    for item in extracted_data:
        if item.get('name', '').lower() == name:
            return item.get('keywords', [])[:5]
    # 3) No match → return empty so features get used
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

def generate_keywords(product, model="gpt-4o-mini"):
    """Generate 5 SEO keywords for a product"""
    try:
        prompt = f"""
        Based on the following product information, generate 5 SEO-friendly keywords or keyphrases.
        They should be short (1-3 words) and very relevant to the product and what people might search for.

        Product Name: {product['Product Name']}
        Product Features: {product['Product Features']}
        Target Audience: {product['Target Audience']}

        List them as a comma-separated list (no numbering or explanations).
        """
        keywords_text = call_gpt4o(prompt, model=model)
        keywords = [k.strip() for k in keywords_text.split(',') if k.strip()]
        print(f"Generated fallback keywords: {keywords}")
        return keywords[:5]
    except Exception as e:
        print(f"Error generating fallback keywords: {str(e)}")
        return []