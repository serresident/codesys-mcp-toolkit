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

class CmdWorker(QtCore.QThread):
    log_received = Signal(str)
    process_finished = Signal(int)

    def __init__(self, cmd, cwd=None, env=None):
        super().__init__()
        self.cmd = cmd
        self.cwd = cwd
        self.env = env

    def run(self):
        try:
            # Set system encoding to UTF-8 for subprocess piping
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            process = subprocess.Popen(
                self.cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1,
                shell=True,
                cwd=self.cwd,
                env=self.env,
                startupinfo=startupinfo
            )
            
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                self.log_received.emit(line)
                
            process.wait()
            self.process_finished.emit(process.returncode)
        except Exception as e:
            self.log_received.emit(f"\n[ERROR] Exception during process execution: {str(e)}\n")
            self.process_finished.emit(-1)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CODESYS Git Sync & Version Control Manager")
        self.resize(1100, 750)
        self.setStyleSheet(DARK_THEME)

        self.config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui_config.json")
        self.active_worker = None

        self.init_ui()
        self.load_config()
        self.refresh_git_status()

    def init_ui(self):
        # Central Widget & Main Layout
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QtWidgets.QHBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # --- Sidebar / Left Panel (Configuration) ---
        sidebar = QtWidgets.QWidget()
        sidebar.setFixedWidth(340)
        sidebar_layout = QtWidgets.QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(12)

        # Path Settings Group
        grp_paths = QtWidgets.QGroupBox("Пути и настройки")
        paths_layout = QtWidgets.QVBoxLayout(grp_paths)
        paths_layout.setSpacing(8)

        paths_layout.addWidget(QtWidgets.QLabel("CODESYS / Abak.IDE EXE Path:"))
        self.txt_codesys_exe = QtWidgets.QLineEdit()
        self.txt_codesys_exe.setPlaceholderText("C:\\Program Files (x86)\\...\\abak.ide.exe")
        paths_layout.addWidget(self.txt_codesys_exe)

        paths_layout.addWidget(QtWidgets.QLabel("CODESYS Project File or Directory:"))
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

        paths_layout.addWidget(QtWidgets.QLabel("CODESYS Target Profile Name:"))
        self.txt_profile = QtWidgets.QLineEdit()
        self.txt_profile.setText("Abak.IDE V1.0.0.0")
        paths_layout.addWidget(self.txt_profile)

        sidebar_layout.addWidget(grp_paths)

        # Quick Actions Group
        grp_actions = QtWidgets.QGroupBox("Синхронизация и сборка")
        actions_layout = QtWidgets.QVBoxLayout(grp_actions)
        actions_layout.setSpacing(10)

        self.btn_export = QtWidgets.QPushButton("⬇ Экспорт исходников (.st)")
        self.btn_export.setObjectName("btn_action_sync")
        self.btn_export.clicked.connect(lambda: self.run_sync_action("export"))
        actions_layout.addWidget(self.btn_export)

        self.btn_import = QtWidgets.QPushButton("⬆ Импорт изменений (.st -> PLC)")
        self.btn_import.setObjectName("btn_action_sync")
        self.btn_import.clicked.connect(lambda: self.run_sync_action("import"))
        actions_layout.addWidget(self.btn_import)

        self.btn_compile = QtWidgets.QPushButton("🔨 Запустить тест компиляции")
        self.btn_compile.setObjectName("btn_action_compile")
        self.btn_compile.clicked.connect(self.run_compile_check)
        actions_layout.addWidget(self.btn_compile)

        sidebar_layout.addWidget(grp_actions)
        sidebar_layout.addStretch()

        main_layout.addWidget(sidebar)

        # --- Right Panel (Main Tab Widget) ---
        self.tabs = QtWidgets.QTabWidget()
        main_layout.addWidget(self.tabs)

        # Tab 1: Sync Logs Console
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

        self.tabs.addTab(self.tab_logs, "📟 Лог выполнения")

        # Tab 2: Git Integration Control
        self.tab_git = QtWidgets.QWidget()
        lay_tab_git = QtWidgets.QVBoxLayout(self.tab_git)
        lay_tab_git.setContentsMargins(10, 10, 10, 10)

        # Splitter to balance diff viewer and files list
        git_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        lay_tab_git.addWidget(git_splitter)

        # Git changes left list
        git_left_panel = QtWidgets.QWidget()
        lay_git_left = QtWidgets.QVBoxLayout(git_left_panel)
        lay_git_left.setContentsMargins(0, 0, 0, 0)
        
        lay_git_left.addWidget(QtWidgets.QLabel("Измененные файлы (Git Status):"))
        
        self.lst_git_changes = QtWidgets.QListWidget()
        self.lst_git_changes.itemSelectionChanged.connect(self.show_selected_diff)
        lay_git_left.addWidget(self.lst_git_changes)

        # Commit interface
        lay_commit = QtWidgets.QVBoxLayout()
        lay_commit.setSpacing(6)
        lay_commit.addWidget(QtWidgets.QLabel("Сообщение коммита:"))
        self.txt_commit_msg = QtWidgets.QLineEdit()
        self.txt_commit_msg.setPlaceholderText("Например: Добавлено масштабирование ПИД...")
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

        # Git diff right panel
        git_right_panel = QtWidgets.QWidget()
        lay_git_right = QtWidgets.QVBoxLayout(git_right_panel)
        lay_git_right.setContentsMargins(0, 0, 0, 0)
        lay_git_right.addWidget(QtWidgets.QLabel("Просмотр изменений (Diff):"))
        
        self.txt_diff = QtWidgets.QTextBrowser()
        lay_git_right.addWidget(self.txt_diff)
        git_splitter.addWidget(git_right_panel)

        # Set default weights for splitter
        git_splitter.setStretchFactor(0, 2)
        git_splitter.setStretchFactor(1, 3)

        self.tabs.addTab(self.tab_git, "🌿 Git Версионирование")

    # --- Config Management ---
    def load_config(self):
        default_codesys = 'C:\\Program Files (x86)\\Abak.IDE.1.0.0\\CODESYS\\Common\\abak.ide.exe'
        default_proj = 'D:\\Projects\\CEX_15\\апп 511\\PLC'
        default_src = 'D:\\Projects\\CEX_15\\апп 511\\PLC\\project_sources'
        
        # Override with relative path if we are in a subfolder
        curr_dir = os.path.dirname(os.path.abspath(__file__))
        local_st_sources = os.path.join(curr_dir, "sources_st", "511_05")
        if os.path.exists(local_st_sources):
            default_src = local_st_sources

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.txt_codesys_exe.setText(data.get("codesys_exe", default_codesys))
                    self.txt_project_path.setText(data.get("project_path", default_proj))
                    self.txt_sources_path.setText(data.get("sources_path", default_src))
                    self.txt_profile.setText(data.get("profile", "Abak.IDE V1.0.0.0"))
                    return
            except:
                pass

        self.txt_codesys_exe.setText(default_codesys)
        self.txt_project_path.setText(default_proj)
        self.txt_sources_path.setText(default_src)

    def save_config(self):
        data = {
            "codesys_exe": self.txt_codesys_exe.text(),
            "project_path": self.txt_project_path.text(),
            "sources_path": self.txt_sources_path.text(),
            "profile": self.txt_profile.text()
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

    # --- Log Display Helpers ---
    def write_log(self, text):
        # Format typical output lines dynamically with colors
        formatted_line = text
        if "SCRIPT_SUCCESS" in text or "SYNC SUCCESS" in text or "completed successfully" in text:
            formatted_line = f"<span style='color:#10b981; font-weight:bold;'>{text}</span>"
        elif "SCRIPT_ERROR" in text or "ERROR" in text or "failed" in text or "Exception" in text:
            formatted_line = f"<span style='color:#ef4444; font-weight:bold;'>{text}</span>"
        elif "WARN" in text or "WARNING" in text:
            formatted_line = f"<span style='color:#f59e0b;'>{text}</span>"
        elif "DEBUG" in text:
            formatted_line = f"<span style='color:#06b6d4;'>{text}</span>"
        
        self.txt_console.append(formatted_line)
        # Auto scroll to bottom
        self.txt_console.moveCursor(QtGui.QTextCursor.MoveOperation.End)

    # --- Action Execution ---
    def set_buttons_enabled(self, enabled):
        self.btn_export.setEnabled(enabled)
        self.btn_import.setEnabled(enabled)
        self.btn_compile.setEnabled(enabled)
        self.btn_git_commit.setEnabled(enabled)
        self.btn_git_push.setEnabled(enabled)
        self.btn_git_pull.setEnabled(enabled)

    def run_sync_action(self, action):
        self.save_config()
        self.tabs.setCurrentIndex(0) # Switch to logs console
        self.txt_console.clear()
        
        proj_path = self.txt_project_path.text()
        sources_path = self.txt_sources_path.text()
        exe_path = self.txt_codesys_exe.text()
        profile = self.txt_profile.text()

        self.write_log(f"=== ЗАПУСК ОПЕРАЦИИ СИНХРОНИЗАЦИИ: {action.upper()} ===")
        self.write_log(f"Проект: {proj_path}")
        self.write_log(f"Папка исходников: {sources_path}\n")

        # Command to invoke sync_cli.js
        cmd = ["node", "sync_cli.js", action, proj_path, sources_path, "--codesys-path", exe_path, "--codesys-profile", profile]
        
        self.set_buttons_enabled(False)
        self.active_worker = CmdWorker(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
        self.active_worker.log_received.connect(self.write_log)
        self.active_worker.process_finished.connect(self.on_sync_finished)
        self.active_worker.start()

    def on_sync_finished(self, return_code):
        self.set_buttons_enabled(True)
        self.active_worker = None
        if return_code == 0:
            self.write_log("\n<span style='color:#10b981; font-weight:bold;'>=== СИНХРОНИЗАЦИЯ УСПЕШНО ЗАВЕРШЕНА ===</span>")
        else:
            self.write_log(f"\n<span style='color:#ef4444; font-weight:bold;'>=== СИНХРОНИЗАЦИЯ ЗАВЕРШИЛАСЬ С ОШИБКОЙ (Код возврата: {return_code}) ===</span>")
        self.refresh_git_status()

    # --- Compilation Test via Python script engine in CODESYS ---
    def run_compile_check(self):
        self.save_config()
        self.tabs.setCurrentIndex(0)
        self.txt_console.clear()

        exe_path = self.txt_codesys_exe.text()
        profile = self.txt_profile.text()
        proj_path = self.txt_project_path.text()

        # Since it is a directory, resolve to latest .project file dynamically in python script
        self.write_log("=== ИНИЦИАЛИЗАЦИЯ ТЕСТА КОМПИЛЯЦИИ ===")
        self.write_log(f"CODESYS: {exe_path}")
        self.write_log(f"Выполняется поиск проекта и компиляция...\n")

        # Python script to run inside CODESYS
        python_script_content = f"""# -*- coding: utf-8 -*-
import sys
import scriptengine as script_engine
import os
import time

def resolve_project_path(provided):
    if os.path.isdir(provided):
        project_files = []
        for file in os.listdir(provided):
            if file.endswith('.project'):
                fpath = os.path.join(provided, file)
                project_files.append((fpath, os.path.getmtime(fpath)))
        project_files.sort(key=lambda x: x[1], reverse=True)
        if project_files:
            return project_files[0][0]
    return provided

PROJECT_RAW = r"{proj_path}"
resolved_path = resolve_project_path(PROJECT_RAW)
print("DEBUG: Project resolved to: %s" % resolved_path)

try:
    update_mode = script_engine.VersionUpdateFlags.NoUpdates | script_engine.VersionUpdateFlags.SilentMode
    proj = script_engine.projects.open(resolved_path, update_flags=update_mode)
    time.sleep(2.0)
    
    app = None
    apps = proj.find("Application", True)
    if apps:
        app = apps[0]
    else:
        # Try active application fallback
        app = proj.active_application

    if app:
        print("Application found: %s. Rebuilding..." % app.get_name())
        app.clean()
        build_result = app.build()
        print("Build command completed.")
        
        if build_result:
            has_errors = False
            for msg in build_result.messages:
                # Severity values: Error=1, Warning=2, Info=3
                sev = "INFO"
                if msg.severity == 1:
                    sev = "ERROR"
                    has_errors = True
                elif msg.severity == 2:
                    sev = "WARNING"
                print("[%s] %s" % (sev, msg.text))
                
            if has_errors:
                print("SCRIPT_ERROR: Compilation completed with errors.")
                sys.exit(1)
        
        print("SCRIPT_SUCCESS: Compilation completed successfully without errors.")
        sys.exit(0)
    else:
        raise RuntimeError("No Application object found in project.")
except Exception as err:
    print("SCRIPT_ERROR: Exception during execution: %s" % err)
    sys.exit(1)
"""
        # Save Python code to a temp file
        temp_fd, temp_path = tempfile.mkstemp(suffix=".py", prefix="codesys_compile_")
        os.close(temp_fd)
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(python_script_content)
        except Exception as err:
            self.write_log(f"ERROR creating temp script: {err}")
            return

        cmd = [f'"{exe_path}"', f'--profile="{profile}"', "--noUI", f'--runscript="{temp_path}"']
        
        # Spawn execution
        self.set_buttons_enabled(False)
        self.active_worker = CmdWorker(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
        
        # Clean up temp file when done
        def cleanup_temp(rc):
            try:
                os.remove(temp_path)
            except:
                pass
            self.set_buttons_enabled(True)
            self.active_worker = None
            if rc == 0:
                self.write_log("\n<span style='color:#10b981; font-weight:bold;'>=== КОМПИЛЯЦИЯ УСПЕШНО ПРОЙДЕНА ===</span>")
            else:
                self.write_log("\n<span style='color:#ef4444; font-weight:bold;'>=== СБОЙ ПРИ ТЕСТЕ КОМПИЛЯЦИИ ===</span>")

        self.active_worker.log_received.connect(self.write_log)
        self.active_worker.process_finished.connect(cleanup_temp)
        self.active_worker.start()

    # --- Git Functionality ---
    def refresh_git_status(self):
        self.lst_git_changes.clear()
        self.txt_diff.clear()
        
        # Execute porcelain status to see files
        cmd = ["git", "status", "--porcelain"]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                cwd=os.path.dirname(os.path.abspath(__file__)),
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
                        # Map symbols to human-readable text
                        display_text = f"[{status}] {filepath}"
                        item = QtWidgets.QListWidgetItem(display_text)
                        # Set user-data for direct file path query
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

        cmd = ["git", "diff", "--", filepath]
        
        # If file is untracked (status is '??'), show diff relative to empty file
        display_status = selected_items[0].text()
        if "[??]" in display_status:
            cmd = ["git", "diff", "--no-index", "NUL", filepath]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                cwd=os.path.dirname(os.path.abspath(__file__)),
                shell=True
            )
            diff_text = result.stdout
            
            if not diff_text and "[??]" in display_status:
                # Fallback: just read the whole untracked file contents
                abs_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filepath)
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

            # Format diff lines with HTML
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

        # Stage all changes first
        add_result = subprocess.run(["git", "add", "."], capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__)), shell=True)
        self.write_log(add_result.stdout)
        
        # Commit command
        cmd = ["git", "commit", "-m", f'"{commit_msg}"']
        
        self.set_buttons_enabled(False)
        self.active_worker = CmdWorker(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
        
        def on_commit_done(rc):
            self.set_buttons_enabled(True)
            self.active_worker = None
            if rc == 0:
                self.write_log("\n<span style='color:#10b981; font-weight:bold;'>=== КОММИТ УСПЕШНО СОЗДАН ===</span>")
                self.txt_commit_msg.clear()
            else:
                self.write_log("\n<span style='color:#ef4444; font-weight:bold;'>=== ОШИБКА СОЗДАНИЯ КОММИТА ===</span>")
            self.refresh_git_status()

        self.active_worker.log_received.connect(self.write_log)
        self.active_worker.process_finished.connect(on_commit_done)
        self.active_worker.start()

    def run_git_push(self):
        self.tabs.setCurrentIndex(0)
        self.txt_console.clear()
        self.write_log("=== ОТПРАВКА ИЗМЕНЕНИЙ В УДАЛЕННЫЙ РЕПОЗИТОРИЙ (PUSH) ===")

        cmd = ["git", "push"]
        self.set_buttons_enabled(False)
        self.active_worker = CmdWorker(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
        
        def on_push_done(rc):
            self.set_buttons_enabled(True)
            self.active_worker = None
            if rc == 0:
                self.write_log("\n<span style='color:#10b981; font-weight:bold;'>=== PUSH УСПЕШНО ЗАВЕРШЕН ===</span>")
            else:
                self.write_log("\n<span style='color:#ef4444; font-weight:bold;'>=== ОШИБКА ПРИ ВЫПОЛНЕНИИ PUSH ===</span>")
            self.refresh_git_status()

        self.active_worker.log_received.connect(self.write_log)
        self.active_worker.process_finished.connect(on_push_done)
        self.active_worker.start()

    def run_git_pull(self):
        self.tabs.setCurrentIndex(0)
        self.txt_console.clear()
        self.write_log("=== ПОЛУЧЕНИЕ ИЗМЕНЕНИЙ ИЗ УДАЛЕННОГО РЕПОЗИТОРИЯ (PULL) ===")

        cmd = ["git", "pull"]
        self.set_buttons_enabled(False)
        self.active_worker = CmdWorker(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
        
        def on_pull_done(rc):
            self.set_buttons_enabled(True)
            self.active_worker = None
            if rc == 0:
                self.write_log("\n<span style='color:#10b981; font-weight:bold;'>=== PULL УСПЕШНО ЗАВЕРШЕН ===</span>")
            else:
                self.write_log("\n<span style='color:#ef4444; font-weight:bold;'>=== ОШИБКА ПРИ ВЫПОЛНЕНИИ PULL ===</span>")
            self.refresh_git_status()

        self.active_worker.log_received.connect(self.write_log)
        self.active_worker.process_finished.connect(on_pull_done)
        self.active_worker.start()


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
