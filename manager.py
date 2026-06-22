import tkinter as tk
from tkinter import ttk
import os
import subprocess
import threading
import re
import webbrowser

inspector_process = None
current_inspector_url = None

def build_project():
    print("Запуск сборки...")
    os.system('start cmd /c "npm run build && echo. && pause"')

def read_output(process):
    global current_inspector_url
    url_pattern = re.compile(r'(http://localhost:\d+/\?MCP_PROXY_AUTH_TOKEN=[a-zA-Z0-9]+)')
    
    while True:
        try:
            line = process.stdout.readline()
        except:
            break
            
        if not line:
            break
            
        print("INSPECTOR:", line.strip())
        
        # Ищем ссылку в логах
        match = url_pattern.search(line)
        if match:
            current_inspector_url = match.group(1)
            print(">>> НАЙДЕН URL:", current_inspector_url)
            # Обновляем текст кнопки в главном потоке GUI
            root.after(0, lambda: btn_browser.config(text="4. Открыть Web UI (Готово!)", state="normal"))
            # Можно раскомментировать строку ниже, чтобы браузер открывался сам:
            # webbrowser.open(current_inspector_url)

def start_inspector():
    global inspector_process, current_inspector_url
    print("Запуск MCP Inspector...")
    
    if inspector_process is not None and inspector_process.poll() is None:
        print("Инспектор уже запущен.")
        return
        
    current_inspector_url = None
    btn_browser.config(text="4. Открыть Web UI (Запуск...)", state="disabled")
    
    # Получаем абсолютный путь к dist/bin.js и меняем слэши на прямые,
    # чтобы они не "съедались" как спецсимволы при передаче аргументов
    bin_js_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist', 'bin.js')
    bin_js_path = bin_js_path.replace('\\', '/')
    
    # Запускаем скрытно, перехватываем вывод
    inspector_process = subprocess.Popen(
        f'npx @modelcontextprotocol/inspector node "{bin_js_path}"',
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Запускаем поток для чтения консоли, чтобы не вешать UI
    threading.Thread(target=read_output, args=(inspector_process,), daemon=True).start()

def stop_inspector():
    global inspector_process, current_inspector_url
    print("Остановка MCP Inspector...")
    if inspector_process is not None and inspector_process.poll() is None:
        subprocess.run(['taskkill', '/F', '/T', '/PID', str(inspector_process.pid)], capture_output=True)
        inspector_process = None
        current_inspector_url = None
        btn_browser.config(text="4. Открыть Web UI", state="disabled")
        print("Инспектор остановлен.")
    else:
        print("Инспектор не запущен.")

def restart_inspector():
    print("Перезапуск MCP Inspector...")
    stop_inspector()
    start_inspector()

def open_browser():
    if current_inspector_url:
        print("Открываем URL:", current_inspector_url)
        webbrowser.open(current_inspector_url)
    else:
        print("URL еще не получен.")

root = tk.Tk()
root.title("CODESYS MCP Manager")
root.geometry("320x400") # Увеличили высоту для новой кнопки
root.resizable(False, False)

# Стилизация
style = ttk.Style()
style.theme_use('vista')

lbl = tk.Label(root, text="Управление сервером MCP", font=("Arial", 12, "bold"))
lbl.pack(pady=20)

btn_build = ttk.Button(root, text="1. Пересобрать (npm run build)", command=build_project)
btn_build.pack(fill='x', padx=30, pady=5, ipady=5)

btn_insp = ttk.Button(root, text="2. Запустить MCP Inspector", command=start_inspector)
btn_insp.pack(fill='x', padx=30, pady=5, ipady=5)

btn_restart = ttk.Button(root, text="3. Перезапустить сервер", command=restart_inspector)
btn_restart.pack(fill='x', padx=30, pady=5, ipady=5)

# КНОПКА ОТКРЫТИЯ В БРАУЗЕРЕ (изначально отключена)
btn_browser = ttk.Button(root, text="4. Открыть Web UI", command=open_browser, state="disabled")
btn_browser.pack(fill='x', padx=30, pady=5, ipady=5)

btn_stop = ttk.Button(root, text="5. Остановить сервер", command=stop_inspector)
btn_stop.pack(fill='x', padx=30, pady=5, ipady=5)

btn_close = ttk.Button(root, text="Закрыть менеджер", command=root.destroy)
btn_close.pack(fill='x', padx=30, pady=5, ipady=5)

# Очистка при закрытии главного окна
def on_closing():
    global inspector_process
    if inspector_process is not None and inspector_process.poll() is None:
        subprocess.run(['taskkill', '/F', '/T', '/PID', str(inspector_process.pid)], capture_output=True)
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

# Центрируем окно по экрану
root.update_idletasks()
width = root.winfo_width()
height = root.winfo_height()
x = (root.winfo_screenwidth() // 2) - (width // 2)
y = (root.winfo_screenheight() // 2) - (height // 2)
root.geometry('{}x{}+{}+{}'.format(width, height, x, y))

root.mainloop()
