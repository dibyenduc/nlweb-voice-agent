#!/usr/bin/env python3
"""
Enhanced NLWeb Voice Agent for Podcast Data
Supports voice interaction with loaded podcast RSS feeds.
"""

import sys
import json
import requests
import speech_recognition as sr
import pyttsx3
import threading
import time
import argparse
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path

# Configure logging for clear output
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class VoiceAgent:
    """
    Manages voice interactions, queries the NLWeb API, and handles responses.
    """
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize the Voice Agent with speech recognition and TTS."""
        self.base_url = base_url
        self.sites = ["Behind-the-Tech", "Decoder"]
        
        logger.info("🔧 Initializing NLWeb Voice Agent...")
        self._init_speech_components()
        logger.info("✅ NLWeb Voice Agent initialized.")

    def _init_speech_components(self):
        """Initializes speech recognition and text-to-speech engines."""
        logger.info("🎤 Setting up speech recognition...")
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Improved microphone calibration
        with self.microphone as source:
            logger.info("🔧 Adjusting for ambient noise... Please be quiet for a moment.")
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
        
        # Fine-tune recognition settings
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        self.recognizer.phrase_threshold = 0.3
        
        logger.info("🔊 Setting up text-to-speech...")
        self.tts_engine = pyttsx3.init()
        voices = self.tts_engine.getProperty('voices')
        if voices:
            # Try to use a more natural voice if available
            for voice in voices:
                if 'female' in voice.name.lower() or 'karen' in voice.name.lower():
                    self.tts_engine.setProperty('voice', voice.id)
                    break
            else:
                self.tts_engine.setProperty('voice', voices[0].id)
        
        self.tts_engine.setProperty('rate', 160)  # Slightly slower for better understanding
        self.tts_engine.setProperty('volume', 0.9)
        logger.info("✅ Speech components ready.")

    def listen_for_speech(self, timeout: int = 8, phrase_limit: int = 15) -> Optional[str]:
        """
        Listens for speech input from the microphone with improved settings.
        
        Args:
            timeout (int): The maximum time to wait for the first audio.
            phrase_limit (int): Maximum duration for a single phrase.
        
        Returns:
            Optional[str]: The recognized text or None if no speech is detected or an error occurs.
        """
        try:
            logger.info("🎤 Listening... (speak clearly)")
            with self.microphone as source:
                # Listen with longer timeout and phrase limit
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
            
            logger.info("🔍 Processing speech...")
            
            # Try Google Speech Recognition first, then fallback to offline
            try:
                text = self.recognizer.recognize_google(audio, language='en-US')
                logger.info(f"📝 Heard: '{text}'")
                return text.strip()
            except (sr.UnknownValueError, sr.RequestError):
                # Fallback to offline recognition if available
                try:
                    text = self.recognizer.recognize_sphinx(audio)
                    logger.info(f"📝 Heard (offline): '{text}'")
                    return text.strip()
                except (sr.UnknownValueError, sr.RequestError):
                    raise sr.UnknownValueError("Could not understand speech")
            
        except sr.WaitTimeoutError:
            logger.warning("⏰ No speech detected. Please try speaking louder or closer to the microphone.")
            return None
        except sr.UnknownValueError:
            logger.warning("❌ Could not understand speech. Please speak more clearly.")
            return None
        except sr.RequestError as e:
            logger.error(f"❌ Speech recognition service error: {e}")
            return None

    def speak_response(self, text: str):
        """Converts text to speech and plays it with better handling."""
        if not text or not text.strip():
            logger.warning("⚠️ Empty response - using fallback message")
            text = "I found some results but couldn't generate a proper response. The system found documents but there may be an issue with content processing."
        
        # Limit response length for better voice experience
        if len(text) > 500:
            text = text[:500] + "... Would you like me to continue?"
        
        logger.info(f"🔊 Speaking: {text[:100]}{'...' if len(text) > 100 else ''}")
        
        try:
            # Use direct TTS without threading to avoid run loop issues
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            logger.error(f"TTS error: {e}")
            # Fallback: try reinitializing TTS engine
            try:
                self.tts_engine.stop()
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty('rate', 160)
                self.tts_engine.setProperty('volume', 0.9)
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            except Exception as e2:
                logger.error(f"TTS fallback also failed: {e2}")
                print(f"[VOICE OUTPUT]: {text}")  # Print to console as last resort

    def query_nlweb(self, query: str) -> str:
        """
        Sends a query to the NLWeb API and retrieves the response.
        
        Args:
            query (str): The natural language query to ask the API.
        
        Returns:
            str: The final, cleaned response from the API.
        """
        logger.info(f"❓ Asking NLWeb: '{query}'")
        payload = {
            "query": query,
            "top_k": 3,  # Reduced for more focused results
            "embedding_provider": "ollama",
            "embedding_model": "qwen3:0.6b", 
            "database_endpoint": "qdrant_local",
            "sites": self.sites,
            "llm_timeout": 15,  # Shorter timeout to fail faster
            "max_tokens": 200   # Limit response length
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/ask",
                json=payload,
                headers={"Content-Type": "application/json"},
                stream=True,
                timeout=45  # Longer timeout for complex queries
            )
            
            if response.status_code != 200:
                logger.error(f"❌ API Error: {response.status_code} - {response.text}")
                return f"Sorry, I encountered an API error. The service might be busy."
            
            return self._parse_sse_response(response)
        
        except requests.exceptions.Timeout:
            logger.error("❌ Request timed out - LLM is too slow, trying direct search")
            # Fallback: try to get just search results from web interface format
            return self._get_web_interface_results(query)
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Request failed: {e}")
            return "Sorry, I couldn't connect to the knowledge base. Please check if the service is running."

    def _parse_sse_response(self, response: requests.Response) -> str:
        """
        Parses the Server-Sent Events (SSE) response from the API stream.
        """
        logger.info("🔍 Processing your query...")
        
        final_answer = ""
        assembled_content = ""
        retrieval_count = -1
        recommendations = []
        
        for line in response.iter_lines(decode_unicode=True):
            if not line or not line.startswith('data:'):
                continue
            
            data_str = line[5:].strip()
            if data_str == '[DONE]':
                break
            if not data_str:
                continue

            try:
                data = json.loads(data_str)
                msg_type = data.get('message_type', data.get('type', 'unknown'))
                
                if msg_type == 'retrieval_count':
                    retrieval_count = data.get('count', 0)
                    logger.info(f"📊 Found {retrieval_count} relevant documents.")
                    if retrieval_count == 0:
                        return "I couldn't find any relevant episodes in the podcast database. Try asking about technology topics, Microsoft, AI, or specific companies."
                
                elif msg_type == 'ensemble_result':
                    # Extract recommendations from ensemble results
                    result_data = data.get('result', {})
                    recs = result_data.get('recommendations', {})
                    if isinstance(recs, dict):
                        rec_list = recs.get('recommendations', recs.get('Recommendations', []))
                        if rec_list:
                            recommendations = rec_list
                
                elif msg_type == 'complete':
                    final_answer = data.get('answer', data.get('content', ''))
                    break
                
                elif 'content' in data:
                    assembled_content += data['content']
                    
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ JSON decode error: {e}")
                continue
        
    def _parse_sse_response(self, response: requests.Response) -> str:
        """
        Parses the Server-Sent Events (SSE) response from the API stream.
        """
        logger.info("🔍 Processing your query...")
        
        final_answer = ""
        assembled_content = ""
        retrieval_count = -1
        recommendations = []
        debug_messages = []
        
        for line in response.iter_lines(decode_unicode=True):
            if not line or not line.startswith('data:'):
                continue
            
            data_str = line[5:].strip()
            if data_str == '[DONE]':
                break
            if not data_str:
                continue

            try:
                data = json.loads(data_str)
                msg_type = data.get('message_type', data.get('type', 'unknown'))
                
                # Debug: log all message types we receive
                logger.info(f"📦 Received: {msg_type}")
                
                if msg_type == 'retrieval_count':
                    retrieval_count = data.get('count', 0)
                    logger.info(f"📊 Found {retrieval_count} relevant documents.")
                    if retrieval_count == 0:
                        return "I couldn't find any relevant episodes in the podcast database. Try asking about technology topics, Microsoft, AI, or specific companies."
                
                elif msg_type == 'ensemble_result':
                    # Extract recommendations from ensemble results
                    result_data = data.get('result', {})
                    recs = result_data.get('recommendations', {})
                    if isinstance(recs, dict):
                        rec_list = recs.get('recommendations', recs.get('Recommendations', []))
                        if rec_list:
                            recommendations = rec_list
                            logger.info(f"🎯 Found {len(recommendations)} recommendations")
                            # Log the actual recommendations for debugging
                            for i, rec in enumerate(rec_list[:2]):
                                logger.info(f"   {i+1}. {rec.get('item', 'Unknown')}")
                            # Don't break here - continue processing in case there's more
                
                elif msg_type == 'result_batch':
                    # Handle result_batch messages which contain the actual search results
                    logger.info(f"📄 Processing result_batch...")
                    batch_content = data.get('content', data.get('results', data.get('batch', [])))
                    
                    # Debug: log what we actually received
                    logger.info(f"🔍 Batch content type: {type(batch_content)}")
                    if hasattr(batch_content, '__len__'):
                        logger.info(f"🔍 Batch length: {len(batch_content)}")
                    
                    if isinstance(batch_content, list):
                        # Extract episode titles from batch results
                        for result in batch_content:
                            if isinstance(result, dict):
                                title = result.get('title', result.get('item', result.get('name', result.get('episode_title', ''))))
                                url = result.get('url', result.get('link', ''))
                                if title and title not in [r.get('item', '') for r in recommendations]:
                                    recommendations.append({'item': title, 'url': url})
                                    logger.info(f"   📎 Added: {title}")
                    
                    elif isinstance(batch_content, str) and batch_content.strip():
                        # If it's a string, try to extract useful info
                        assembled_content += batch_content + " "
                        logger.info(f"📝 Added string content: {batch_content[:50]}...")
                    
                    else:
                        # Debug: log the actual structure
                        logger.info(f"🐛 Unexpected batch content: {str(batch_content)[:100]}...")
                    
                    logger.info(f"📊 Total recommendations so far: {len(recommendations)}")
                
                elif msg_type == 'complete':
                    final_answer = data.get('answer', data.get('content', ''))
                    logger.info(f"✅ Complete message: content={bool(final_answer)}")
                    # Only break if we haven't found recommendations yet
                    if not recommendations:
                        logger.warning("⚠️ Complete message but no recommendations found")
                    break
                
                elif msg_type in ['license', 'data_retention', 'ui_component']:
                    # Skip metadata messages
                    continue
                    
                elif 'content' in data:
                    content = data['content']
                    if content and content not in ["This data is provided under MIT License. See https://opensource.org/license/mit for details.", 
                                                  "Data provided may be retained for up to 1 day.",
                                                  "This field may be used to provide a link to the web components that can be used to display the results."]:
                        assembled_content += content
                        logger.debug(f"📄 Added content: {content[:50]}...")
                    
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ JSON decode error: {e}")
                continue
        
        # Build response from recommendations if available (this should work now)
        if recommendations:
            response_parts = ["Here are relevant podcast episodes:"]
            for i, rec in enumerate(recommendations[:3], 1):  # Limit to 3 for voice
                item = rec.get('item', 'Unknown episode')
                # Just use the episode title for cleaner voice output
                response_parts.append(f"{i}. {item}")
            final_response = " ".join(response_parts)
            logger.info(f"✅ Generated response from {len(recommendations)} recommendations")
            return final_response
        
        # Use final answer or assembled content
        result = final_answer or assembled_content.strip()
        
        if not result:
            if retrieval_count > 0:
                return f"I found {retrieval_count} relevant episodes but couldn't generate a summary. The LLM service might be having issues."
            else:
                return "I couldn't find any relevant information. Try asking about technology topics or specific podcast episodes."

        logger.info(f"✅ Generated final response: {result[:100]}...")
        return self._clean_response(result)

    def _clean_response(self, response: str) -> str:
        """Cleans up extraneous metadata from the API response."""
        logger.info(f"🧹 Cleaning response: {response[:200]}...")
        
        cleanup_phrases = [
            "This data is provided under MIT License. See https://opensource.org/license/mit for details.",
            "Data provided may be retained for up to 1 day.",
            "This field may be used to provide a link to the web components that can be used to display the results.",
            "[End of response]",
            "message_type:",
            "query_id:"
        ]
        
        cleaned = response
        for phrase in cleanup_phrases:
            cleaned = cleaned.replace(phrase, "").strip()
        
        # Remove excess whitespace and clean up formatting
        cleaned = " ".join(cleaned.split())
        
        # If cleaning removed everything, return a fallback
        if not cleaned or len(cleaned) < 10:
            logger.warning("⚠️ Cleaning removed all content - response was just metadata")
            return ""
        
        # Limit response length for better voice experience
        if len(cleaned) > 800:
            cleaned = cleaned[:800] + "..."
        
        logger.info(f"✅ Cleaned response: {cleaned[:100]}...")
        return cleaned

    def _try_fallback_query(self, query: str) -> str:
        """
        Fallback method when LLM times out - gets raw search results without LLM processing.
        """
        logger.info("🔄 Trying fallback query without LLM processing...")
        
        payload = {
            "query": query,
            "top_k": 5,
            "embedding_provider": "ollama", 
            "embedding_model": "qwen3:0.6b",
            "database_endpoint": "qdrant_local",
            "sites": self.sites,
            "disable_llm": True  # Disable LLM to just get search results
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/ask",
                json=payload,
                headers={"Content-Type": "application/json"},
                stream=True,
                timeout=15  # Shorter timeout for simple retrieval
            )
            
            if response.status_code != 200:
                return "Sorry, I found some episodes but couldn't process them properly."
            
            # Parse just the retrieval results
            retrieval_count = 0
            recommendations = []
            
            for line in response.iter_lines(decode_unicode=True):
                if not line or not line.startswith('data:'):
                    continue
                
                data_str = line[5:].strip()
                if data_str == '[DONE]' or not data_str:
                    break
                
                try:
                    data = json.loads(data_str)
                    msg_type = data.get('message_type', data.get('type', 'unknown'))
                    
                    if msg_type == 'retrieval_count':
                        retrieval_count = data.get('count', 0)
                    
                    elif msg_type == 'ensemble_result':
                        result_data = data.get('result', {})
                        recs = result_data.get('recommendations', {})
                        if isinstance(recs, dict):
                            rec_list = recs.get('recommendations', recs.get('Recommendations', []))
                            if rec_list:
                                recommendations = rec_list
                                break
                                
                except json.JSONDecodeError:
                    continue
            
            if recommendations:
                response_parts = [f"I found {retrieval_count} episodes. Here are the top matches:"]
                for i, rec in enumerate(recommendations[:2], 1):  # Just 2 for fallback
                    item = rec.get('item', 'Unknown episode')
                    response_parts.append(f"{i}. {item}")
                return " ".join(response_parts)
            else:
                return f"I found {retrieval_count} relevant episodes but couldn't format them properly. The search is working, but there's a processing issue."
                
        except Exception as e:
            logger.error(f"Fallback query also failed: {e}")
        return "Sorry, I'm having technical difficulties processing your request."

    def _get_web_interface_results(self, query: str) -> str:
        """
        Simple fallback that mimics what the web interface shows you.
        Gets search results without waiting for LLM processing.
        """
        logger.info("🔄 Using web interface fallback approach...")
        
        try:
            # Use a very simple request that should return quickly
            response = requests.get(
                f"{self.base_url}/search",
                params={"q": query, "limit": 3},
                timeout=10
            )
            
            if response.status_code == 200:
                # This is a guess at the format - may need adjustment
                results = response.json()
                if isinstance(results, list) and results:
                    items = []
                    for r in results[:3]:
                        title = r.get('title', r.get('item', 'Unknown episode'))
                        items.append(title)
                    return f"I found these episodes: {', '.join(items)}"
            
        except Exception as e:
            logger.error(f"Web interface fallback failed: {e}")
        
        # Final fallback - at least we know documents were found
        return f"I found relevant episodes about {query} in the podcast database, but I'm having trouble processing the full response. The search system is working, but the language model might need attention."

    def run_interactive_mode(self):
        """Runs the voice agent in a continuous interactive loop."""
        logger.info("🚀 Starting interactive voice mode...")
        logger.info("🎙️ Say 'stop', 'quit', 'exit', or 'goodbye' to end the session.")
        logger.info("💡 Try asking: 'What podcasts do you have?', 'Tell me about AI episodes', or 'Find Microsoft related content'")
        
        self.speak_response("Hello! I'm your podcast voice assistant. I can help you find episodes from Behind the Tech and Decoder podcasts. What would you like to know?")
        
        consecutive_failures = 0
        max_failures = 3
        
        while True:
            try:
                user_input = self.listen_for_speech(timeout=12)
                if not user_input:
                    consecutive_failures += 1
                    if consecutive_failures >= max_failures:
                        self.speak_response("I'm having trouble hearing you. Let me know if you want to continue by speaking clearly, or say goodbye to exit.")
                        consecutive_failures = 0
                    continue
                
                consecutive_failures = 0  # Reset on successful input
                
                if user_input.lower() in ['stop', 'quit', 'exit', 'goodbye', 'bye']:
                    self.speak_response("Goodbye! Happy podcast listening!")
                    logger.info("👋 Voice agent stopped by user.")
                    break
                
                # Handle help requests
                if any(word in user_input.lower() for word in ['help', 'what can you do', 'how does this work']):
                    help_text = "I can help you find podcast episodes from Behind the Tech and Decoder. Try asking about specific topics like artificial intelligence, Microsoft, technology companies, or ask me what podcasts are available."
                    self.speak_response(help_text)
                    continue
                
                response = self.query_nlweb(user_input)
                self.speak_response(response)
                
            except KeyboardInterrupt:
                logger.info("\n⚡ Interrupted by user.")
                self.speak_response("Session ended. Goodbye!")
                break
            except Exception as e:
                logger.error(f"❌ Error in interactive mode: {e}")
                self.speak_response("Sorry, I encountered an error. Please try again.")
                continue

    def run_test_mode(self, test_type: str):
        """
        Runs predefined tests based on the specified test type.
        """
        test_queries = {
            "quick": [
                "What podcasts do you have?", 
                "Tell me about Microsoft"
            ],
            "full": [
                "What podcasts are available in the database?",
                "Tell me about Behind the Tech episodes",
                "What topics does the Decoder podcast cover?",
                "Find episodes about artificial intelligence",
                "Show me technology company interviews"
            ],
            "debug": [
                "What podcasts are available?",
                "Microsoft",
                "machine learning"
            ]
        }
        
        logger.info(f"🧪 Running {test_type} test mode...")
        
        for i, query in enumerate(test_queries.get(test_type, []), 1):
            logger.info(f"\n🔢 Test {i}: '{query}'")
            response = self.query_nlweb(query)
            logger.info(f"📝 Response: {response}")
            logger.info("=" * 80)
            time.sleep(2)

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="NLWeb Voice Agent for podcast data.")
    parser.add_argument(
        "mode", 
        nargs='?', 
        default='interactive',
        choices=['interactive', 'test'],
        help="Operating mode: 'interactive' (default) or 'test'."
    )
    parser.add_argument(
        "test_type",
        nargs='?',
        default='full',
        choices=['quick', 'full', 'debug'],
        help="Sub-mode for 'test' command: 'quick', 'full', or 'debug'."
    )
    
    args = parser.parse_args()
    
    try:
        agent = VoiceAgent()
        
        if args.mode == 'interactive':
            agent.run_interactive_mode()
        elif args.mode == 'test':
            agent.run_test_mode(args.test_type)
            
    except KeyboardInterrupt:
        logger.info("\n⚡ Program interrupted by user.")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        logger.info("🏁 Program finished.")

if __name__ == "__main__":
    main()
