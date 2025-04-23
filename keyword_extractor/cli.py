import argparse
import logging
from pipeline import run_pipeline


def main():
    parser = argparse.ArgumentParser(
        description="Run the keyword extraction pipeline"
    )
    parser.add_argument(
        '--method', choices=['tfidf','rake'],
        help="Override default extraction method"
    )
    parser.add_argument(
        '--top-n', type=int,
        help="Override number of keywords per item"
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )

    run_pipeline(method=args.method, top_n=args.top_n)

if __name__ == '__main__':
    main()
