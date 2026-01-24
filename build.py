import os
import sys
import json
import subprocess
import shutil
import zipfile
from datetime import datetime

def create_exe():
    """Создает EXE файл с помощью PyInstaller"""
    
    print("Создание EXE файла...")
    
    # Команда для PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",  # Один файл
        "--windowed",  # Без консоли
        "--icon=icon.ico",  # Иконка
        "--name=Stickers",  # Имя приложения
        "--add-data=icon.ico;.",  # Добавляем иконку
        "--add-data=version.json;.",  # Добавляем файл версии
        "--hidden-import=PyQt5",  # Явно импортируем PyQt5
        "--hidden-import=PyQt5.QtCore",
        "--hidden-import=PyQt5.QtGui",
        "--hidden-import=PyQt5.QtWidgets",
        "--hidden-import=requests",
        "--hidden-import=packaging",
        "--hidden-import=packaging.version",
        "--hidden-import=packaging.specifiers",
        "--hidden-import=packaging.requirements",
        "--hidden-import=win32com",
        "--hidden-import=win32com.client",
        "--collect-all=winshell",
        "sticky_notes.py"
    ]
    
    try:
        # Запускаем PyInstaller
        subprocess.run(cmd, check=True)
        print("EXE файл создан успешно!")
        
        # Проверяем результат
        dist_dir = "dist"
        if os.path.exists(dist_dir):
            exe_files = [f for f in os.listdir(dist_dir) if f.endswith('.exe')]
            if exe_files:
                print(f"Созданный файл: {os.path.join(dist_dir, exe_files[0])}")
                return os.path.join(dist_dir, exe_files[0])
        
        return None
        
    except subprocess.CalledProcessError as e:
        print(f"Ошибка создания EXE: {e}")
        return None
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        return None

def create_shortcut_script():
    """Создает скрипт для создания ярлыков"""
    
    script = '''import os
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
        
        print("\\nГотово! Ярлыки созданы.")
        input("Нажмите Enter для выхода...")
        
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        input("Нажмите Enter для выхода...")

if __name__ == "__main__":
    print("Создание ярлыков для Стикеры-заметки...")
    create_shortcuts()
'''
    
    with open("create_shortcuts.py", "w", encoding="utf-8") as f:
        f.write(script)
    
    print("Скрипт для создания ярлыков создан: create_shortcuts.py")
    
    # Создаем BAT файл для удобства
    bat_content = '''@echo off
echo Создание ярлыков для Стикеры-заметки...
python create_shortcuts.py
pause
'''
    
    with open("create_shortcuts.bat", "w", encoding="utf-8") as f:
        f.write(bat_content)
    
    print("BAT файл создан: create_shortcuts.bat")

def create_installer():
    """Создает установщик"""
    
    print("\nСоздание установщика...")
    
    # Создаем папку для установщика
    installer_dir = "Installer"
    os.makedirs(installer_dir, exist_ok=True)
    
    # Копируем EXE файл
    dist_dir = "dist"
    if os.path.exists(dist_dir):
        for file in os.listdir(dist_dir):
            if file.endswith('.exe'):
                src = os.path.join(dist_dir, file)
                dst = os.path.join(installer_dir, file)
                shutil.copy2(src, dst)
                print(f"Скопирован EXE: {file}")
    
    # Копируем дополнительные файлы
    files_to_copy = [
        "icon.ico",
        "version.json",
        "create_shortcuts.py",
        "create_shortcuts.bat",
        "README.md"
    ]
    
    for file in files_to_copy:
        if os.path.exists(file):
            shutil.copy2(file, os.path.join(installer_dir, file))
            print(f"Скопирован: {file}")
    
    # Создаем README для установки
    readme_install = '''# Установка Стикеры-заметки

     ## Простая установка:

      1. Запустите файл `create_shortcuts.bat`
      2. Нажмите Enter при появлении запроса

     ## Ручная установка:

     1. Запустите `Стикеры-заметки.exe`
     2. Для создания ярлыков запустите:
     python create_shortcuts.py

     ## Функции:

     - Автоматическое обновление
     - Создание заметок на рабочем столе
     - Работа из системного трея
     - Автосохранение

     Приложение будет добавлено в автозагрузку автоматически.
      '''
 
    with open(os.path.join(installer_dir, "УСТАНОВКА.txt"), "w", encoding="utf-8") as f:
     f.write(readme_install)
 
     # Создаем ZIP архив установщика
     version = get_version()
     zip_name = f"Sticky_Notes_Setup_v{version}.zip"
 
     with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
         for root, dirs, files in os.walk(installer_dir):
          for file in files:
             file_path = os.path.join(root, file)
             arcname = os.path.relpath(file_path, installer_dir)
             zipf.write(file_path, arcname)
 
         print(f"\nУстановщик создан: {zip_name}")
         print(f"Размер: {os.path.getsize(zip_name) / 1024 / 1024:.2f} MB")
 
      # Удаляем временную папку
    shutil.rmtree(installer_dir, ignore_errors=True)
 
    return zip_name

def get_version():
 """Получает версию из version.json"""
 try:
     import json
     with open("version.json", "r", encoding="utf-8") as f:
         data = json.load(f)
         return data.get("version", "1.0.0")
 except:
     return "1.0.0"

def clean_build():
 """Очищает временные файлы сборки"""
 print("\nОчистка временных файлов...")
 
 dirs_to_remove = ["build", "__pycache__"]
 files_to_remove = ["Стикеры-заметки.spec"]
 
 for dir_name in dirs_to_remove:
     if os.path.exists(dir_name):
         shutil.rmtree(dir_name, ignore_errors=True)
         print(f"Удалена папка: {dir_name}")
 
 for file_name in files_to_remove:
     if os.path.exists(file_name):
         os.remove(file_name)
         print(f"Удален файл: {file_name}")

def main():
 """Основная функция сборки"""
 print("=" * 50)
 print("Сборка Стикеры-заметки")
 print("=" * 50)
 
 # Проверяем зависимости
 try:
     import PyInstaller
     print("PyInstaller найден")
 except ImportError:
     print("Установите PyInstaller: pip install pyinstaller")
     return
 
 # Создаем EXE
 exe_path = create_exe()
 if not exe_path:
     print("Ошибка! EXE файл не создан.")
     return
 
 # Создаем скрипт для ярлыков
 create_shortcut_script()
 
 # Создаем установщик
 installer = create_installer()
 
 # Очищаем временные файлы
 clean_build()
 
 print("\n" + "=" * 50)
 print("Сборка завершена успешно!")
 print(f"EXE файл: dist\\Стикеры-заметки.exe")
 print(f"Установщик: {installer}")
 print("=" * 50)
 
 # Создаем файл для GitHub Releases
 create_github_release_file(installer)

def create_github_release_file(installer_zip):
 """Создает файл для загрузки на GitHub"""
 version = get_version()
 
 release_info = {
     "version": version,
     "release_date": datetime.now().strftime("%Y-%m-%d"),
     "files": [
         {
             "name": installer_zip,
             "size": os.path.getsize(installer_zip),
             "description": "Полный установщик"
         }
     ],
     "changelog": "• Автоматическое обновление\n• Улучшенный интерфейс\n• Быстрый запуск\n• Исправлены ошибки"
 }
 
 with open("release_info.json", "w", encoding="utf-8") as f:
     json.dump(release_info, f, indent=2, ensure_ascii=False)
 
 print(f"\nИнформация для релиза сохранена в: release_info.json")

if __name__ == "__main__":
 main()