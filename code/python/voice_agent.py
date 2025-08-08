import requests
import speech_recognition as sr
import pyttsx3
import time
import json
import re

class NLWebVoiceAgent:
    def __init__(self, nlweb_url="http://localhost:8000"):
        self.nlweb_url = nlweb_url
        self.api_endpoint = "/ask"  # We know this works
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Initialize TTS engine
        self.tts_engine = pyttsx3.init()
        self.tts_engine.setProperty('rate', 180)
        self.tts_engine.setProperty('volume', 0.9)
        
        print("✅ NLWeb Voice Agent initialized with /ask endpoint")
    
    def parse_sse_response(self, response_text):
        """Parse Server-Sent Events response format"""
        try:
            # SSE format is: data: {json}\ndata: {json}\n...
            lines = response_text.strip().split('\n')
            
            answer_parts = []
            retrieval_info = None
            
            for line in lines:
                if line.startswith('data: '):
                    json_str = line[6:]  # Remove 'data: ' prefix
                    try:
                        data = json.loads(json_str)
                        message_type = data.get('message_type', '')
                        
                        if message_type == 'retrieval_count':
                            retrieval_info = data
                            print(f"📊 Found {data.get('count', 0)} relevant documents")
                            
                        elif message_type == 'answer_chunk':
                            # This contains part of the answer
                            chunk = data.get('content', '')
                            if chunk:
                                answer_parts.append(chunk)
                                
                        elif message_type == 'final_answer':
                            # Complete answer
                            return data.get('content', data.get('answer', ''))
                            
                        elif 'answer' in data:
                            # Sometimes the answer is directly in the data
                            return data['answer']
                            
                        elif 'content' in data and data.get('message_type') != 'retrieval_count':
                            answer_parts.append(data['content'])
                            
                    except json.JSONDecodeError:
                        continue
            
            # Combine answer parts if we collected chunks
            if answer_parts:
                return ''.join(answer_parts).strip()
            
            # If no clear answer found, return a helpful message
            if retrieval_info and retrieval_info.get('count', 0) == 0:
                return "I couldn't find any relevant information in the knowledge base for that question."
            
            return "I received a response but couldn't extract a clear answer. Please try rephrasing your question."
            
        except Exception as e:
            print(f"Error parsing response: {e}")
            return "I had trouble processing the response from NLWeb."
    
    def query_nlweb(self, question, site_filter="all"):
        """Send query to NLWeb and parse SSE response"""
        try:
            # NLWeb /ask endpoint typically expects form data, not JSON
            payload = {
                "question": question,
                "site": site_filter
            }
            
            print(f"🔄 Querying: {question}")
            
            # Try JSON first
            response = requests.post(
                f"{self.nlweb_url}{self.api_endpoint}",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream"  # Accept SSE
                },
                timeout=15
            )
            
            if response.status_code == 200:
                answer = self.parse_sse_response(response.text)
                return answer
            else:
                print(f"JSON request failed with {response.status_code}, trying form data...")
                
                # Try form data format
                response = requests.post(
                    f"{self.nlweb_url}{self.api_endpoint}",
                    data=payload,  # Use data instead of json
                    headers={
                        "Accept": "text/event-stream"
                    },
                    timeout=15
                )
                
                if response.status_code == 200:
                    answer = self.parse_sse_response(response.text)
                    return answer
                else:
                    return f"Both JSON and form requests failed. Status: {response.status_code}"
                
        except requests.exceptions.Timeout:
            return "The request timed out. Please try again with a shorter question."
        except Exception as e:
            print(f"Exception details: {e}")
            return f"Error connecting to NLWeb: {str(e)}"
    
    def test_connection(self):
        """Test the NLWeb connection with a simple query"""
        print("🧪 Testing NLWeb connection...")
        response = self.query_nlweb("Hello")
        print(f"Test response: {response}")
        
        success = (
            response and 
            "Error" not in response and 
            "failed" not in response.lower() and
            len(response.strip()) > 0
        )
        
        if success:
            print("✅ Connection test passed!")
        else:
            print("❌ Connection test failed")
            
        return
