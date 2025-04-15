from . import celery_app
import json
import os
from description_generator import (
    generate_description,
    improve_description,
    find_matching_keywords,
    load_extracted_keywords
)
from seo_scorer import SEOScorer

@celery_app.task
def process_product_description(product_data):
    """
    Celery task to process a single product description
    """
    try:
        # Initialize SEO scorer
        scorer = SEOScorer()
        
        # Load extracted keywords
        extracted_keywords = load_extracted_keywords()
        
        # Find matching keywords
        keywords = find_matching_keywords(product_data['Product Name'], extracted_keywords)
        if not keywords and 'Product Features' in product_data:
            keywords = product_data['Product Features'].split(', ')
        
        # Generate initial description
        initial_description = generate_description(product_data, keywords)
        if not initial_description:
            return {
                'status': 'error',
                'error': 'Failed to generate initial description'
            }
        
        # Load existing descriptions for uniqueness comparison
        all_descriptions = []
        if os.path.exists(os.path.join('GeneratedDescriptions', 'generated_descriptions.json')):
            with open(os.path.join('GeneratedDescriptions', 'generated_descriptions.json'), 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                all_descriptions = [d['generated_description'] for d in existing_data]
        
        # Improve the description
        final_description = improve_description(
            product_data,
            initial_description,
            keywords,
            scorer,
            all_descriptions,
            max_iterations=3,
            min_improvement=0.5
        )
        
        # Calculate final SEO score
        final_score = scorer.score_description(final_description, keywords, all_descriptions)
        
        return {
            'status': 'success',
            'result': {
                'product_name': product_data['Product Name'],
                'features': product_data.get('Product Features', ''),
                'target_audience': product_data.get('Target Audience', ''),
                'used_keywords': keywords,
                'generated_description': final_description,
                'seo_score': final_score['overall_score'],
                'detailed_seo_scores': final_score['detailed_scores']
            }
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }

@celery_app.task
def score_seo_description(description, keywords=None, all_descriptions=None):
    """
    Celery task to calculate SEO score for a description
    """
    try:
        scorer = SEOScorer()
        score = scorer.score_description(
            text=description,
            keywords=keywords or [],
            all_descriptions=all_descriptions or []
        )
        return {
            'status': 'success',
            'score': score
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        } 