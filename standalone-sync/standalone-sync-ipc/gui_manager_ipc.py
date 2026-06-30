import sys
import os
import json
import subprocess
import tempfile
import time

try:
    from PyQt6 import QtCore, QtGui, QtWidgets
    from PyQt6.QtCore import pyqtSignal as Signal, pyqtSlot as Slot
except ImportError:
    from PyQt5 import QtCore, QtGui, QtWidgets
    from PyQt5.QtCore import pyqtSignal as Signal, pyqtSlot as Slot

temp_dir = tempfile.gettempdir()
req_path = os.path.join(temp_dir, "codesys_ipc_req.json")
res_path = os.path.join(temp_dir, "codesys_ipc_res.json")
log_path = os.path.join(temp_dir, "codesys_ipc.log")

# --- QSS Dark Theme Stylesheet ---
DARK_THEME = """
QMainWindow {
    background-color: #121214;
}

QWidget {
    color: #e3e3e6;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
}

QTabWidget::pane {
    border: 1px solid #2d2d34;
    background-color: #18181b;
    border-radius: 6px;
}

QTabBar::tab {
    background-color: #1f1f23;
    border: 1px solid #2d2d34;
    border-bottom: none;
    padding: 8px 16px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
    color: #a1a1aa;
}

QTabBar::tab:hover {
    background-color: #27272a;
    color: #f4f4f5;
}

QTabBar::tab:selected {
    background-color: #18181b;
    border-color: #2d2d34;
    border-bottom: 2px solid #00f0ff;
    color: #00f0ff;
    font-weight: bold;
}

QGroupBox {
    border: 1px solid #2d2d34;
    border-radius: 8px;
    margin-top: 12px;
    font-weight: bold;
    color: #00f0ff;
    padding: 10px;
    background-color: #18181b;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 5px;
    background-color: #121214;
}

QLineEdit {
    background-color: #27272a;
    border: 1px solid #3f3f46;
    border-radius: 4px;
    padding: 6px;
    color: #f4f4f5;
}

QLineEdit:focus {
    border: 1px solid #00f0ff;
}

QPushButton {
    background-color: #2563eb;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    font-weight: bold;
    color: white;
}

QPushButton:hover {
    background-color: #3b82f6;
}

QPushButton:pressed {
    background-color: #1d4ed8;
}

QPushButton:disabled {
    background-color: #3f3f46;
    color: #a1a1aa;
}

QPushButton#btn_browse {
    background-color: #3f3f46;
    color: #f4f4f5;
}

QPushButton#btn_browse:hover {
    background-color: #52525b;
}

QPushButton#btn_action_sync {
    background-color: #0d9488;
}

QPushButton#btn_action_sync:hover {
    background-color: #14b8a6;
}

QPushButton#btn_action_compile {
    background-color: #7c3aed;
}

QPushButton#btn_action_compile:hover {
    background-color: #8b5cf6;
}

QPushButton#btn_git_commit {
    background-color: #10b981;
}

QPushButton#btn_git_commit:hover {
    background-color: #34d399;
}

QListWidget {
    background-color: #18181b;
    border: 1px solid #2d2d34;
    border-radius: 6px;
    padding: 5px;
    color: #e3e3e6;
}

QListWidget::item {
    padding: 6px;
    border-bottom: 1px solid #27272a;
}

QListWidget::item:hover {
    background-color: #27272a;
    border-radius: 4px;
}

QListWidget::item:selected {
    background-color: #3b82f6;
    color: white;
    border-radius: 4px;
}

QTextEdit, QTextBrowser {
    background-color: #09090b;
    border: 1px solid #2d2d34;
    border-radius: 6px;
    color: #e3e3e6;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 12px;
}

QScrollBar:vertical {
    border: none;
    background: #18181b;
    width: 10px;
    margin: 0px 0px 0px 0px;
}

QScrollBar::handle:vertical {
    background: #3f3f46;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #52525b;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CODESYS Sync & Git Manager (IPC Mode)")
        self.resize(1100, 750)
        self.setStyleSheet(DARK_THEME)

        self.config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui_ipc_config.json")
        self.log_offset = 0
        
        self.poll_timer = QtCore.QTimer()
        self.poll_timer.timeout.connect(self.poll_ipc)

        self.status_timer = QtCore.QTimer()
        self.status_timer.timeout.connect(self.check_environment_status)
        self.status_timer.start(2000)
        self.waiting_for_ping = False

        self.init_ui()
        self.load_config()
        self.refresh_git_status()

    def init_ui(self):
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QtWidgets.QHBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # --- Sidebar / Left Panel ---
        sidebar = QtWidgets.QWidget()
        sidebar.setFixedWidth(340)
        sidebar_layout = QtWidgets.QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(12)

        grp_paths = QtWidgets.QGroupBox("Пути и настройки")
        paths_layout = QtWidgets.QVBoxLayout(grp_paths)
        paths_layout.setSpacing(8)

        paths_layout.addWidget(QtWidgets.QLabel("CODESYS Project Folder or File:"))
        lay_proj = QtWidgets.QHBoxLayout()
        self.txt_project_path = QtWidgets.QLineEdit()
        btn_browse_proj = QtWidgets.QPushButton("...")
        btn_browse_proj.setObjectName("btn_browse")
        btn_browse_proj.setFixedWidth(35)
        btn_browse_proj.clicked.connect(self.browse_project_file)
        lay_proj.addWidget(self.txt_project_path)
        lay_proj.addWidget(btn_browse_proj)
        paths_layout.addLayout(lay_proj)

        paths_layout.addWidget(QtWidgets.QLabel("Structured Text (.st) Sources Directory:"))
        lay_src = QtWidgets.QHBoxLayout()
        self.txt_sources_path = QtWidgets.QLineEdit()
        btn_browse_src = QtWidgets.QPushButton("...")
        btn_browse_src.setObjectName("btn_browse")
        btn_browse_src.setFixedWidth(35)
        btn_browse_src.clicked.connect(self.browse_sources_dir)
        lay_src.addWidget(self.txt_sources_path)
        lay_src.addWidget(btn_browse_src)
        paths_layout.addLayout(lay_src)

        self.btn_open_src = QtWidgets.QPushButton("📂 Открыть папку ST в Проводнике")
        self.btn_open_src.setObjectName("btn_browse")
        self.btn_open_src.clicked.connect(self.open_sources_dir)
        paths_layout.addWidget(self.btn_open_src)

        self.btn_open_ide = QtWidgets.QPushButton("💻 Открыть папку ST в Antigravity IDE")
        self.btn_open_ide.setObjectName("btn_browse")
        self.btn_open_ide.clicked.connect(self.open_sources_ide)
        paths_layout.addWidget(self.btn_open_ide)

        sidebar_layout.addWidget(grp_paths)

        # --- Status Group ---
        grp_status = QtWidgets.QGroupBox("Статус окружения")
        status_layout = QtWidgets.QVBoxLayout(grp_status)
        status_layout.setSpacing(8)

        self.lbl_ide_status = QtWidgets.QLabel("Abak.IDE: Проверка...")
        self.lbl_proj_status = QtWidgets.QLabel("Проект: Проверка...")
        self.lbl_script_status = QtWidgets.QLabel("Скрипт IPC: Проверка...")
        
        status_layout.addWidget(self.lbl_ide_status)
        status_layout.addWidget(self.lbl_proj_status)
        status_layout.addWidget(self.lbl_script_status)

        self.btn_launch_ide = QtWidgets.QPushButton("💻 Открыть проект в Abak.IDE")
        self.btn_launch_ide.setObjectName("btn_browse")
        self.btn_launch_ide.clicked.connect(self.launch_ide_only)
        status_layout.addWidget(self.btn_launch_ide)

        self.btn_run_script = QtWidgets.QPushButton("▶ Запустить скрипт IPC")
        self.btn_run_script.setObjectName("btn_browse")
        self.btn_run_script.clicked.connect(self.run_script_only)
        status_layout.addWidget(self.btn_run_script)

        sidebar_layout.addWidget(grp_status)

        grp_actions = QtWidgets.QGroupBox("Синхронизация через IPC")
        actions_layout = QtWidgets.QVBoxLayout(grp_actions)
        actions_layout.setSpacing(10)

        # Info tip
        lbl_info = QtWidgets.QLabel("Запустите скрипт ipc_listener.py в среде Abak.IDE перед отправкой команд.")
        lbl_info.setWordWrap(True)
        lbl_info.setStyleSheet("color:#a1a1aa; font-style: italic;")
        actions_layout.addWidget(lbl_info)

        self.chk_add_context = QtWidgets.QCheckBox("Добавить сервер и контекст (.context)")
        self.chk_add_context.setChecked(True)
        self.chk_add_context.setStyleSheet("font-weight: normal; color: #e3e3e6;")
        actions_layout.addWidget(self.chk_add_context)

        self.btn_export = QtWidgets.QPushButton("⬇ Быстрый экспорт исходников")
        self.btn_export.setObjectName("btn_action_sync")
        self.btn_export.clicked.connect(lambda: self.run_ipc_action("export"))
        actions_layout.addWidget(self.btn_export)

        self.btn_import = QtWidgets.QPushButton("⬆ Мгновенный импорт в среду")
        self.btn_import.setObjectName("btn_action_sync")
        self.btn_import.clicked.connect(lambda: self.run_ipc_action("import"))
        actions_layout.addWidget(self.btn_import)

        self.btn_compile = QtWidgets.QPushButton("🔨 Тест компиляции в IDE")
        self.btn_compile.setObjectName("btn_action_compile")
        self.btn_compile.clicked.connect(lambda: self.run_ipc_action("compile"))
        actions_layout.addWidget(self.btn_compile)

        sidebar_layout.addWidget(grp_actions)
        sidebar_layout.addStretch()

        main_layout.addWidget(sidebar)

        # --- Right Panel (Tabs) ---
        self.tabs = QtWidgets.QTabWidget()
        main_layout.addWidget(self.tabs)

        # Tab 1: Logs Console
        self.tab_logs = QtWidgets.QWidget()
        lay_tab_logs = QtWidgets.QVBoxLayout(self.tab_logs)
        lay_tab_logs.setContentsMargins(10, 10, 10, 10)
        
        self.txt_console = QtWidgets.QTextBrowser()
        self.txt_console.setOpenExternalLinks(True)
        lay_tab_logs.addWidget(self.txt_console)

        lay_console_ctrl = QtWidgets.QHBoxLayout()
        btn_clear_console = QtWidgets.QPushButton("Очистить лог")
        btn_clear_console.setFixedWidth(120)
        btn_clear_console.clicked.connect(self.txt_console.clear)
        lay_console_ctrl.addWidget(btn_clear_console)
        lay_console_ctrl.addStretch()
        lay_tab_logs.addLayout(lay_console_ctrl)

        self.tabs.addTab(self.tab_logs, "📟 Лог IPC")

        # Tab 2: Git Control
        self.tab_git = QtWidgets.QWidget()
        lay_tab_git = QtWidgets.QVBoxLayout(self.tab_git)
        lay_tab_git.setContentsMargins(10, 10, 10, 10)

        git_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        lay_tab_git.addWidget(git_splitter)

        git_left_panel = QtWidgets.QWidget()
        lay_git_left = QtWidgets.QVBoxLayout(git_left_panel)
        lay_git_left.setContentsMargins(0, 0, 0, 0)
        
        lay_git_left.addWidget(QtWidgets.QLabel("Измененные файлы (Git Status):"))
        self.lst_git_changes = QtWidgets.QListWidget()
        self.lst_git_changes.itemSelectionChanged.connect(self.show_selected_diff)
        lay_git_left.addWidget(self.lst_git_changes)

        lay_commit = QtWidgets.QVBoxLayout()
        lay_commit.setSpacing(6)
        lay_commit.addWidget(QtWidgets.QLabel("Сообщение коммита:"))
        self.txt_commit_msg = QtWidgets.QLineEdit()
        self.txt_commit_msg.setPlaceholderText("Например: Добавлен блок IPC...")
        lay_commit.addWidget(self.txt_commit_msg)

        lay_git_btns = QtWidgets.QHBoxLayout()
        self.btn_git_commit = QtWidgets.QPushButton("Зафиксировать (Commit)")
        self.btn_git_commit.setObjectName("btn_git_commit")
        self.btn_git_commit.clicked.connect(self.run_git_commit)
        
        self.btn_git_refresh = QtWidgets.QPushButton("🔄 Обновить")
        self.btn_git_refresh.setFixedWidth(90)
        self.btn_git_refresh.clicked.connect(self.refresh_git_status)

        lay_git_btns.addWidget(self.btn_git_commit)
        lay_git_btns.addWidget(self.btn_git_refresh)
        lay_commit.addLayout(lay_git_btns)

        lay_push_pull = QtWidgets.QHBoxLayout()
        self.btn_git_push = QtWidgets.QPushButton("🚀 Отправить в ветку (Push)")
        self.btn_git_push.clicked.connect(self.run_git_push)
        self.btn_git_pull = QtWidgets.QPushButton("📥 Стянуть изменения (Pull)")
        self.btn_git_pull.clicked.connect(self.run_git_pull)
        lay_push_pull.addWidget(self.btn_git_pull)
        lay_push_pull.addWidget(self.btn_git_push)
        lay_commit.addLayout(lay_push_pull)

        lay_git_left.addLayout(lay_commit)
        git_splitter.addWidget(git_left_panel)

        git_right_panel = QtWidgets.QWidget()
        lay_git_right = QtWidgets.QVBoxLayout(git_right_panel)
        lay_git_right.setContentsMargins(0, 0, 0, 0)
        lay_git_right.addWidget(QtWidgets.QLabel("Просмотр изменений (Diff):"))
        self.txt_diff = QtWidgets.QTextBrowser()
        lay_git_right.addWidget(self.txt_diff)
        git_splitter.addWidget(git_right_panel)

        git_splitter.setStretchFactor(0, 2)
        git_splitter.setStretchFactor(1, 3)

        self.tabs.addTab(self.tab_git, "🌿 Git Версионирование")

        # Tab 3: Help Section
        self.tab_help = QtWidgets.QWidget()
        lay_tab_help = QtWidgets.QVBoxLayout(self.tab_help)
        lay_tab_help.setContentsMargins(10, 10, 10, 10)
        self.txt_help = QtWidgets.QTextBrowser()
        self.txt_help.setOpenExternalLinks(True)
        lay_tab_help.addWidget(self.txt_help)
        self.tabs.addTab(self.tab_help, "❓ Справка IPC")
        self.load_help_content()

    # --- Config Management ---
    def load_config(self):
        default_proj = 'D:\\Projects\\CEX_15\\апп 511\\PLC'
        default_src = 'D:\\Projects\\CEX_15\\апп 511\\PLC\\project_sources'
        
        # Relative path fallback
        curr_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        local_st_sources = os.path.join(curr_dir, "sources_st", "511_05")
        if os.path.exists(local_st_sources):
            default_src = local_st_sources

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.txt_project_path.setText(data.get("project_path", default_proj))
                    self.txt_sources_path.setText(data.get("sources_path", default_src))
                    self.chk_add_context.setChecked(data.get("add_context", True))
                    return
            except:
                pass

        self.txt_project_path.setText(default_proj)
        self.txt_sources_path.setText(default_src)
        self.chk_add_context.setChecked(True)

    def save_config(self):
        data = {
            "project_path": self.txt_project_path.text(),
            "sources_path": self.txt_sources_path.text(),
            "add_context": self.chk_add_context.isChecked()
        }
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self.write_log(f"<span style='color:#ef4444;'>[ERROR] Failed to save config: {e}</span>")

    # --- Path Dialogs ---
    def browse_project_file(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Выберите файл проекта CODESYS", "", "CODESYS Projects (*.project);;All Files (*)"
        )
        if not file_path:
            file_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Или выберите папку проекта")
        if file_path:
            self.txt_project_path.setText(os.path.normpath(file_path))
            self.save_config()

    def browse_sources_dir(self):
        dir_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Выберите папку с исходниками Structured Text (.st)")
        if dir_path:
            self.txt_sources_path.setText(os.path.normpath(dir_path))
            self.save_config()
            self.refresh_git_status()

    def open_sources_dir(self):
        dir_path = self.txt_sources_path.text().strip()
        if os.path.exists(dir_path):
            try:
                os.startfile(dir_path)
            except Exception as e:
                self.write_log(f"<span style='color:#ef4444;'>Не удалось открыть папку: {e}</span>")
        else:
            QtWidgets.QMessageBox.warning(self, "Предупреждение", "Указанная папка ST не существует!")

    def open_sources_ide(self):
        dir_path = self.txt_sources_path.text().strip()
        if os.path.exists(dir_path):
            try:
                import subprocess
                user_home = os.path.expanduser("~")
                antigravity_path = os.path.join(user_home, "AppData", "Local", "Programs", "Antigravity IDE", "Antigravity IDE.exe")
                if os.path.exists(antigravity_path):
                    subprocess.Popen(f'start "" "{antigravity_path}" "{dir_path}"', shell=True)
                else:
                    subprocess.Popen(f'start "" code "{dir_path}"', shell=True)
            except Exception as e:
                self.write_log(f"<span style='color:#ef4444;'>Не удалось открыть в IDE: {e}</span>")
        else:
            QtWidgets.QMessageBox.warning(self, "Предупреждение", "Указанная папка ST не существует!")

    # --- Log Display Helpers ---
    def write_log(self, text):
        import re
        formatted_line = text
        if "SCRIPT_SUCCESS" in text or "УСПЕШНО" in text or "completed successfully" in text:
            formatted_line = f"<span style='color:#10b981; font-weight:bold;'>{text}</span>"
        elif "SCRIPT_ERROR" in text or "ERROR" in text or "failed" in text or "Exception" in text or "ОШИБКА" in text:
            formatted_line = f"<span style='color:#ef4444; font-weight:bold;'>{text}</span>"
        elif "WARN" in text or "WARNING" in text:
            formatted_line = f"<span style='color:#f59e0b;'>{text}</span>"
        elif "DEBUG" in text:
            formatted_line = f"<span style='color:#06b6d4;'>{text}</span>"
        
        # Find file:/// URIs and wrap them in HTML anchor tags for clickability
        formatted_line = re.sub(
            r'(file:///[^\s<>\'\"]+)',
            r'<a href="\1" style="color:#00f0ff; text-decoration:underline;">\1</a>',
            formatted_line
        )
        
        self.txt_console.append(formatted_line)
        self.txt_console.moveCursor(QtGui.QTextCursor.MoveOperation.End)

    def set_buttons_enabled(self, enabled):
        self.btn_export.setEnabled(enabled)
        self.btn_import.setEnabled(enabled)
        self.btn_compile.setEnabled(enabled)
        self.btn_git_commit.setEnabled(enabled)
        self.btn_git_push.setEnabled(enabled)
        self.btn_git_pull.setEnabled(enabled)

    # --- Project lock helpers ---
    def resolve_project_path(self, provided):
        if os.path.isdir(provided):
            project_files = []
            try:
                for file in os.listdir(provided):
                    if file.endswith('.project'):
                        fpath = os.path.join(provided, file)
                        project_files.append((fpath, os.path.getmtime(fpath)))
                project_files.sort(key=lambda x: x[1], reverse=True)
                if project_files:
                    return project_files[0][0]
            except:
                pass
        return provided

    def is_project_locked(self):
        proj_path = self.txt_project_path.text().strip()
        resolved = self.resolve_project_path(proj_path)
        if resolved and os.path.exists(resolved):
            lock_file = resolved + ".~u"
            return os.path.exists(lock_file)
        return False

    def launch_ide_only(self):
        proj_path = self.txt_project_path.text().strip()
        resolved_proj = self.resolve_project_path(proj_path)
        if not os.path.exists(resolved_proj):
            QtWidgets.QMessageBox.warning(self, "Ошибка", f"Файл проекта не найден:\n{resolved_proj}")
            return
            
        ide_exe = "C:\\Program Files (x86)\\Abak.IDE.1.0.0\\CODESYS\\Common\\abak.ide.exe"
        if not os.path.exists(ide_exe):
            QtWidgets.QMessageBox.warning(self, "Ошибка", f"Исполняемый файл Abak.IDE не найден по пути:\n{ide_exe}")
            return
            
        profile = "Abak.IDE V1.0.0.0"
        cmd = f'start "" "{ide_exe}" --profile="{profile}" "{resolved_proj}"'
        
        try:
            subprocess.Popen(cmd, shell=True)
            self.write_log(f"<span style='color:#00f0ff;'>Запуск Abak.IDE с проектом...</span>\nКоманда: {cmd}")
        except Exception as e:
            self.write_log(f"<span style='color:#ef4444;'>Ошибка запуска: {e}</span>")

    def run_script_only(self):
        curr_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(curr_dir, "ipc_listener.py")
        automation_script = os.path.join(curr_dir, "attach_ipc_script.py")
        
        # Запускаем python-скрипт автоматизации GUI
        cmd = f'start "" python "{automation_script}" "{script_path}"'
        
        try:
            subprocess.Popen(cmd, shell=True)
            self.write_log(f"<span style='color:#00f0ff;'>Попытка внедрения скрипта в открытый Abak.IDE...</span>\nКоманда: {cmd}")
            self.write_log("<span style='color:#a1a1aa;'>Пожалуйста, не трогайте мышь и клавиатуру в течение 2-х секунд!</span>")
        except Exception as e:
            self.write_log(f"<span style='color:#ef4444;'>Ошибка запуска: {e}</span>")

    def check_environment_status(self):
        # 1. Check IDE process
        ide_running = False
        try:
            import uiautomation as auto
            if auto.WindowControl(searchDepth=1, RegexName=r'.*Abak\.IDE.*').Exists(0, 0):
                ide_running = True
        except ImportError:
            try:
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                res = subprocess.run(["tasklist", "/FI", "IMAGENAME eq abak.ide.exe", "/NH"], capture_output=True, text=True, startupinfo=startupinfo, timeout=1.0)
                if "abak.ide.exe" in res.stdout.lower():
                    ide_running = True
            except Exception:
                pass

        # 2. Check Project lock
        proj_locked = self.is_project_locked()

        if ide_running:
            self.lbl_ide_status.setText("Abak.IDE: Запущена 🟢")
            self.lbl_ide_status.setStyleSheet("color: #10b981; font-weight: bold;")
        else:
            self.lbl_ide_status.setText("Abak.IDE: Не запущена 🔴")
            self.lbl_ide_status.setStyleSheet("color: #ef4444; font-weight: bold;")

        if proj_locked:
            self.lbl_proj_status.setText("Проект: Открыт 🟢")
            self.lbl_proj_status.setStyleSheet("color: #10b981; font-weight: bold;")
        else:
            self.lbl_proj_status.setText("Проект: Не открыт 🔴")
            self.lbl_proj_status.setStyleSheet("color: #ef4444; font-weight: bold;")

        # 3. Check Script status via ping
        if ide_running and proj_locked:
            if not self.poll_timer.isActive(): # don't interfere with real actions
                if not self.waiting_for_ping:
                    # Send ping
                    ping_data = {"action": "ping", "sources_path": "", "add_context": False}
                    try:
                        with open(req_path, "w", encoding="utf-8") as f:
                            json.dump(ping_data, f)
                        self.ping_sent_time = time.time()
                        self.waiting_for_ping = True
                        self.lbl_script_status.setText("Скрипт IPC: Проверка...")
                        self.lbl_script_status.setStyleSheet("color: #a1a1aa;")
                    except:
                        pass
                else:
                    # Check ping response
                    if os.path.exists(res_path):
                        try:
                            with open(res_path, "r", encoding="utf-8") as f:
                                res = json.load(f)
                            if res.get("success"):
                                self.lbl_script_status.setText("Скрипт IPC: Активен 🟢")
                                self.lbl_script_status.setStyleSheet("color: #10b981; font-weight: bold;")
                            else:
                                self.lbl_script_status.setText("Скрипт IPC: Ошибка 🔴")
                                self.lbl_script_status.setStyleSheet("color: #ef4444; font-weight: bold;")
                        except:
                            pass
                        finally:
                            try: os.remove(res_path)
                            except: pass
                            try: os.remove(req_path)
                            except: pass
                        self.waiting_for_ping = False
                    elif time.time() - getattr(self, 'ping_sent_time', 0) > 3.0:
                        self.lbl_script_status.setText("Скрипт IPC: Не отвечает 🔴")
                        self.lbl_script_status.setStyleSheet("color: #ef4444; font-weight: bold;")
                        self.waiting_for_ping = False
                        try: os.remove(req_path)
                        except: pass
        else:
            self.lbl_script_status.setText("Скрипт IPC: Нет среды 🔴")
            self.lbl_script_status.setStyleSheet("color: #ef4444; font-weight: bold;")
            self.waiting_for_ping = False

    # --- IPC execution logic ---
    def run_ipc_action(self, action):
        self.save_config()
        self.tabs.setCurrentIndex(0)
        self.txt_console.clear()

        # Check if project is locked (open in Abak.IDE GUI)
        # In IPC mode, the project MUST be locked (i.e. open in Abak.IDE)
        # If it is not locked, warning prompt is displayed
        if not self.is_project_locked():
            reply = QtWidgets.QMessageBox.warning(
                self,
                "Среда Abak.IDE не запущена",
                "Внимание: Не обнаружен открытый проект в Abak.IDE (отсутствует файл блокировки .~u).\n\n"
                "IPC режим требует, чтобы Abak.IDE была открыта, и в ней был запущен скрипт 'ipc_listener.py'.\n\n"
                "Отправить команду все равно?",
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
                QtWidgets.QMessageBox.StandardButton.No
            )
            if reply == QtWidgets.QMessageBox.StandardButton.No:
                return

        self.write_log(f"=== ЗАПУСК IPC ОПЕРАЦИИ: {action.upper()} ===")
        self.write_log(f"Отправка запроса в запущенную Abak.IDE...")

        # Clear previous logs and files
        if os.path.exists(res_path):
            try: os.remove(res_path)
            except: pass
        if os.path.exists(log_path):
            try: os.remove(log_path)
            except: pass
        
        # Write request file
        sources_path = self.txt_sources_path.text()
        req_data = {
            "action": action,
            "sources_path": sources_path,
            "add_context": self.chk_add_context.isChecked()
        }
        
        try:
            with open(req_path, "w", encoding="utf-8") as f:
                json.dump(req_data, f)
        except Exception as e:
            self.write_log(f"ОШИБКА записи запроса IPC: {e}")
            return

        # Start log reader
        self.set_buttons_enabled(False)
        self.log_offset = 0
        self.poll_timer.start(250) # check files every 250ms

    def poll_ipc(self):
        # Read any new log content
        if os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    file_len = os.path.getsize(log_path)
                    if file_len < self.log_offset:
                        self.log_offset = 0
                    f.seek(self.log_offset)
                    new_data = f.read()
                    self.log_offset = f.tell()
                if new_data:
                    self.write_log(new_data.strip())
            except Exception:
                pass

        # Check if response arrived
        if os.path.exists(res_path):
            self.poll_timer.stop()
            time.sleep(0.1) # tiny delay to let buffer flush
            
            # Read final remaining log content
            if os.path.exists(log_path):
                try:
                    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                        f.seek(self.log_offset)
                        new_data = f.read()
                    if new_data:
                        self.write_log(new_data.strip())
                except Exception:
                    pass

            try:
                with open(res_path, "r", encoding="utf-8") as f:
                    res = json.load(f)
                success = res.get("success", False)
                error = res.get("error", "")
                
                if success:
                    self.write_log("\n<span style='color:#10b981; font-weight:bold;'>=== IPC ОПЕРАЦИИ ВЫПОЛНЕНА УСПЕШНО ===</span>")
                else:
                    self.write_log(f"\n<span style='color:#ef4444; font-weight:bold;'>=== ОШИБКА ВНУТРИ IDE: {error} ===</span>")
            except Exception as e:
                self.write_log(f"\n<span style='color:#ef4444; font-weight:bold;'>=== ОШИБКА ЧТЕНИЯ ОТВЕТА IPC: {e} ===</span>")
            finally:
                # Clean up files
                try: os.remove(res_path)
                except: pass
                try: os.remove(log_path)
                except: pass
                
                self.set_buttons_enabled(True)
                self.refresh_git_status()

    # --- Git Functionality ---
    def refresh_git_status(self):
        self.lst_git_changes.clear()
        self.txt_diff.clear()
        
        # Relative directory of repo
        repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        cmd = ["git", "status", "--porcelain"]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                cwd=repo_dir,
                shell=True
            )
            if result.returncode == 0:
                lines = result.stdout.splitlines()
                if not lines:
                    self.lst_git_changes.addItem("Нет измененных файлов (Git репозиторий чист)")
                    return
                
                for line in lines:
                    if len(line) > 3:
                        status = line[:2].strip()
                        filepath = line[3:]
                        display_text = f"[{status}] {filepath}"
                        item = QtWidgets.QListWidgetItem(display_text)
                        item.setData(QtCore.Qt.ItemDataRole.UserRole, filepath)
                        self.lst_git_changes.addItem(item)
            else:
                self.lst_git_changes.addItem("Ошибка при выполнении git status")
        except Exception as e:
            self.lst_git_changes.addItem(f"Ошибка проверки Git: {e}")

    def show_selected_diff(self):
        self.txt_diff.clear()
        selected_items = self.lst_git_changes.selectedItems()
        if not selected_items:
            return
        
        filepath = selected_items[0].data(QtCore.Qt.ItemDataRole.UserRole)
        if not filepath:
            return

        repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cmd = ["git", "diff", "--", filepath]
        
        display_status = selected_items[0].text()
        if "[??]" in display_status:
            cmd = ["git", "diff", "--no-index", "NUL", filepath]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                cwd=repo_dir,
                shell=True
            )
            diff_text = result.stdout
            
            if not diff_text and "[??]" in display_status:
                abs_file_path = os.path.join(repo_dir, filepath)
                if os.path.exists(abs_file_path):
                    try:
                        with open(abs_file_path, "r", encoding="utf-8") as f:
                            lines = f.readlines()
                            diff_text = "".join(f"+ {line}" for line in lines)
                    except:
                        diff_text = "Не удалось прочитать содержимое нового файла."
            
            if not diff_text:
                self.txt_diff.setHtml("<span style='color:#a1a1aa;'>Нет изменений в выбранном файле.</span>")
                return

            html_lines = []
            for line in diff_text.splitlines():
                escaped_line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                if escaped_line.startswith("+") and not escaped_line.startswith("+++"):
                    html_lines.append(f"<span style='color:#10b981; background-color:#064e3b;'>{escaped_line}</span>")
                elif escaped_line.startswith("-") and not escaped_line.startswith("---"):
                    html_lines.append(f"<span style='color:#ef4444; background-color:#7f1d1d;'>{escaped_line}</span>")
                elif escaped_line.startswith("@@"):
                    html_lines.append(f"<span style='color:#3b82f6; font-weight:bold;'>{escaped_line}</span>")
                else:
                    html_lines.append(escaped_line)

            self.txt_diff.setHtml("<br>".join(html_lines))
        except Exception as e:
            self.txt_diff.setHtml(f"<span style='color:#ef4444;'>Ошибка при формировании diff: {e}</span>")

    def run_git_commit(self):
        commit_msg = self.txt_commit_msg.text().strip()
        if not commit_msg:
            QtWidgets.QMessageBox.warning(self, "Предупреждение", "Введите сообщение коммита перед фиксацией!")
            return

        self.tabs.setCurrentIndex(0)
        self.txt_console.clear()
        self.write_log("=== ФИКСАЦИЯ ИЗМЕНЕНИЙ В GIT ===")

        repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Stage all changes
        subprocess.run(["git", "add", "."], capture_output=True, text=True, cwd=repo_dir, shell=True)
        
        # Run commit
        res = subprocess.run(["git", "commit", "-m", f'"{commit_msg}"'], capture_output=True, text=True, cwd=repo_dir, shell=True)
        
        self.write_log(res.stdout)
        self.write_log(res.stderr)
        
        if res.returncode == 0:
            self.write_log("\n=== КОММИТ УСПЕШНО СОЗДАН ===")
            self.txt_commit_msg.clear()
        else:
            self.write_log("\n=== ОШИБКА СОЗДАНИЯ КОММИТА ===")
        self.refresh_git_status()

    def run_git_push(self):
        self.tabs.setCurrentIndex(0)
        self.txt_console.clear()
        self.write_log("=== ОТПРАВКА ИЗМЕНЕНИЙ В УДАЛЕННЫЙ РЕПОЗИТОРИЙ (PUSH) ===")

        repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        res = subprocess.run(["git", "push"], capture_output=True, text=True, cwd=repo_dir, shell=True)
        self.write_log(res.stdout)
        self.write_log(res.stderr)
        
        if res.returncode == 0:
            self.write_log("\n=== PUSH УСПЕШНО ЗАВЕРШЕН ===")
        else:
            self.write_log("\n=== ОШИБКА ПРИ ВЫПОЛНЕНИИ PUSH ===")
        self.refresh_git_status()

    def run_git_pull(self):
        self.tabs.setCurrentIndex(0)
        self.txt_console.clear()
        self.write_log("=== ПОЛУЧЕНИЕ ИЗМЕНЕНИЙ ИЗ УДАЛЕННОГО РЕПОЗИТОРИЯ (PULL) ===")

        repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        res = subprocess.run(["git", "pull"], capture_output=True, text=True, cwd=repo_dir, shell=True)
        self.write_log(res.stdout)
        self.write_log(res.stderr)
        
        if res.returncode == 0:
            self.write_log("\n=== PULL УСПЕШНО ЗАВЕРШЕН ===")
        else:
            self.write_log("\n=== ОШИБКА ПРИ ВЫПОЛНЕНИИ PULL ===")
        self.refresh_git_status()

    def load_help_content(self):
        help_html = """
        <h1 style="color:#00f0ff; margin-bottom:5px;">Инструкция по использованию IPC-режима</h1>
        <p style="color:#a1a1aa;">Этот форк оптимизирован для быстрой синхронизации напрямую с открытым в Abak.IDE GUI-проектом через файловый протокол IPC.</p>
        <hr style="border: 0; border-top: 1px solid #2d2d34; margin: 15px 0;">

        <h2 style="color:#3b82f6; margin-top:15px;">🚀 Как запустить рабочий процесс</h2>
        <ol>
            <li>Запустите среду разработки <b>Abak.IDE</b> и откройте ваш рабочий проект.</li>
            <li>В меню выберите: <b>Инструменты -> Скрипты -> Выполнить файл скрипта...</b> (Tools -> Scripting -> Run Script).</li>
            <li>Выберите файл скрипта сервера: <code>standalone-sync-ipc/ipc_listener.py</code>. Нажмите "Открыть". На панели сообщений CODESYS появится текст <i>"CODESYS IPC Server Listener is running..."</i>.</li>
            <li>Запустите это приложение с помощью скрипта <code>manage_ipc.bat</code>.</li>
        </ol>

        <h2 style="color:#f59e0b; margin-top:20px;">⚡ Мгновенная синхронизация</h2>
        <p>Так как проект уже загружен в оперативную память Abak.IDE, все команды выполняются моментально:</p>
        <ul>
            <li><b>Быстрый экспорт исходников</b>: Выгрузит все POU в ST-файлы за секунду. Используйте после изменения кода в среде.</li>
            <li><b>Мгновенный импорт в среду</b>: Перепишет код внутри открытых POU в Abak.IDE в реальном времени. Все импортированные изменения <b>сразу появятся на ваших экранах</b> в среде разработки!</li>
            <li><b>Тест компиляции в IDE</b>: Среда скомпилирует текущие изменения и передаст количество предупреждений/ошибок прямо в это окно.</li>
        </ul>

        <h2 style="color:#10b981; margin-top:20px;">🌿 Управление версиями (Git)</h2>
        <p>Используйте вкладку <b>Git Версионирование</b> для фиксации текстовых правок, просмотра диффов и работы с коммитами.</p>
        """
        self.txt_help.setHtml(help_html)


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
