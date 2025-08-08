import json
import requests
from datetime import datetime
import re

class MultimodalVoiceAgent:
    def __init__(self, nlweb_url="http://localhost:8000"):
        self.nlweb_url = nlweb_url
        self.conversation_history = []
        
    def classify_query(self, query):
        """Classify the type of query to route appropriately"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['weather', 'temperature', 'forecast']):
            return 'weather'
        elif any(word in query_lower for word in ['time', 'date', 'day']):
            return 'datetime'
        elif any(word in query_lower for word in ['calculate', 'math', 'plus', 'minus']):
            return 'calculation'
        else:
            return 'knowledge'
    
    def handle_query(self, query):
        """Route query to appropriate handler"""
        query_type = self.classify_query(query)
        
        if query_type == 'datetime':
            return self.handle_datetime_query(query)
        elif query_type == 'calculation':
            return self.handle_calculation_query(query)
        else:
            return self.handle_knowledge_query(query)
    
    def handle_datetime_query(self, query):
        """Handle date/time related queries"""
        now = datetime.now()
        
        if 'time' in query.lower():
            return f"The current time is {now.strftime('%I:%M %p')}"
        elif 'date' in query.lower():
            return f"Today is {now.strftime('%A, %B %d, %Y')}"
        else:
            return f"Today is {now.strftime('%A, %B %d, %Y')} and the time is {now.strftime('%I:%M %p')}"
    
    def handle_calculation_query(self, query):
        """Handle basic math queries"""
        # Simple math expression extraction
        math_pattern = r'(\d+(?:\.\d+)?)\s*([\+\-\*\/])\s*(\d+(?:\.\d+)?)'
        match = re.search(math_pattern, query)
        
        if match:
            num1, op, num2 = match.groups()
            num1, num2 = float(num1), float(num2)
            
            if op == '+':
                result = num1 + num2
            elif op == '-':
                result = num1 - num2
            elif op == '*':
                result = num1 * num2
            elif op == '/':
                result = num1 / num2 if num2 != 0 else "Cannot divide by zero"
            
            return f"The answer is {result}"
        else:
            return "I couldn't understand that calculation. Please try again."
    
    def handle_knowledge_query(self, query):
        """Handle knowledge-based queries through NLWeb"""
        try:
            payload = {
                "question": query,
                "conversation_history": self.conversation_history[-5:]  # Last 5 exchanges
            }
            
            response = requests.post(
                f"{self.nlweb_url}/api/ask",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get("answer", "I couldn't find an answer to that question.")
                
                # Store conversation history
                self.conversation_history.append({
                    "question": query,
                    "answer": answer,
                    "timestamp": datetime.now().isoformat()
                })
                
                return answer
            else:
                return "I'm having trouble accessing my knowledge base right now."
                
        except Exception as e:
            return "I encountered an error while processing your request."

