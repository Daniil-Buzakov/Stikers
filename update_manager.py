import os
import sys
import json
import shutil
import tempfile
import zipfile
import subprocess
import requests
from pathlib import Path
from PyQt5.QtWidgets import QProgressDialog, QMessageBox, QApplication
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import winshell
from win32com.client import Dispatch
import winreg

class UpdateDownloader(QThread):
    """Поток для загрузки обновлений"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, download_url):
        super().__init__()
        self.download_url = download_url
        
    def run(self):
        try:
            # Создаем временную папку
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, "update.zip")
            
            print(f"Загрузка обновления из: {self.download_url}")
            print(f"Сохранение в: {zip_path}")
            
            # Загружаем файл
            response = requests.get(self.download_url, stream=True, timeout=30)
            total_size = int(response.headers.get('content-length', 0))
            
            with open(zip_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = int((downloaded / total_size) * 100)
                            self.progress.emit(progress)
            
            print(f"Загрузка завершена. Размер: {downloaded} байт")
            self.finished.emit(zip_path)
            
        except Exception as e:
            print(f"Ошибка загрузки: {e}")
            self.error.emit(str(e))

class UpdateManager:
    """Менеджер обновлений"""
    
    def __init__(self, current_version, app_name="Стикеры-заметки"):
        self.current_version = current_version
        self.app_name = app_name
        self.update_info_url = "https://raw.githubusercontent.com/DaniiL-Buzakov/Stikers/main/version.json"
        self.releases_url = "https://api.github.com/repos/DaniiL-Buzakov/Stikers/releases/latest"
        
        # Определяем пути
        if getattr(sys, 'frozen', False):
            self.app_dir = os.path.dirname(sys.executable)
            self.is_exe = True
        else:
            self.app_dir = os.path.dirname(os.path.abspath(__file__))
            self.is_exe = False
        
        print(f"Текущая версия: {current_version}")
        print(f"Путь к приложению: {self.app_dir}")
        print(f"Это EXE: {self.is_exe}")
        
    def check_for_updates(self):
        """Проверяет наличие обновлений"""
        try:
            print("Проверка обновлений...")
            
            # Пробуем получить информацию из version.json
            try:
                response = requests.get(self.update_info_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    latest_version = data.get('version', '0.0.0')
                    download_url = data.get('download_url', '')
                    changelog = data.get('changelog', '')
                    
                    print(f"Найдена версия {latest_version} в version.json")
                    
                    if self.is_newer_version(latest_version):
                        return {
                            'version': latest_version,
                            'changelog': changelog,
                            'download_url': download_url,
                            'source': 'version.json'
                        }
            except Exception as e:
                print(f"Ошибка при проверке version.json: {e}")
            
            # Если нет прямой ссылки, проверяем GitHub Releases
            try:
                response = requests.get(self.releases_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    latest_version = data.get('tag_name', '').lstrip('v')
                    changelog = data.get('body', '')
                    
                    # Ищем asset для скачивания
                    download_url = None
                    for asset in data.get('assets', []):
                        if asset.get('name', '').endswith('.zip'):
                            download_url = asset.get('browser_download_url')
                            break
                    
                    print(f"Найдена версия {latest_version} на GitHub")
                    
                    if download_url and self.is_newer_version(latest_version):
                        return {
                            'version': latest_version,
                            'changelog': changelog,
                            'download_url': download_url,
                            'source': 'github'
                        }
            except Exception as e:
                print(f"Ошибка при проверке GitHub Releases: {e}")
            
            return None
            
        except Exception as e:
            print(f"Ошибка проверки обновлений: {e}")
            return None
    
    def is_newer_version(self, new_version):
        """Сравнивает версии"""
        try:
            from packaging import version
            return version.parse(new_version) > version.parse(self.current_version)
        except:
            # Простое сравнение строк
            return new_version > self.current_version
    
    def download_and_install(self, download_url):
        """Скачивает и устанавливает обновление"""
        try:
            # Создаем диалог прогресса
            progress_dialog = QProgressDialog("Загрузка обновления...", "Отмена", 0, 100)
            progress_dialog.setWindowTitle("Обновление")
            progress_dialog.setWindowModality(Qt.WindowModal)
            progress_dialog.setMinimumDuration(0)
            progress_dialog.show()
            
            # Создаем поток загрузки
            self.downloader = UpdateDownloader(download_url)
            self.downloader.progress.connect(progress_dialog.setValue)
            self.downloader.finished.connect(lambda path: self.on_download_finished(path, progress_dialog))
            self.downloader.error.connect(lambda err: self.on_download_error(err, progress_dialog))
            self.downloader.start()
            
        except Exception as e:
            QMessageBox.critical(None, "Ошибка", f"Ошибка начала обновления: {str(e)}")
    
    def on_download_finished(self, zip_path, progress_dialog):
        """Обработчик завершения загрузки"""
        progress_dialog.close()
        try:
            self.install_update(zip_path)
        except Exception as e:
            QMessageBox.critical(None, "Ошибка", f"Ошибка установки: {str(e)}")
    
    def on_download_error(self, error_msg, progress_dialog):
        """Обработчик ошибки загрузки"""
        progress_dialog.close()
        QMessageBox.critical(None, "Ошибка", f"Ошибка загрузки: {error_msg}")
    
    def install_update(self, zip_path):
        """Устанавливает обновление из ZIP-файла"""
        try:
            # Создаем временную папку для распаковки
            temp_extract_dir = tempfile.mkdtemp()
            print(f"Распаковка в: {temp_extract_dir}")
            
            # Распаковываем архив
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_extract_dir)
            
            print("Архив распакован")
            
            # Определяем, что распаковалось
            extracted_items = os.listdir(temp_extract_dir)
            print(f"Распакованные файлы: {extracted_items}")
            
            # Ищем папку с обновлением (может быть вложенной)
            update_dir = None
            for item in extracted_items:
                item_path = os.path.join(temp_extract_dir, item)
                if os.path.isdir(item_path):
                    # Проверяем, есть ли в папке нужные файлы
                    files = os.listdir(item_path)
                    if 'sticky_notes.exe' in files or 'sticky_notes.py' in files:
                        update_dir = item_path
                        break
            
            # Если не нашли вложенную папку, используем корень
            if update_dir is None:
                update_dir = temp_extract_dir
            
            print(f"Папка обновления: {update_dir}")
            
            # Создаем скрипт обновления
            update_script = self.create_update_script(update_dir)
            
            # Запускаем скрипт обновления
            self.run_update_script(update_script, update_dir)
            
        except Exception as e:
            print(f"Ошибка установки: {e}")
            raise
    
    def create_update_script(self, update_dir):
        """Создает скрипт для обновления"""
        script_content = f"""
import os
import sys
import shutil
import time
import subprocess
import winshell
from win32com.client import Dispatch
import winreg

# Ждем завершения основного процесса
time.sleep(2)

app_dir = r"{self.app_dir}"
update_dir = r"{update_dir}"

print("Начало обновления...")
print(f"Папка приложения: {{app_dir}}")
print(f"Папка обновления: {{update_dir}}")

try:
    # Копируем все файлы из обновления
    for root, dirs, files in os.walk(update_dir):
        for file in files:
            src_path = os.path.join(root, file)
            rel_path = os.path.relpath(src_path, update_dir)
            dst_path = os.path.join(app_dir, rel_path)
            
            # Создаем директории если нужно
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            
            # Копируем файл
            shutil.copy2(src_path, dst_path)
            print(f"Скопирован: {{rel_path}}")
    
    print("Обновление файлов завершено")
    
    # Обновляем ярлыки
    try:
        exe_path = os.path.join(app_dir, "sticky_notes.exe")
        if os.path.exists(exe_path):
            # Ярлык на рабочем столе
            desktop = winshell.desktop()
            desktop_shortcut = os.path.join(desktop, "Стикеры-заметки.lnk")
            if os.path.exists(desktop_shortcut):
                shell = Dispatch('WScript.Shell')
                shortcut = shell.CreateShortCut(desktop_shortcut)
                shortcut.Targetpath = exe_path
                shortcut.WorkingDirectory = app_dir
                shortcut.IconLocation = exe_path
                shortcut.save()
            
            # Ярлык в меню Пуск
            start_menu = os.path.join(os.getenv('APPDATA'), 
                                     'Microsoft', 'Windows', 'Start Menu', 'Programs')
            start_menu_shortcut = os.path.join(start_menu, "Стикеры-заметки.lnk")
            if os.path.exists(start_menu_shortcut):
                shell = Dispatch('WScript.Shell')
                shortcut = shell.CreateShortCut(start_menu_shortcut)
                shortcut.Targetpath = exe_path
                shortcut.WorkingDirectory = app_dir
                shortcut.IconLocation = exe_path
                shortcut.save()
            
            # Автозагрузка
            startup = os.path.join(os.getenv('APPDATA'), 
                                  'Microsoft', 'Windows', 'Start Menu', 
                                  'Programs', 'Startup')
            startup_shortcut = os.path.join(startup, "Стикеры-заметки.lnk")
            if os.path.exists(startup_shortcut):
                shell = Dispatch('WScript.Shell')
                shortcut = shell.CreateShortCut(startup_shortcut)
                shortcut.Targetpath = exe_path
                shortcut.WorkingDirectory = app_dir
                shortcut.IconLocation = exe_path
                shortcut.save()
            
            # Реестр для автозапуска
            try:
                key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 
                                    0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, "StickyNotes", 0, 
                                winreg.REG_SZ, exe_path)
                winreg.CloseKey(key)
            except:
                pass
    except Exception as e:
        print(f"Ошибка обновления ярлыков: {{e}}")
    
    # Запускаем обновленное приложение
    time.sleep(1)
    subprocess.Popen([exe_path])
    
except Exception as e:
    print(f"Критическая ошибка обновления: {{e}}")
    input("Нажмите Enter для выхода...")

# Удаляем временные файлы
try:
    import tempfile
    temp_dir = os.path.dirname(r"{update_dir}")
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)
except:
    pass
"""
        
        # Сохраняем скрипт
        script_path = os.path.join(self.app_dir, "update_script.py")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script_content)
        
        return script_path
    
    def run_update_script(self, script_path, update_dir):
        """Запускает скрипт обновления"""
        try:
            # Создаем BAT файл для запуска скрипта обновления
            bat_content = f"""
@echo off
echo Обновление Стикеры-заметки...
timeout /t 2 /nobreak >nul

REM Закрываем основное приложение
taskkill /f /im sticky_notes.exe >nul 2>&1
taskkill /f /im python.exe >nul 2>&1

REM Запускаем скрипт обновления
python "{script_path}"

REM Удаляем временные файлы
del "{script_path}" >nul 2>&1
del "%~f0" >nul 2>&1
"""
            
            bat_path = os.path.join(self.app_dir, "update.bat")
            with open(bat_path, "w", encoding="utf-8") as f:
                f.write(bat_content)
            
            # Запускаем BAT файл
            subprocess.Popen(['cmd', '/c', bat_path], 
                           shell=True, 
                           creationflags=subprocess.CREATE_NEW_CONSOLE)
            
            # Закрываем текущее приложение
            QApplication.quit()
            
        except Exception as e:
            print(f"Ошибка запуска скрипта обновления: {e}")
            raise