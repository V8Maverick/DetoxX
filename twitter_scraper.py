"""
Twitter scraper module using undetected-chromedriver.
"""
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import logging
from typing import List, Dict
import time
import random
from urllib.parse import urlparse, urlunparse
import json

class TwitterScraper:
    def __init__(self):
        """Initialize the scraper."""
        self.logger = logging.getLogger('twitter_scraper')
        self.driver = None
        self.wait = None
        
    def _setup_driver(self):
        """Set up the undetected Chrome driver."""
        try:
            if not self.driver:
                options = uc.ChromeOptions()
                options.add_argument('--headless')  # Run in headless mode
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--window-size=1920,1080')  # Set a standard window size
                options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36')
                
                self.driver = uc.Chrome(options=options)
                self.wait = WebDriverWait(self.driver, 20)  # Increased wait time
                self.logger.info("Chrome driver initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Chrome driver: {str(e)}")
            raise
            
    def _cleanup_driver(self):
        """Clean up the driver resources."""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                self.wait = None
                self.logger.info("Chrome driver cleaned up successfully")
        except Exception as e:
            self.logger.warning(f"Error during driver cleanup: {str(e)}")
            
    def _random_delay(self):
        """Add a random delay between actions."""
        delay = random.uniform(2, 4)
        self.logger.debug(f"Adding random delay of {delay:.2f} seconds")
        time.sleep(delay)
        
    def _normalize_url(self, url: str) -> str:
        """
        Normalize Twitter URL to use x.com domain.
        
        Args:
            url: Twitter URL (twitter.com or x.com)
            
        Returns:
            Normalized URL using x.com domain
        """
        try:
            parsed = urlparse(url)
            if parsed.netloc in ['twitter.com', 'www.twitter.com']:
                # Replace twitter.com with x.com
                new_parsed = parsed._replace(netloc='x.com')
                normalized = urlunparse(new_parsed)
                self.logger.debug(f"Normalized URL from {url} to {normalized}")
                return normalized
            return url
        except Exception as e:
            self.logger.error(f"Error normalizing URL {url}: {str(e)}")
            return url
            
    def _parse_url(self, url: str) -> tuple:
        """
        Parse a Twitter URL to determine the type and ID.
        
        Args:
            url: Twitter URL
            
        Returns:
            Tuple of (type, id) where type is 'profile' or 'thread'
        """
        try:
            # Normalize URL to use x.com
            url = self._normalize_url(url)
            
            parsed = urlparse(url)
            path_parts = parsed.path.strip('/').split('/')
            
            if len(path_parts) >= 1:
                if len(path_parts) >= 2 and path_parts[1] == 'status':
                    self.logger.info(f"Detected thread URL with ID {path_parts[2]}")
                    return 'thread', path_parts[2]
                else:
                    self.logger.info(f"Detected profile URL for user {path_parts[0]}")
                    return 'profile', path_parts[0]
                    
            self.logger.warning(f"Could not determine URL type for {url}")
            return None, None
        except Exception as e:
            self.logger.error(f"Error parsing URL {url}: {str(e)}")
            return None, None
            
    def _scroll_to_load_more(self, scroll_count: int = 5):
        """Scroll the page to load more content."""
        try:
            for i in range(scroll_count):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                self.logger.debug(f"Performed scroll {i + 1}/{scroll_count}")
                self._random_delay()
        except Exception as e:
            self.logger.warning(f"Error during scrolling: {str(e)}")
            
    def _extract_tweet_data(self, tweet_element) -> Dict:
        """Extract data from a tweet element."""
        try:
            # Get tweet text - try multiple selectors
            text_selectors = [
                'div[data-testid="tweetText"]',
                'div[class*="css-"] > span',  # X.com uses dynamic CSS classes
                'div[lang] > span'  # Tweets have a lang attribute
            ]
            
            text = None
            for selector in text_selectors:
                try:
                    text_elements = tweet_element.find_elements(By.CSS_SELECTOR, selector)
                    if text_elements:
                        text = ' '.join([el.text for el in text_elements if el.text])
                        if text:
                            self.logger.debug(f"Found tweet text using selector: {selector}")
                            break
                except NoSuchElementException:
                    continue
                    
            if not text:
                self.logger.warning("Could not find tweet text")
                return None
                
            # Get timestamp
            try:
                time_element = tweet_element.find_element(By.TAG_NAME, 'time')
                timestamp = time_element.get_attribute('datetime')
                self.logger.debug(f"Found tweet timestamp: {timestamp}")
            except NoSuchElementException:
                self.logger.warning("Could not find tweet timestamp")
                timestamp = None
                
            # Get author - try multiple selectors
            author_selectors = [
                'div[data-testid="User-Name"] > div:first-child > div:first-child span',
                'a[role="link"] > div > div > span',
                'div[data-testid="User-Name"] span.css-1qaijid'
            ]
            
            author = None
            for selector in author_selectors:
                try:
                    author_elements = tweet_element.find_elements(By.CSS_SELECTOR, selector)
                    if author_elements:
                        author = author_elements[0].text
                        if author:
                            self.logger.debug(f"Found author using selector: {selector}")
                            break
                except NoSuchElementException:
                    continue
                    
            if not author:
                self.logger.warning("Could not find author")
                return None
                
            tweet_data = {
                'author': author,
                'text': text,
                'timestamp': timestamp,
                'type': 'tweet'
            }
            
            self.logger.info(f"Successfully extracted tweet data from {author}")
            return tweet_data
            
        except Exception as e:
            self.logger.error(f"Error extracting tweet data: {str(e)}")
            return None
            
    def scrape_content(self, url: str) -> List[Dict]:
        """
        Scrape content from a Twitter URL.
        
        Args:
            url: Twitter URL (profile or thread)
            
        Returns:
            List of dictionaries containing tweet data
        """
        try:
            self._setup_driver()
            content_type, content_id = self._parse_url(url)
            
            if not content_type:
                self.logger.error(f"Invalid URL: {url}")
                return []
                
            # Normalize URL to use x.com
            url = self._normalize_url(url)
            
            # Navigate to the URL
            self.logger.info(f"Navigating to URL: {url}")
            self.driver.get(url)
            
            # Wait for initial page load
            self._random_delay()
            
            # Wait for content to load - try multiple selectors
            tweet_selectors = [
                'article[data-testid="tweet"]',
                'article[role="article"]',
                'div[data-testid="cellInnerDiv"]'
            ]
            
            tweet_found = False
            for selector in tweet_selectors:
                try:
                    self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    tweet_found = True
                    self.logger.info(f"Found tweets using selector: {selector}")
                    break
                except TimeoutException:
                    continue
                    
            if not tweet_found:
                self.logger.error("Timeout waiting for tweets to load")
                return []
                
            # Additional wait for dynamic content
            self._random_delay()
            
            content = []
            
            if content_type == 'profile':
                # Scrape profile tweets
                self._scroll_to_load_more()
                tweet_elements = self.driver.find_elements(By.CSS_SELECTOR, 'article[role="article"]')
                self.logger.info(f"Found {len(tweet_elements)} tweets on profile")
                
                for tweet_element in tweet_elements:
                    tweet_data = self._extract_tweet_data(tweet_element)
                    if tweet_data:
                        content.append(tweet_data)
                        
            else:  # thread
                # Scrape thread tweets
                tweet_elements = self.driver.find_elements(By.CSS_SELECTOR, 'article[role="article"]')
                self.logger.info(f"Found {len(tweet_elements)} tweets in thread")
                
                for tweet_element in tweet_elements:
                    tweet_data = self._extract_tweet_data(tweet_element)
                    if tweet_data:
                        content.append(tweet_data)
                        
            self.logger.info(f"Successfully scraped {len(content)} tweets")
            return content
            
        except WebDriverException as e:
            self.logger.error(f"WebDriver error during scraping: {str(e)}")
            return []
        except Exception as e:
            self.logger.error(f"Error scraping content: {str(e)}")
            return []
            
        finally:
            self._cleanup_driver() 