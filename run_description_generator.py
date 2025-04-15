import json
import os
import pandas as pd
from celery_app.tasks import process_product_description

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

def main():
    print("Starting description generation process...")
    
    # Load products
    products_df = load_products()
    if products_df is None or products_df.empty:
        print("No products found. Exiting...")
        return
        
    print(f"Loaded {len(products_df)} products")
    
    # Queue tasks and collect task objects
    tasks = []
    for index, product in products_df.iterrows():
        print(f"Queueing product {index + 1}/{len(products_df)}: {product['Product Name']}")
        
        # Convert product Series to dict for serialization
        product_data = product.to_dict()
        
        # Queue the task
        task = process_product_description.delay(product_data)
        tasks.append((product['Product Name'], task))
    
    # Wait for all tasks to complete and collect results
    results = []
    for product_name, task in tasks:
        print(f"Waiting for results for: {product_name}")
        result = task.get()  # This will wait for the task to complete
        
        if result['status'] == 'success':
            results.append(result['result'])
            print(f"✓ Completed {product_name} - SEO Score: {result['result']['seo_score']}/100")
        else:
            print(f"✗ Failed {product_name} - Error: {result.get('error', 'Unknown error')}")
    
    # Save all results
    if results:
        output_file = os.path.join('GeneratedDescriptions', 'generated_descriptions.json')
        os.makedirs('GeneratedDescriptions', exist_ok=True)
        print(f"Saving results to {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Print summary
        avg_score = sum(r['seo_score'] for r in results) / len(results)
        print(f"\nSEO Scoring Summary:")
        print(f"Average Score: {avg_score:.2f}/100")
        print(f"Highest Score: {max(r['seo_score'] for r in results):.2f}/100")
        print(f"Lowest Score: {min(r['seo_score'] for r in results):.2f}/100")
    else:
        print("\nNo descriptions were generated successfully.")

if __name__ == "__main__":
    main() 