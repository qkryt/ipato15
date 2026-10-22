import glob
import os
import plistlib
import re
import shutil
import zipfile
import gdown

INPUT_DIR = "input_ipas"
OUTPUT_DIR = "output_ipas"

# Ссылка на твои .ipa файлы с Google Drive
URLS_TO_DOWNLOAD = [
    "https://drive.google.com/file/d/1_HFu6kaenOSvVwq29na_v8KinVM0OrL6/view",
]

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_gdrive_download_url(url):
    """Извлекает ID из любой ссылки Google Drive и формирует прямую ссылку для скачивания."""
    file_id = None
    if '/file/d/' in url:
        parts = url.split('/file/d/')
        if len(parts) > 1:
            file_id = parts[1].split('/')[0]
    elif 'id=' in url:
        match = re.search(r'id=([a-zA-Z0-9_-]+)', url)
        if match:
            file_id = match.group(1)
            
    if file_id:
        return f'https://drive.google.com/uc?export=download&id={file_id}'
    return url

def download_file(url, target_path):
    download_url = get_gdrive_download_url(url)
    print(f"Скачивание с Google Drive: {download_url} ...")
    gdown.download(download_url, target_path, quiet=False)
    print(f"Успешно скачано: {target_path}")

def patch_ipa(ipa_path):
    filename = os.path.basename(ipa_path)
    print(f"\n--- Обработка: {filename} ---")
    
    extract_dir = "extracted_app"
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)

    try:
        # 1. Распаковываем .ipa
        with zipfile.ZipFile(ipa_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
            
        # 2. Находим Info.plist
        payload_dir = os.path.join(extract_dir, "Payload")
        if not os.path.exists(payload_dir):
            print(f"Ошибка: папка Payload не найдена в {filename}")
            return

        app_folders = os.listdir(payload_dir)
        if not app_folders:
            print(f"Ошибка: .app бандл не найден в {filename}")
            return
            
        app_path = os.path.join(payload_dir, app_folders[0])
        plist_path = os.path.join(app_path, "Info.plist")
        
        if os.path.exists(plist_path):
            with open(plist_path, "rb") as f:
                plist_data = plistlib.load(f)
                
            old_version = plist_data.get("MinimumOSVersion", "неизвестно")
            plist_data["MinimumOSVersion"] = "15.0"
            
            with open(plist_path, "wb") as f:
                plistlib.dump(plist_data, f)
                
            print(f"Успешно: MinimumOSVersion изменена с '{old_version}' на '15.0'")
                
        # 3. Запаковываем обратно в .ipa
        output_path = os.path.join(OUTPUT_DIR, filename)
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zip_out:
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    full_path = os.path.join(root, file)
                    arcname = os.path.relpath(full_path, extract_dir)
                    zip_out.write(full_path, arcname)
                    
        print(f"Готово! Сохранено в {output_path}")

    except Exception as e:
        print(f"Ошибка при обработке {filename}: {e}")
    finally:
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)

if __name__ == "__main__":
    if not URLS_TO_DOWNLOAD:
        print("Внимание: Список URLS_TO_DOWNLOAD пуст!")
    
    for i, url in enumerate(URLS_TO_DOWNLOAD):
        try:
            download_path = os.path.join(INPUT_DIR, f"app_{i+1}.ipa")
            download_file(url, download_path)
            
            downloaded_files = glob.glob(os.path.join(INPUT_DIR, "*.ipa"))
            if downloaded_files:
                latest_file = max(downloaded_files, key=os.path.getmtime)
                patch_ipa(latest_file)
        except Exception as e:
            print(f"Не удалось скачать или обработать {url}: {e}")
