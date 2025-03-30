# Twitter Toxicity Analyzer

A web application that analyzes Twitter content for toxic language using the Friendly Text Moderator via Gradio.

## Features

- Scrape content from Twitter profiles and threads using undetected-webdriver
- Analyze text for toxicity using the Friendly Text Moderator
- Visualize toxicity statistics with interactive charts
- Filter content by toxicity level
- Modern, responsive UI

## Prerequisites

- Python 3.8 or higher
- Chrome browser installed

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd detoxx2
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the Flask application:
```bash
python app.py
```

2. Open your web browser and navigate to `http://localhost:5000`

3. Enter a Twitter URL (profile or thread) to analyze

4. View the toxicity analysis results and statistics

## Configuration

The following environment variables can be configured:

- `TOXICITY_THRESHOLD`: Threshold for determining toxic content (default: 0.7)
- `SAFER_VALUE`: Value for safer content detection (default: 0.02)

## Notes

- The application uses undetected-webdriver to bypass Twitter's anti-scraping measures
- Content is scraped in headless mode by default
- Rate limiting and delays are implemented to avoid detection
- The toxicity analysis is powered by the Friendly Text Moderator via Gradio

## License

MIT License 