import os
import zipfile
import plistlib
import glob

INPUT_DIR = "input_ipas"
OUTPUT_DIR = "output_ipas"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def patch_ipa(ipa_path):
    filename = os.path.basename(ipa_path)
    print(f"Обработка: {filename}")
    
    extract_dir = "extracted_app"
    
    # 1. Распаковываем .ipa (это обычный zip)
    with zipfile.ZipFile(ipa_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
        
    # 2. Ищем Info.plist внутри Payload/*.app/
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
        try:
            # Читаем plist (Python сам понимает и XML, и бинарный формат)
            with open(plist_path, "rb") as f:
                plist_data = plistlib.load(f)
                
            # Меняем MinimumOSVersion на 15.0
            old_version = plist_data.get("MinimumOSVersion", "неизвестно")
            plist_data["MinimumOSVersion"] = "15.0"
            
            # Сохраняем обратно
            with open(plist_path, "wb") as f:
                plistlib.dump(plist_data, f)
                
            print(f"Успешно: MinimumOSVersion изменена с {old_version} на 15.0")
        except Exception as e:
            print(f"Ошибка при чтении/записи plist: {e}")
            
    # 3. Запаковываем обратно в .ipa
    output_path = os.path.join(OUTPUT_DIR, filename)
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zip_out:
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                full_path = os.path.join(root, file)
                # Относительный путь внутри архива должен начинаться с Payload/...
                arcname = os.path.relpath(full_path, extract_dir)
                zip_out.write(full_path, arcname)
                
    # Очищаем временную папку
    import shutil
    shutil.rmtree(extract_dir)
    print(f"Готово! Сохранено в {output_path}\n")

if __name__ == "__main__":
    ipas = glob.glob(os.path.join(INPUT_DIR, "*.ipa"))
    if notipas:
        print("В папке input_ipas нет файлов для обработки.")
    for ipa in ipas:
        patch_ipa(ipa)