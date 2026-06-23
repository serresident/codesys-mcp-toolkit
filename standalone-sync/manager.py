import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import os
import subprocess
import threading

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
root.title("CODESYS Git Sync Manager")
root.geometry("380x320") # Компактный размер для ручной синхронизации
root.resizable(False, False)

# Стилизация
style = ttk.Style()
style.theme_use('vista')

lbl_git = tk.Label(root, text="Синхронизация Git (Ручной режим)", font=("Arial", 11, "bold"))
lbl_git.pack(pady=15)

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
frame_buttons.pack(fill='x', padx=30, pady=15)

btn_export = ttk.Button(frame_buttons, text="Экспорт исходников", command=lambda: run_sync_command('export'))
btn_export.pack(side='left', fill='x', expand=True, padx=(0, 2), ipady=3)
btn_import = ttk.Button(frame_buttons, text="Импорт исходников", command=lambda: run_sync_command('import'))
btn_import.pack(side='right', fill='x', expand=True, padx=(2, 0), ipady=3)

btn_close = ttk.Button(root, text="Закрыть менеджер", command=root.destroy)
btn_close.pack(fill='x', padx=30, pady=10, ipady=3)

# Центрируем окно по экрану
root.update_idletasks()
width = root.winfo_width()
height = root.winfo_height()
x = (root.winfo_screenwidth() // 2) - (width // 2)
y = (root.winfo_screenheight() // 2) - (height // 2)
root.geometry('{}x{}+{}+{}'.format(width, height, x, y))

root.mainloop()
