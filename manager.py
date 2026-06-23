import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
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

def run_sync_command(action):
    proj_path = entry_proj.get().strip()
    sources_path = entry_sources.get().strip()
    
    # Создаем всплывающее окно вывода логов
    out_win = tk.Toplevel(root)
    out_win.title(f"Синхронизация: {action.upper()}")
    out_win.geometry("650x450")
    
    lbl_title = tk.Label(out_win, text=f"Выполнение операции: {action.upper()}", font=("Arial", 10, "bold"))
    lbl_title.pack(pady=5)
    
    txt = tk.Text(out_win, wrap="word", font=("Consolas", 10))
    txt.pack(fill="both", expand=True, padx=10, pady=5)
    txt.insert("end", f"Запуск синхронизации: {action}...\n")
    txt.insert("end", f"Проект: {proj_path}\n")
    txt.insert("end", f"Папка: {sources_path}\n\n")
    txt.see("end")
    
    def worker():
        cmd = ["node", "sync_cli.js", action, proj_path, sources_path]
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                shell=True
            )
            for line in proc.stdout:
                txt.insert("end", line)
                txt.see("end")
            proc.wait()
            if proc.returncode == 0:
                txt.insert("end", f"\n=== УСПЕШНО ЗАВЕРШЕНО ===\n")
            else:
                txt.insert("end", f"\n=== ОШИБКА (Код возврата: {proc.returncode}) ===\n")
        except Exception as ex:
            txt.insert("end", f"\nОшибка запуска: {ex}\n")
        txt.see("end")
        
    threading.Thread(target=worker, daemon=True).start()

def browse_project():
    path = filedialog.askopenfilename(
        title="Выберите файл проекта CODESYS",
        filetypes=[("CODESYS Projects", "*.project"), ("All files", "*.*")]
    )
    if not path:
        path = filedialog.askdirectory(title="Или выберите папку с проектами")
    if path:
        entry_proj.delete(0, tk.END)
        entry_proj.insert(0, os.path.normpath(path))

def browse_sources():
    path = filedialog.askdirectory(title="Выберите папку для исходников (.st)")
    if path:
        entry_sources.delete(0, tk.END)
        entry_sources.insert(0, os.path.normpath(path))

root = tk.Tk()
root.title("CODESYS MCP & Git Manager")
root.geometry("380x620") # Увеличили ширину для удобства выбора путей
root.resizable(False, False)

# Стилизация
style = ttk.Style()
style.theme_use('vista')

lbl = tk.Label(root, text="Управление сервером MCP", font=("Arial", 11, "bold"))
lbl.pack(pady=10)

btn_build = ttk.Button(root, text="1. Пересобрать (npm run build)", command=build_project)
btn_build.pack(fill='x', padx=30, pady=3, ipady=3)

btn_insp = ttk.Button(root, text="2. Запустить MCP Inspector", command=start_inspector)
btn_insp.pack(fill='x', padx=30, pady=3, ipady=3)

btn_restart = ttk.Button(root, text="3. Перезапустить сервер", command=restart_inspector)
btn_restart.pack(fill='x', padx=30, pady=3, ipady=3)

# КНОПКА ОТКРЫТИЯ В БРАУЗЕРЕ (изначально отключена)
btn_browser = ttk.Button(root, text="4. Открыть Web UI", command=open_browser, state="disabled")
btn_browser.pack(fill='x', padx=30, pady=3, ipady=3)

btn_stop = ttk.Button(root, text="5. Остановить сервер", command=stop_inspector)
btn_stop.pack(fill='x', padx=30, pady=3, ipady=3)

# --- РАЗДЕЛ СИНХРОНИЗАЦИИ GIT ---
lbl_sep = ttk.Separator(root, orient='horizontal')
lbl_sep.pack(fill='x', padx=20, pady=10)

lbl_git = tk.Label(root, text="Синхронизация Git (Ручной режим)", font=("Arial", 11, "bold"))
lbl_git.pack(pady=5)

lbl_proj = tk.Label(root, text="Путь к проекту или папке проекта:", font=("Arial", 8))
lbl_proj.pack(anchor='w', padx=30)

frame_proj = ttk.Frame(root)
frame_proj.pack(fill='x', padx=30, pady=2)
entry_proj = ttk.Entry(frame_proj)
entry_proj.insert(0, r"D:\Projects\CEX_15\апп 511\PLC")
entry_proj.pack(side='left', fill='x', expand=True)
btn_browse_proj = ttk.Button(frame_proj, text="...", width=3, command=browse_project)
btn_browse_proj.pack(side='right', padx=(5, 0))

lbl_sources = tk.Label(root, text="Папка с исходниками (.st):", font=("Arial", 8))
lbl_sources.pack(anchor='w', padx=30)

frame_sources = ttk.Frame(root)
frame_sources.pack(fill='x', padx=30, pady=2)
entry_sources = ttk.Entry(frame_sources)
entry_sources.insert(0, r"D:\Projects\CEX_15\апп 511\PLC\project_sources")
entry_sources.pack(side='left', fill='x', expand=True)
btn_browse_src = ttk.Button(frame_sources, text="...", width=3, command=browse_sources)
btn_browse_src.pack(side='right', padx=(5, 0))

frame_buttons = ttk.Frame(root)
frame_buttons.pack(fill='x', padx=30, pady=5)

btn_export = ttk.Button(frame_buttons, text="Экспорт исходников", command=lambda: run_sync_command('export'))
btn_export.pack(side='left', fill='x', expand=True, padx=(0, 2), ipady=3)
btn_import = ttk.Button(frame_buttons, text="Импорт исходников", command=lambda: run_sync_command('import'))
btn_import.pack(side='right', fill='x', expand=True, padx=(2, 0), ipady=3)
# --------------------------------

btn_close = ttk.Button(root, text="Закрыть менеджер", command=root.destroy)
btn_close.pack(fill='x', padx=30, pady=15, ipady=5)

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
