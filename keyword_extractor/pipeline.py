import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
import numpy as np

from config import (
    PRODUCT_FILE, CATEGORIES_FILE, EXTRACTED_DIR,
    TFIDF_PARAMS, TOP_N, DEFAULT_METHOD,
    SPACY_MODEL, CUSTOM_STOPWORDS
)
from preprocessing import TextPreprocessor
from extractor import KeywordExtractor
from io_utils import load_json, save_json


def run_pipeline(method=None, top_n=None):
    logging.info("Starting keyword extraction pipeline…")

    # Load data
    products = load_json(PRODUCT_FILE)
    categories = load_json(CATEGORIES_FILE)
    if not products:
        logging.error("No products loaded. Exiting.")
        return

    cat_lookup = {
        str(c.get('category_id','')): c.get('category_path','')
        for c in categories
        if c.get('category_id') is not None
    }

    # Preprocessing
    method = method or DEFAULT_METHOD
    top_n = top_n or TOP_N
    preprocessor = TextPreprocessor(
        model_name=SPACY_MODEL,
        custom_stops=CUSTOM_STOPWORDS
    )

    combined = [
        (p.get('id',''), f"{p.get('name','')} {p.get('description','')}")
        for p in products
    ]

    logging.info("Preprocessing texts…")
    processed_texts = [''] * len(combined)
    with ProcessPoolExecutor() as executor:
        futures = {executor.submit(preprocessor, txt): idx for idx, (_, txt) in enumerate(combined)}
        for fut in as_completed(futures):
            processed_texts[futures[fut]] = fut.result()

    # Global TF-IDF
    extractor = KeywordExtractor(
        method=method,
        top_n=top_n,
        **TFIDF_PARAMS
    )
    extractor.fit(processed_texts)

    # Per-product
    logging.info("Extracting product keywords…")
    prod_results = []
    for idx, (pid, _) in enumerate(combined):
        kws = (
            extractor.extract(None, doc_index=idx)
            if method == 'tfidf'
            else extractor.extract(processed_texts[idx])
        )
        prod_results.append({
            'product_id': pid,
            'keywords':   [k for k,_ in kws],
            'scores':     [s for _,s in kws]
        })
    save_json(prod_results, EXTRACTED_DIR / 'extracted_keywords.json')

    # Per-category
    logging.info("Extracting category keywords…")
    cat_results = []
    for cid, cname in cat_lookup.items():
        idxs = [i for i,p in enumerate(products)
                if p.get('category_id') == cid and processed_texts[i].strip()]
        if not idxs:
            continue
        sub_corpus = [processed_texts[i] for i in idxs]
        sub_ex = KeywordExtractor(method=method, top_n=top_n, **TFIDF_PARAMS)
        sub_ex.fit(sub_corpus)
        agg = sub_ex.tfidf_matrix.toarray().sum(axis=0)
        top_idxs = np.argsort(agg)[-top_n:][::-1]
        kws = [(sub_ex.features[i], float(agg[i])) for i in top_idxs if agg[i] > 0]
        cat_results.append({
            'category_id':   cid,
            'category_name': cname,
            'keywords':      [k for k,_ in kws],
            'scores':        [s for _,s in kws]
        })
    save_json(cat_results, EXTRACTED_DIR / 'category_keywords.json')

    logging.info("Pipeline completed successfully.")