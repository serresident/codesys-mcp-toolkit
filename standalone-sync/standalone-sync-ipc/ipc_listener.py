# -*- coding: utf-8 -*-
# ipc_listener.py
# Python script to run INSIDE Abak.IDE (Tools -> Scripting -> Run Script...)
# Serves requests from gui_manager_ipc.py via File IPC.

import sys
import os
import time
import json
import traceback
import tempfile
import shutil
import scriptengine as script_engine
from scriptengine import PouType

temp_dir = tempfile.gettempdir()
req_path = os.path.join(temp_dir, "codesys_ipc_req.json")
res_path = os.path.join(temp_dir, "codesys_ipc_res.json")
log_path = os.path.join(temp_dir, "codesys_ipc.log")

# Custom output class to redirect prints to log file
class Logger(object):
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, "w")

    def write(self, message):
        try:
            self.terminal.write(message)
        except Exception:
            pass
            
        if sys.version_info[0] < 3 and isinstance(message, unicode):
            message = message.encode('utf-8')
        elif isinstance(message, str) and sys.version_info[0] >= 3:
            # Under python 3, write expects string if opened in "w", but we can write directly
            pass

        try:
            self.log.write(message)
            self.log.flush()
        except Exception:
            pass

    def flush(self):
        try:
            self.terminal.flush()
        except Exception:
            pass
        try:
            self.log.flush()
        except Exception:
            pass

    def close(self):
        try:
            self.log.close()
        except Exception:
            pass

def get_extension(node):
    POU_GUID = "6f9dac99-8de1-4efc-8465-68ac443b7d08"
    GVL_GUIDS = ["ff4b50c3-1739-4f7f-8d73-4081bc326c5f", "ffbfa93a-b94d-45fc-a329-229860183b1d", "261bd6e6-249c-4232-bb6f-84c2fbeef430"]
    DUT_GUIDS = ["2dbcc358-b378-477c-9bfe-b591583d7357", "2db5746d-d284-4425-9f7f-2663a34b0ebc"]
    METHOD_GUID = "f8a58466-d7f6-439f-bbb8-d4600e41d099"
    ACTION_GUID = "561775e5-f4bd-44a6-8c7e-07e37609a068"
    PROPERTY_GUID = "5a3b8626-d3e9-4f37-98b5-66420063d91e"

    type_str = str(node.type).lower()
    if type_str == POU_GUID:
        try:
            pt = node.pou_type
            if pt == PouType.Program: return '.prg.st'
            elif pt == PouType.FunctionBlock: return '.fb.st'
            elif pt == PouType.Function: return '.func.st'
        except Exception:
            decl = ""
            if hasattr(node, 'textual_declaration') and node.textual_declaration:
                decl = node.textual_declaration.text or ""
            import re
            decl_clean = re.sub(r'\(\*[\s\S]*?\*\)', '', decl)
            decl_clean = re.sub(r'//.*', '', decl_clean)
            words = re.findall(r'\b\w+\b', decl_clean.upper())
            if 'FUNCTION_BLOCK' in words:
                return '.fb.st'
            elif 'FUNCTION' in words:
                return '.func.st'
            elif 'PROGRAM' in words:
                return '.prg.st'
            return '.prg.st'
    elif type_str == METHOD_GUID:
        return '.method.st'
    elif type_str == ACTION_GUID:
        return '.action.st'
    elif type_str == PROPERTY_GUID:
        return '.property.st'
    elif type_str in GVL_GUIDS:
        return '.gvl.st'
    elif type_str in DUT_GUIDS:
        return '.dut.st'
    elif hasattr(node, 'textual_declaration') and node.textual_declaration is not None:
        return '.st'
    return None

def clean_or_create_dir(path):
    if os.path.exists(path):
        try: shutil.rmtree(path)
        except: pass
    if not os.path.exists(path):
        os.makedirs(path)

def to_utf8(val):
    if val is None:
        return ""
    if sys.version_info[0] < 3:
        if isinstance(val, unicode):
            return val.encode('utf-8')
        return str(val)
    else:
        if isinstance(val, str):
            return val.encode('utf-8')
        return bytes(val)

def export_object(node, disk_path):
    try:
        name = node.get_name()
    except:
        return
    if not name: return
    ext = get_extension(node)
    
    children = []
    try: children = node.get_children(False)
    except: pass
    
    exportable_children = [c for c in children if get_extension(c) is not None]
    
    if ext:
        if exportable_children:
            obj_dir = os.path.join(disk_path, name)
            if not os.path.exists(obj_dir):
                os.makedirs(obj_dir)
            file_path = os.path.join(obj_dir, name + ext)
            child_disk_path = obj_dir
        else:
            file_path = os.path.join(disk_path, name + ext)
            child_disk_path = disk_path
            
        decl = node.textual_declaration.text if hasattr(node, 'textual_declaration') and node.textual_declaration else ""
        impl = None
        if hasattr(node, 'textual_implementation') and node.textual_implementation:
            impl = node.textual_implementation.text
            
        with open(file_path, 'wb') as f:
            f.write(to_utf8("// @OBJECT_ID: " + str(node.guid) + "\n"))
            f.write(to_utf8("// @DECLARATION\n"))
            f.write(to_utf8(decl))
            if impl is not None:
                f.write(to_utf8("\n\n// @IMPLEMENTATION\n"))
                f.write(to_utf8(impl))
                
        # Convert path to file:/// URI format for clickable links
        uri_path = "file:///" + file_path.replace('\\', '/')
        print("Exported: %s -> %s" % (name, uri_path))
        
        for child in exportable_children:
            export_object(child, child_disk_path)
    else:
        if hasattr(node, 'is_folder') and node.is_folder:
            folder_dir = os.path.join(disk_path, name)
            if not os.path.exists(folder_dir):
                os.makedirs(folder_dir)
            child_disk_path = folder_dir
        else:
            child_disk_path = disk_path
            
        for child in children:
            export_object(child, child_disk_path)

def parse_st_file(file_path):
    with open(file_path, 'rb') as f:
        content = f.read().decode('utf-8')
    
    guid = None
    decl = ""
    impl = None
    
    lines = content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("// @OBJECT_ID:"):
            guid = line.split(":", 1)[1].strip()
            i += 1
            continue
        elif line.strip() == "// @DECLARATION":
            i += 1
            decl_lines = []
            while i < len(lines) and lines[i].strip() != "// @IMPLEMENTATION":
                if lines[i].startswith("// @OBJECT_ID:"):
                    break
                decl_lines.append(lines[i])
                i += 1
            decl = "\n".join(decl_lines)
            continue
        elif line.strip() == "// @IMPLEMENTATION":
            i += 1
            impl_lines = []
            while i < len(lines):
                impl_lines.append(lines[i])
                i += 1
            impl = "\n".join(impl_lines)
            break
        i += 1
        
    return guid, decl, impl

def get_relative_parts(filepath, base_dir):
    relpath = os.path.relpath(filepath, base_dir)
    normalized = relpath.replace('\\', '/')
    return normalized.split('/')

def find_or_create_folder_path(root_node, path_parts):
    current = root_node
    for part in path_parts:
        found = None
        for child in current.get_children(False):
            if child.get_name() == part:
                found = child
                break
        if not found:
            print("Creating folder: %s under %s" % (part, current.get_name()))
            found = current.create_folder(part)
        current = found
    return current

def write_project_context(proj, EXPORT_DIR_PATH):
    context_dir = os.path.join(EXPORT_DIR_PATH, ".context")
    if not os.path.exists(context_dir):
        os.makedirs(context_dir)
        
    project_path = "Unknown"
    try: project_path = proj.path
    except: pass
    project_name = os.path.basename(project_path) if project_path else "Unknown"
    
    # Write context.md
    context_md_path = os.path.join(context_dir, "context.md")
    context_content = """# CODESYS Project Context & Sync Toolkit

Этот каталог создан автоматически при экспорте исходных кодов PLC. Он содержит метаданные проекта и инструменты синхронизации для обеспечения совместимости с другими ИИ-агентами (AI-Ready).

## Метаданные проекта
- **Название проекта**: {project_name}
- **Путь к файлу проекта**: {project_path}
- **Среда разработки**: Abak.IDE V1.0.0 (CODESYS V3.5)
- **Целевой язык**: Structured Text (.st)
- **Инструмент синхронизации**: File IPC (Inter-Process Communication)

## Как запустить работу с проектом
Этот каталог содержит все необходимые скрипты для обеспечения мгновенной синхронизации с открытой средой разработки:

1. **В среде Abak.IDE**: Откройте проект и запустите скрипт `.context/ipc_listener.py` (*Tools -> Scripting -> Run Script*). Это запустит асинхронный .NET-таймер, который слушает запросы от ИИ-агентов.
2. **В ИИ-агенте**: Вы можете выполнять синхронизацию автономно с помощью команды:
   * **Экспорт**: `python .context/sync_ipc_cli.py --action export`
   * **Импорт**: `python .context/sync_ipc_cli.py --action import`
   * **Компиляция**: `python .context/sync_ipc_cli.py --action compile`

## Возможные проблемы и решения (Troubleshooting)
* **Зависание среды**: Обычные циклы `while True` вешают главный UI-поток CODESYS. Наш скрипт `ipc_listener.py` использует .NET-таймер `System.Windows.Forms.Timer`, который выполняется асинхронно и не вешает интерфейс.
* **Ошибка "open() got an unexpected keyword argument 'encoding'"**: Среда Abak.IDE использует IronPython 2.7. Стандартная функция `open` не имеет параметра `encoding`. В скрипте реализован безопасный метод `to_utf8` для обработки юникода.
* **Ошибка "Охраняется для пользователя ..."**: Возникает, если проект уже открыт в GUI, а вы пытаетесь запустить фоновую синхронизацию (headless). Для работы при открытой среде используйте только IPC-версию!
""".format(project_name=project_name, project_path=project_path)
    
    with open(context_md_path, "wb") as f:
        f.write(to_utf8(context_content))
        
    # Copy tools
    tools_dir = None
    try:
        tools_dir = os.path.dirname(os.path.abspath(__file__))
    except:
        pass
    if not tools_dir or not os.path.exists(os.path.join(tools_dir, "ipc_listener.py")):
        # fallback
        workspace_dir = os.path.dirname(os.path.dirname(EXPORT_DIR_PATH))
        tools_dir = os.path.join(workspace_dir, "standalone-sync-ipc")
        
    if os.path.exists(tools_dir):
        files_to_copy = ["ipc_listener.py", "gui_manager_ipc.py", "sync_ipc_cli.py", "manage_ipc.bat", "README_IPC.md"]
        for fname in files_to_copy:
            src_file = os.path.join(tools_dir, fname)
            dst_file = os.path.join(context_dir, fname)
            if os.path.exists(src_file):
                try:
                    shutil.copy2(src_file, dst_file)
                    print("Copied tool to context: %s" % fname)
                except Exception as e:
                    print("WARN: Failed to copy %s: %s" % (fname, e))

def run_export(proj, EXPORT_DIR_PATH, add_context=False):
    print("Exporting PLCopen XML to folder...")
    clean_or_create_dir(EXPORT_DIR_PATH)
    
    xml_path = os.path.join(EXPORT_DIR_PATH, "project_sources.xml")
    print("Exporting PLCopen XML to: %s" % xml_path)
    apps = proj.find("Application", True)
    if apps:
        app = apps[0]
        proj.export_xml([app], xml_path, recursive=True, export_folder_structure=True, declarations_as_plaintext=True)
        print("XML export done.")
        
        for child in app.get_children(False):
            export_object(child, EXPORT_DIR_PATH)
            
        if add_context:
            try:
                write_project_context(proj, EXPORT_DIR_PATH)
            except Exception as e:
                print("WARN: Failed to write context directory: %s" % e)
                
        print("SCRIPT_SUCCESS: All sources exported successfully.")
    else:
        raise Exception("Application node not found in project")

def run_import(proj, IMPORT_DIR_PATH):
    print("Starting ST files import...")
    guid_to_obj = {}
    for obj in proj.get_children(True):
        try:
            guid_to_obj[str(obj.guid)] = obj
        except:
            pass
            
    apps = proj.find("Application", True)
    if not apps:
        raise Exception("Application node not found in project")
    app = apps[0]
    
    st_files = []
    for root, dirs, files in os.walk(IMPORT_DIR_PATH):
        for file in files:
            if file.endswith('.st'):
                st_files.append(os.path.join(root, file))
                
    def sort_key(filepath):
        if any(filepath.endswith(x) for x in ['.method.st', '.action.st', '.property.st']):
            return 1
        return 0
    st_files.sort(key=sort_key)
    
    for filepath in st_files:
        guid, decl, impl = parse_st_file(filepath)
        filename = os.path.basename(filepath)
        
        ext = None
        for possible_ext in ['.prg.st', '.fb.st', '.func.st', '.method.st', '.action.st', '.property.st', '.gvl.st', '.dut.st']:
            if filename.endswith(possible_ext):
                ext = possible_ext
                break
        if not ext:
            continue
            
        obj_name = filename[:-len(ext)]
        
        obj = None
        if guid and guid in guid_to_obj:
            obj = guid_to_obj[guid]
            
        if obj:
            print("Syncing code for existing object: %s (%s)" % (obj_name, guid))
            if hasattr(obj, 'textual_declaration') and obj.textual_declaration:
                obj.textual_declaration.replace(decl)
            if impl is not None and hasattr(obj, 'textual_implementation') and obj.textual_implementation:
                obj.textual_implementation.replace(impl)
        else:
            print("Creating new object: %s (Type: %s)" % (obj_name, ext))
            
            parts = get_relative_parts(filepath, IMPORT_DIR_PATH)
            parent_parts = parts[:-1]
            if len(parent_parts) > 0 and parent_parts[-1] == obj_name:
                parent_parts = parent_parts[:-1]
                
            if ext in ['.method.st', '.action.st', '.property.st']:
                parent_pou_name = parts[-2]
                parent_pou = None
                parent_folder_parts = parts[:-2]
                parent_container = find_or_create_folder_path(app, parent_folder_parts)
                for child in parent_container.get_children(False):
                    if child.get_name() == parent_pou_name:
                        parent_pou = child
                        break
                if not parent_pou:
                    raise Exception("Parent POU %s not found for method %s" % (parent_pou_name, obj_name))
                
                if ext == '.method.st':
                    new_obj = parent_pou.create_method(obj_name)
                elif ext == '.property.st':
                    new_obj = parent_pou.create_property(obj_name, 'BOOL')
                elif ext == '.action.st':
                    if hasattr(parent_pou, 'create_action'):
                        new_obj = parent_pou.create_action(obj_name)
                    else:
                        print("WARN: Parent doesn't support create_action, skipping.")
                        new_obj = None
            else:
                parent_container = find_or_create_folder_path(app, parent_parts)
                if ext == '.prg.st':
                    new_obj = parent_container.create_pou(obj_name, PouType.Program)
                elif ext == '.fb.st':
                    new_obj = parent_container.create_pou(obj_name, PouType.FunctionBlock)
                elif ext == '.func.st':
                    new_obj = parent_container.create_pou(obj_name, PouType.Function)
                elif ext == '.gvl.st':
                    new_obj = parent_container.create_gvl(obj_name)
                elif ext == '.dut.st':
                    new_obj = parent_container.create_dut(obj_name)
                else:
                    new_obj = None
                    
            if new_obj:
                if hasattr(new_obj, 'textual_declaration') and new_obj.textual_declaration:
                    new_obj.textual_declaration.replace(decl)
                if impl is not None and hasattr(new_obj, 'textual_implementation') and new_obj.textual_implementation:
                    new_obj.textual_implementation.replace(impl)
                guid_to_obj[str(new_obj.guid)] = new_obj
                print("Created successfully: %s" % obj_name)
                
    print("Saving project changes...")
    proj.save()
    print("SCRIPT_SUCCESS: Sync completed successfully.")

def run_compile(proj):
    apps = proj.find("Application", True)
    if not apps:
        raise Exception("Application node not found in project")
    app = apps[0]
    print("Application found: %s. Rebuilding..." % app.get_name())
    app.clean()
    build_result = app.build()
    print("Build command completed.")
    
    if build_result:
        has_errors = False
        print("Build Messages:")
        for msg in build_result.messages:
            sev = "INFO"
            if msg.severity == 1:
                sev = "ERROR"
                has_errors = True
            elif msg.severity == 2:
                sev = "WARNING"
            print("[%s] %s" % (sev, msg.text))
            
        if has_errors:
            raise Exception("Compilation completed with errors.")
    print("SCRIPT_SUCCESS: Compilation completed successfully.")

def handle_request(req):
    action = req.get("action")
    sources_path = req.get("sources_path")
    add_context = req.get("add_context", False)
    
    proj = script_engine.projects.primary
    if not proj:
        raise Exception("No active project opened in Abak.IDE!")
        
    if action == "export":
        run_export(proj, sources_path, add_context)
    elif action == "import":
        run_import(proj, sources_path)
    elif action == "compile":
        run_compile(proj)
    else:
        raise Exception("Unknown action: %s" % action)

# Start main timer loop
import clr
clr.AddReference("System.Windows.Forms")
import System.Windows.Forms
from System.Windows.Forms import Timer

# Stop previous timer if it exists in the shared sys module
if hasattr(sys, 'active_ipc_timer'):
    print("Stopping previous IPC timer...")
    try:
        sys.active_ipc_timer.Stop()
        sys.active_ipc_timer.Dispose()
    except Exception as e:
        print("Error stopping previous timer: %s" % e)

# Remove orphaned res file if any
if os.path.exists(res_path):
    try: os.remove(res_path)
    except: pass

def on_tick(sender, event_args):
    # Temporarily disable timer to prevent re-entrancy
    sender.Stop()
    
    should_resume = True
    try:
        if os.path.exists(req_path):
            # Give a small margin for file write buffer
            time.sleep(0.05)
            
            # Start logging redirect
            logger = Logger(log_path)
            sys.stdout = logger
            
            success = False
            error_msg = ""
            
            try:
                print("\n>>> [%s] IPC Request received!" % time.strftime("%H:%M:%S"))
                with open(req_path, "r") as f:
                    req = json.load(f)
                
                action = req.get("action")
                if action == "stop":
                    success = True
                    should_resume = False
                    print("IPC Server stopped via stop command.")
                else:
                    handle_request(req)
                    success = True
            except Exception as e:
                error_msg = str(e)
                print("SCRIPT_ERROR: %s" % error_msg)
                traceback.print_exc()
            finally:
                # Restore console stdout
                sys.stdout = logger.terminal
                logger.close()
                
                # Write response
                res = {"success": success, "error": error_msg}
                with open(res_path, "w") as f:
                    json.dump(res, f)
                
                # Delete request file to acknowledge
                try: os.remove(req_path)
                except: pass
                
                print(">>> Done! Result written to Temp. Waiting for next request...")
    finally:
        if should_resume:
            sender.Start()
        else:
            sender.Dispose()
            if hasattr(sys, 'active_ipc_timer'):
                delattr(sys, 'active_ipc_timer')

# Create and start the new timer
ipc_timer = Timer()
ipc_timer.Interval = 300  # 300 ms
ipc_timer.Tick += on_tick
sys.active_ipc_timer = ipc_timer
ipc_timer.Start()

print("--------------------------------------------------")
print("CODESYS IPC Server Listener is running via .NET Timer...")
print("The IDE GUI will remain fully responsive!")
print("To stop the server, run the script again or send stop command.")
print("--------------------------------------------------")

