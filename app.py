"""
Main Flask application for the Twitter Toxicity Analyzer.
"""
from flask import Flask, render_template, request, jsonify
import logging
from twitter_scraper import TwitterScraper
from toxicity_detector import ToxicityDetector
import plotly.graph_objects as go
import json
import plotly
import os
from logging.handlers import RotatingFileHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
scraper = TwitterScraper()
detector = ToxicityDetector()

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """Analyze content from a given URL."""
    try:
        url = request.form.get('url')
        if not url:
            return jsonify({'error': 'No URL provided'}), 400
            
        logger.info(f"Analyzing content from URL: {url}")
        
        # Scrape content
        content = scraper.scrape_content(url)
        if not content:
            return jsonify({'error': 'No content found at the provided URL'}), 404
            
        # Analyze toxicity
        analyzed_content, stats = detector.analyze_comments(content)
        
        # Create toxicity distribution chart
        toxic_count = stats['toxic_count']
        safe_count = stats['total_count'] - toxic_count
        
        fig = go.Figure(data=[go.Pie(
            labels=['Toxic', 'Safe'],
            values=[toxic_count, safe_count],
            hole=.3,
            marker_colors=['#e74c3c', '#2ecc71']
        )])
        
        fig.update_layout(
            title='Toxicity Distribution',
            showlegend=True,
            height=400
        )
        
        chart = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        
        return jsonify({
            'content': analyzed_content,
            'stats': stats,
            'chart': chart
        })
        
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
        
    # Set up file handler
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    
    app.run(debug=True) 