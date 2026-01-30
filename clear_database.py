# clear_database.py
# Запусти этот файл, чтобы очистить все данные в таблице (кроме заголовков)

import gspread
from google.oauth2.service_account import Credentials

# Те же SCOPE и credentials, что в sheets.py
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive",
]

creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPE)
client = gspread.authorize(creds)

SHEET_NAME = "marketplace"  # ← твое название таблицы
sheet = client.open(SHEET_NAME)

# Вкладки, которые будем очищать
worksheets = [
    sheet.worksheet("Users"),
    sheet.worksheet("Products"),
    sheet.worksheet("Orders"),
]

print("Очистка базы данных...")
print("Это действие НЕЛЬЗЯ отменить!")
confirm = input("Введи 'YES' чтобы продолжить: ").strip().upper()

if confirm != "YES":
    print("Очистка отменена.")
    exit()

for ws in worksheets:
    try:
        # Получаем количество строк (кроме заголовка)
        num_rows = ws.row_count
        if num_rows > 1:
            # Удаляем все строки начиная со второй
            ws.delete_rows(2, num_rows)
            print(f"Очищена вкладка: {ws.title} ({num_rows - 1} строк удалено)")
        else:
            print(f"Вкладка {ws.title} уже пуста (только заголовки)")
    except Exception as e:
        print(f"Ошибка при очистке {ws.title}: {e}")

print("\nОчистка завершена!")
print("Теперь все вкладки пустые (кроме заголовков).")