
import threading
import time
from datetime import datetime

class AIAdvisor:
    """Project Overmind - AI Tactical Advisor"""
    
    def __init__(self, model="llama3.1:8b"):
        self.model = model
        self.enabled = False
        self.history = []
        
        try:
            import ollama
            self.ollama = ollama
            # Test connection
            self.ollama.list()
            self.enabled = True
        except ImportError:
            self.error = "Ollama python library not installed"
        except Exception as e:
            self.error = f"Ollama connection failed: {e}"

    def analyze_log(self, log_entry):
        """Analyze a specific log entry for tactical advice"""
        if not self.enabled:
            return None
            
        # Analyze interesting events (Errors, Disconnects, New Connections, etc)
        keywords = ["ERROR", "WARNING", "Disconnect", "Timeout", "Refused", "connected", "SUCCESS"]
        if not any(k in log_entry for k in keywords):
            return None

        prompt = f"""Act as an elite Red Team Operator and C2 Specialist.
        
        Analyze this C2 server log entry:
        "{log_entry}"
        
        Provide a SHORT, TACTICAL recommendation (max 2 sentences).
        Focus on: Evasion, Persistence, or Connectivity fixes.
        
        Format:
        [TACTICAL ADVICE] <your advice here>
        """
        
        try:
            response = self.ollama.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                options={'temperature': 0.7}
            )
            return response['message']['content'].strip()
        except Exception as e:
            return None
