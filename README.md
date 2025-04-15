# AI Product Description Generator

An automated system that generates SEO-optimized product descriptions using AI and processes them through a distributed task queue.

## Features

- AI-powered product description generation using Ollama
- SEO scoring and optimization
- Distributed task processing with Celery and RabbitMQ
- Keyword extraction and matching
- Iterative description improvement
- Detailed SEO analysis and scoring

## Project Structure

```
.
├── celery_app/                 # Celery task definitions and configuration
│   ├── __init__.py            # Celery app initialization
│   └── tasks.py               # Celery task definitions
├── ExtractedData/             # Directory for extracted keywords
├── GeneratedDescriptions/     # Directory for generated descriptions
├── MockData/                  # Sample data for testing
├── description_generator.py   # Core description generation logic
├── keyword_extractor.py       # Keyword extraction functionality
├── run_description_generator.py # Main script to queue tasks
├── seo_scorer.py             # SEO scoring implementation
├── products.csv              # Input product data
├── requirements.txt          # Project dependencies
└── .env                      # Environment configuration
```

## Prerequisites

- Python 3.8+
- RabbitMQ
- Ollama (for AI model access)
- Virtual environment (recommended)

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-directory>
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
.\.venv\Scripts\activate  # On Windows
source .venv/bin/activate  # On Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install RabbitMQ:
- Windows: Download and install from [RabbitMQ website](https://www.rabbitmq.com/install-windows.html)
- Make sure to install Erlang first as it's required for RabbitMQ

5. Configure environment variables:
Create a `.env` file with the following content:
```
CELERY_BROKER_URL=amqp://localhost
CELERY_RESULT_BACKEND=rpc://
```

## Usage

1. Start the Celery worker (in a separate terminal):
```bash
.\.venv\Scripts\activate  # On Windows
celery -A celery_app worker --pool=solo --loglevel=info
```

2. Run the description generator (in another terminal):
```bash
.\.venv\Scripts\activate  # On Windows
python run_description_generator.py
```

## Input Data Format

The system expects a `products.csv` file with the following columns:
- Product Name
- Product Features
- Target Audience

Example:
```csv
Product Name,Product Features,Target Audience
Wireless Headphones,Noise Cancelling,Bluetooth 5.0,20hr Battery,Music Enthusiasts,Professionals
```

## Output

Generated descriptions are saved in `GeneratedDescriptions/generated_descriptions.json` with the following structure:
```json
[
  {
    "product_name": "Product Name",
    "features": "Feature 1, Feature 2",
    "target_audience": "Target Audience",
    "used_keywords": ["keyword1", "keyword2"],
    "generated_description": "Generated description text...",
    "seo_score": 85.5,
    "detailed_seo_scores": {
      "keyword_score": 90.0,
      "readability_score": 85.0,
      "length_score": 95.0,
      "structure_score": 80.0,
      "uniqueness_score": 75.0
    }
  }
]
```

## SEO Scoring

The system evaluates descriptions based on:
- Keyword usage and density
- Readability (Flesch Reading Ease, Flesch-Kincaid Grade Level)
- Text length (100-150 words ideal)
- Structure (paragraphs, lists, headings)
- Uniqueness compared to other descriptions

## Error Handling

The system includes comprehensive error handling for:
- File I/O operations
- AI model responses
- Task processing
- Data validation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[Your chosen license]

## Acknowledgments

- Ollama for AI model access
- Celery for distributed task processing
- RabbitMQ for message queuing 