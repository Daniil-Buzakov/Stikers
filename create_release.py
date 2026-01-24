import os
import shutil
import zipfile
from datetime import datetime

def create_release_package(version):
    """Создает пакет для релиза"""
    
    # Создаем папку для релиза
    release_dir = f"release_v{version}"
    os.makedirs(release_dir, exist_ok=True)
    
    # Файлы для включения в релиз
    files_to_include = [
        'sticky_notes.py',
        'update_manager.py',
        'requirements.txt',
        'README.md',
        'icon.ico',
        'version.json'
    ]
    
    # Копируем файлы
    for file in files_to_include:
        if os.path.exists(file):
            shutil.copy2(file, os.path.join(release_dir, file))
            print(f"Скопирован: {file}")
    
    # Создаем папку dist если есть
    dist_dir = 'dist'
    if os.path.exists(dist_dir):
        for item in os.listdir(dist_dir):
            item_path = os.path.join(dist_dir, item)
            if os.path.isfile(item_path):
                shutil.copy2(item_path, os.path.join(release_dir, item))
                print(f"Скопирован из dist: {item}")
    
    # Создаем ZIP архив
    zip_name = f"sticky_notes_v{version}.zip"
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(release_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, release_dir)
                zipf.write(file_path, arcname)
    
    # Удаляем временную папку
    shutil.rmtree(release_dir)
    
    print(f"\nРелиз создан: {zip_name}")
    print(f"Размер: {os.path.getsize(zip_name) / 1024 / 1024:.2f} MB")
    
    return zip_name

if __name__ == "__main__":
    version = "1.1.0"
    create_release_package(version)