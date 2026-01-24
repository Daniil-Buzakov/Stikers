import os
import sys
import winshell
from win32com.client import Dispatch
import ctypes
import winreg

def is_admin():
    """Проверяет, запущен ли скрипт от имени администратора"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def create_shortcuts():
    """Создает ярлыки"""
    try:
        # Путь к приложению
        if getattr(sys, 'frozen', False):
            app_path = sys.executable
            app_dir = os.path.dirname(app_path)
        else:
            app_path = os.path.abspath("sticky_notes.exe")
            app_dir = os.path.dirname(app_path)
        
        app_name = "Стикеры-заметки"
        
        print(f"Приложение: {app_path}")
        print(f"Папка: {app_dir}")
        
        # Создаем ярлык на рабочем столе
        try:
            desktop = winshell.desktop()
            shortcut_path = os.path.join(desktop, f"{app_name}.lnk")
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = app_path
            shortcut.WorkingDirectory = app_dir
            shortcut.IconLocation = app_path
            shortcut.Description = "Стикеры-заметки"
            shortcut.save()
            
            print(f"Ярлык на рабочем столе создан: {shortcut_path}")
        except Exception as e:
            print(f"Ошибка создания ярлыка на рабочем столе: {e}")
        
        # Создаем ярлык в меню Пуск
        try:
            start_menu = os.path.join(os.getenv('APPDATA'), 
                                     'Microsoft', 'Windows', 'Start Menu', 
                                     'Programs')
            os.makedirs(start_menu, exist_ok=True)
            
            shortcut_path = os.path.join(start_menu, f"{app_name}.lnk")
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = app_path
            shortcut.WorkingDirectory = app_dir
            shortcut.IconLocation = app_path
            shortcut.Description = "Стикеры-заметки"
            shortcut.save()
            
            print(f"Ярлык в меню Пуск создан: {shortcut_path}")
        except Exception as e:
            print(f"Ошибка создания ярлыка в меню Пуск: {e}")
        
        # Добавляем в автозагрузку (через реестр)
        try:
            if is_admin():
                key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 
                                    0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, app_name, 0, 
                                winreg.REG_SZ, app_path)
                winreg.CloseKey(key)
                print("Добавлено в автозагрузку (реестр)")
            else:
                # Через папку Startup
                startup = os.path.join(os.getenv('APPDATA'), 
                                      'Microsoft', 'Windows', 'Start Menu', 
                                      'Programs', 'Startup')
                os.makedirs(startup, exist_ok=True)
                
                shortcut_path = os.path.join(startup, f"{app_name}.lnk")
                
                shell = Dispatch('WScript.Shell')
                shortcut = shell.CreateShortCut(shortcut_path)
                shortcut.Targetpath = app_path
                shortcut.WorkingDirectory = app_dir
                shortcut.IconLocation = app_path
                shortcut.Description = "Стикеры-заметки"
                shortcut.save()
                
                print(f"Добавлено в автозагрузку (папка): {shortcut_path}")
        except Exception as e:
            print(f"Ошибка добавления в автозагрузку: {e}")
        
        print("\nГотово! Ярлыки созданы.")
        input("Нажмите Enter для выхода...")
        
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        input("Нажмите Enter для выхода...")

if __name__ == "__main__":
    print("Создание ярлыков для Стикеры-заметки...")
    create_shortcuts()
