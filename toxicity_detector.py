"""
Toxicity detection module using the Friendly Text Moderator via Gradio.
"""
import logging
from typing import List, Dict, Tuple
import time
import random
from gradio_client import Client
import json

class ToxicityDetector:
    def __init__(self):
        """Initialize the toxicity detector."""
        self.logger = logging.getLogger('toxicity_detector')
        self.client = Client("duchaba/Friendly_Text_Moderation")
        self.safer_value = 0.02
        
    def _random_delay(self):
        """Add a random delay between API calls to avoid rate limiting."""
        time.sleep(random.uniform(0.5, 1.5))
        
    def _analyze_text(self, text: str) -> Dict:
        """
        Analyze a single text for toxicity using the Gradio endpoint.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary containing toxicity analysis results
        """
        try:
            self._random_delay()
            # Call the API with positional arguments and ignore the first element
            _, json_result = self.client.predict(
                text,           # msg
                self.safer_value,  # safer threshold
                api_name="/fetch_toxicity_level"
            )
            
            # Parse the JSON string result into a dictionary
            result_dict = json.loads(json_result)
            
            # Extract toxicity values from the dictionary
            toxicity_score = result_dict.get('sum_value', 0)
            is_toxic = result_dict.get('is_flagged', False) or result_dict.get('is_safer_flagged', False)
            
            toxicity_details = {
                'harassment': result_dict.get('harassment', 0),
                'harassment_threatening': result_dict.get('harassment_threatening', 0),
                'hate': result_dict.get('hate', 0),
                'hate_threatening': result_dict.get('hate_threatening', 0),
                'self_harm': result_dict.get('self_harm', 0),
                'self_harm_instructions': result_dict.get('self_harm_instructions', 0),
                'self_harm_intent': result_dict.get('self_harm_intent', 0),
                'sexual': result_dict.get('sexual', 0),
                'sexual_minors': result_dict.get('sexual_minors', 0),
                'violence': result_dict.get('violence', 0),
                'violence_graphic': result_dict.get('violence_graphic', 0)
            }
            
            max_category = result_dict.get('max_key', 'none')
            max_value = result_dict.get('max_value', 0)
            
            return {
                'toxicity_score': toxicity_score,
                'is_toxic': is_toxic,
                'toxicity_details': toxicity_details,
                'max_category': max_category,
                'max_value': max_value
            }
            
        except Exception as e:
            self.logger.error(f"Analysis failed: {str(e)}")
            return {'error': str(e)}
            
    def analyze_comments(self, content: List[Dict]) -> Tuple[List[Dict], Dict]:
        """
        Analyze a list of comments for toxicity.
        
        Args:
            content: List of dictionaries containing comment data
            
        Returns:
            Tuple of (analyzed_content, stats)
        """
        analyzed_content = []
        toxic_count = 0
        
        for item in content:
            # Get text from tweet content
            text_to_analyze = item.get('text', '')
            
            if not text_to_analyze:
                continue
                
            # Analyze the text
            analysis = self._analyze_text(text_to_analyze)
            
            # Determine if content is toxic
            is_toxic = False
            if 'error' not in analysis:
                # Check toxicity score
                toxicity_score = analysis.get('toxicity_score', 0)
                is_toxic = toxicity_score > 0.7  # Threshold for toxicity
                
                if is_toxic:
                    toxic_count += 1
                    
            # Add analysis results to the item
            item['is_toxic'] = is_toxic
            item['toxicity_score'] = analysis.get('toxicity_score', 0)
            item['toxicity_details'] = analysis.get('toxicity_details', {})
            analyzed_content.append(item)
            
        # Calculate statistics
        total_count = len(analyzed_content)
        toxic_percentage = (toxic_count / total_count * 100) if total_count > 0 else 0
        
        stats = {
            'total_count': total_count,
            'toxic_count': toxic_count,
            'toxic_percentage': toxic_percentage
        }
        
        return analyzed_content, stats 