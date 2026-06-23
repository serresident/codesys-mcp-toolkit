const path = require('path');
const fs = require('fs');
const { executeCodesysScript } = require('./dist/codesys_interop.js');

const defaultCodesysPath = 'C:\\\\Program Files (x86)\\\\Abak.IDE.1.0.0\\\\CODESYS\\\\Common\\\\abak.ide.exe';
const defaultProfileName = 'Abak.IDE V1.0.0.0';

const ENSURE_PROJECT_OPEN_PYTHON_SNIPPET = `
import sys
import scriptengine as script_engine
import os
import time
import traceback

MAX_RETRIES = 3
RETRY_DELAY = 2.0

def ensure_project_open(target_project_path):
    print("DEBUG: Ensuring project is open: %s" % target_project_path)
    normalized_target_path = os.path.normcase(os.path.abspath(target_project_path))

    for attempt in range(MAX_RETRIES):
        print("DEBUG: Ensure project attempt %d/%d for %s" % (attempt + 1, MAX_RETRIES, normalized_target_path))
        primary_project = None
        try:
            primary_project = script_engine.projects.primary
        except Exception as primary_err:
             print("WARN: Error getting primary project: %s. Assuming none." % primary_err)
             primary_project = None

        current_project_path = ""
        project_ok = False

        if primary_project:
            try:
                current_project_path = os.path.normcase(os.path.abspath(primary_project.path))
                print("DEBUG: Current primary project path: %s" % current_project_path)
                if current_project_path == normalized_target_path:
                    print("DEBUG: Target project path matches primary. Checking access...")
                    try:
                         _ = len(primary_project.get_children(False))
                         print("DEBUG: Target project '%s' is primary and accessible." % target_project_path)
                         project_ok = True
                         return primary_project
                    except Exception as access_err:
                         print("WARN: Primary project access check failed for '%s': %s. Will attempt reopen." % (current_project_path, access_err))
                         primary_project = None
                else:
                      print("DEBUG: Primary project is '%s', not the target '%s'." % (current_project_path, normalized_target_path))
                      primary_project = None

            except Exception as path_err:
                  print("WARN: Could not get path of current primary project: %s. Assuming not the target." % path_err)
                  primary_project = None

        if not project_ok:
            if primary_project is None and current_project_path == "":
                print("DEBUG: No primary project detected. Attempting to open target: %s" % target_project_path)
            elif primary_project is None and current_project_path != "":
                 print("DEBUG: Primary project was '%s' but failed access check or needed close. Attempting to open target: %s" % (current_project_path, target_project_path))
            else:
                print("DEBUG: Target project not primary or initial check failed. Attempting to open/reopen: %s" % target_project_path)

            try:
                update_mode = script_engine.VersionUpdateFlags.NoUpdates | script_engine.VersionUpdateFlags.SilentMode
                opened_project = None
                try:
                     print("DEBUG: Calling script_engine.projects.open('%s', update_flags=%s)..." % (target_project_path, update_mode))
                     opened_project = script_engine.projects.open(target_project_path, update_flags=update_mode)

                     if not opened_project:
                          print("ERROR: projects.open returned None for %s on attempt %d" % (target_project_path, attempt + 1))
                     else:
                          print("DEBUG: projects.open call returned an object for: %s" % target_project_path)
                          print("DEBUG: Pausing for stabilization after open...")
                          time.sleep(RETRY_DELAY)
                          recheck_primary = None
                          try: recheck_primary = script_engine.projects.primary
                          except Exception as recheck_primary_err: print("WARN: Error getting primary project after reopen: %s" % recheck_primary_err)

                          if recheck_primary:
                               recheck_path = ""
                               try:
                                   recheck_path = os.path.normcase(os.path.abspath(recheck_primary.path))
                               except Exception as recheck_path_err:
                                   print("WARN: Failed to get path after reopen: %s" % recheck_path_err)

                               if recheck_path == normalized_target_path:
                                    print("DEBUG: Target project confirmed as primary after reopening.")
                                    try:
                                        _ = len(recheck_primary.get_children(False))
                                        print("DEBUG: Reopened project basic access confirmed.")
                                        return recheck_primary
                                    except Exception as access_err_reopen:
                                         print("WARN: Reopened project (%s) basic access check failed: %s." % (normalized_target_path, access_err_reopen))
                               else:
                                    print("WARN: Different project is primary after reopening! Expected '%s', got '%s'." % (normalized_target_path, recheck_path))
                          else:
                                print("WARN: No primary project found after reopening attempt %d!" % (attempt+1))

                except Exception as open_err:
                     print("ERROR: Exception during projects.open call on attempt %d: %s" % (attempt + 1, open_err))
                     traceback.print_exc()

            except Exception as outer_open_err:
                 print("ERROR: Unexpected error during open setup/logic attempt %d: %s" % (attempt + 1, outer_open_err))
                 traceback.print_exc()

        if attempt < MAX_RETRIES - 1:
            print("DEBUG: Ensure project attempt %d did not succeed. Waiting %f seconds..." % (attempt + 1, RETRY_DELAY))
            time.sleep(RETRY_DELAY)
        else:
             print("ERROR: Failed all ensure_project_open attempts for %s." % normalized_target_path)

    raise RuntimeError("Failed to ensure project '%s' is open and accessible after %d attempts." % (target_project_path, MAX_RETRIES))

PROJECT_FILE_PATH_RAW = r"{PROJECT_FILE_PATH}"
try:
    PROJECT_FILE_PATH = PROJECT_FILE_PATH_RAW.decode('utf-8')
except:
    PROJECT_FILE_PATH = PROJECT_FILE_PATH_RAW
`;

const EXPORT_SOURCES_SCRIPT_TEMPLATE = `
import sys, scriptengine as script_engine, os, shutil, traceback

EXPORT_DIR_PATH_RAW = r"{EXPORT_DIR_PATH}"

try:
    EXPORT_DIR_PATH = EXPORT_DIR_PATH_RAW.decode('utf-8')
except:
    EXPORT_DIR_PATH = EXPORT_DIR_PATH_RAW

${ENSURE_PROJECT_OPEN_PYTHON_SNIPPET}

def clean_or_create_dir(path):
    if os.path.exists(path):
        try: shutil.rmtree(path)
        except: pass
    if not os.path.exists(path):
        os.makedirs(path)

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
            from scriptengine import PouType
            pt = node.pou_type
            if pt == PouType.Program: return '.prg.st'
            elif pt == PouType.FunctionBlock: return '.fb.st'
            elif pt == PouType.Function: return '.func.st'
        except Exception:
            decl = ""
            if hasattr(node, 'textual_declaration') and node.textual_declaration:
                decl = node.textual_declaration.text or ""
            import re
            decl_clean = re.sub(r'\\(\\*[\\s\\S]*?\\*\\)', '', decl)
            decl_clean = re.sub(r'//.*', '', decl_clean)
            words = re.findall(r'\\b\\w+\\b', decl_clean.upper())
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
            f.write(("// @OBJECT_ID: " + str(node.guid) + "\\n").encode('utf-8'))
            f.write("// @DECLARATION\\n".encode('utf-8'))
            f.write(decl.encode('utf-8'))
            if impl is not None:
                f.write("\\n\\n// @IMPLEMENTATION\\n".encode('utf-8'))
                f.write(impl.encode('utf-8'))
                
        print("Exported: %s -> %s" % (name, file_path))
        
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

try:
    proj = ensure_project_open(PROJECT_FILE_PATH)
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
            
        print("SCRIPT_SUCCESS: All sources exported successfully.")
        sys.exit(0)
    else:
        raise Exception("Application node not found in project")
except Exception as e:
    error_message = "Error during export: %s" % e
    print(error_message)
    traceback.print_exc()
    print("SCRIPT_ERROR: %s" % error_message)
    sys.exit(1)
`;

const IMPORT_SOURCES_SCRIPT_TEMPLATE = `
import sys, scriptengine as script_engine, os, traceback

IMPORT_DIR_PATH_RAW = r"{IMPORT_DIR_PATH}"

try:
    IMPORT_DIR_PATH = IMPORT_DIR_PATH_RAW.decode('utf-8')
except:
    IMPORT_DIR_PATH = IMPORT_DIR_PATH_RAW

${ENSURE_PROJECT_OPEN_PYTHON_SNIPPET}

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
            decl = "\\n".join(decl_lines)
            continue
        elif line.strip() == "// @IMPLEMENTATION":
            i += 1
            impl_lines = []
            while i < len(lines):
                impl_lines.append(lines[i])
                i += 1
            impl = "\\n".join(impl_lines)
            break
        i += 1
        
    return guid, decl, impl

def get_relative_parts(filepath, base_dir):
    relpath = os.path.relpath(filepath, base_dir)
    normalized = relpath.replace('\\\\', '/')
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

try:
    proj = ensure_project_open(PROJECT_FILE_PATH)
    
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
    
    from scriptengine import PouType
    
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
    sys.exit(0)
except Exception as e:
    error_message = "Error during import: %s" % e
    print(error_message)
    traceback.print_exc()
    print("SCRIPT_ERROR: %s" % error_message)
    sys.exit(1)
`;

function resolveProjectPath(providedPath, workspaceDir) {
    let absPath = path.normalize(path.isAbsolute(providedPath) ? providedPath : path.join(workspaceDir, providedPath));
    try {
        if (fs.existsSync(absPath)) {
            const stats = fs.statSync(absPath);
            if (stats.isDirectory()) {
                const files = fs.readdirSync(absPath);
                const projectFiles = files
                    .filter(file => file.endsWith('.project'))
                    .map(file => {
                        const filePath = path.join(absPath, file);
                        return {
                            path: filePath,
                            mtime: fs.statSync(filePath).mtimeMs
                        };
                    })
                    .sort((a, b) => b.mtime - a.mtime);

                if (projectFiles.length > 0) {
                    console.error(`Resolved directory ${absPath} to latest project: ${projectFiles[0].path}`);
                    return projectFiles[0].path;
                }
            }
        }
    } catch (e) {
        console.error(`Error resolving project path: ${e.message}`);
    }
    return absPath;
}

// CLI Logic
const args = process.argv.slice(2);
const action = args[0];
const projectPathArg = args[1];
const dirArg = args[2];

if (!action || !projectPathArg || !dirArg || (action !== 'export' && action !== 'import')) {
    console.log("Usage: node sync_cli.js <export|import> <project_path_or_folder> <target_dir_for_sources> [--codesys-path <path>] [--codesys-profile <profile>]");
    process.exit(1);
}

// Parse optional args
let codesysPath = defaultCodesysPath;
let codesysProfile = defaultProfileName;

for (let i = 3; i < args.length; i++) {
    if (args[i] === '--codesys-path' && args[i + 1]) {
        codesysPath = args[i + 1];
        i++;
    } else if (args[i] === '--codesys-profile' && args[i + 1]) {
        codesysProfile = args[i + 1];
        i++;
    }
}

const workspace = process.cwd();
const resolvedProj = resolveProjectPath(projectPathArg, workspace);
const resolvedDir = path.normalize(path.isAbsolute(dirArg) ? dirArg : path.join(workspace, dirArg));

console.log(`Running sync CLI...`);
console.log(`Action: ${action.toUpperCase()}`);
console.log(`Resolved Project: ${resolvedProj}`);
console.log(`Resolved Directory: ${resolvedDir}`);
console.log(`CODESYS Path: ${codesysPath}`);
console.log(`CODESYS Profile: ${codesysProfile}`);

let script = "";
if (action === 'export') {
    script = EXPORT_SOURCES_SCRIPT_TEMPLATE
        .replace("{PROJECT_FILE_PATH}", resolvedProj.replace(/\\/g, '\\\\'))
        .replace("{EXPORT_DIR_PATH}", resolvedDir.replace(/\\/g, '\\\\'));
} else {
    script = IMPORT_SOURCES_SCRIPT_TEMPLATE
        .replace("{PROJECT_FILE_PATH}", resolvedProj.replace(/\\/g, '\\\\'))
        .replace("{IMPORT_DIR_PATH}", resolvedDir.replace(/\\/g, '\\\\'));
}

executeCodesysScript(script, codesysPath, codesysProfile)
    .then(result => {
        if (result.success) {
            console.log(`SYNC SUCCESS: ${action.toUpperCase()} finished successfully.`);
            process.exit(0);
        } else {
            console.error(`SYNC ERROR during ${action}:`);
            console.error(result.output);
            process.exit(1);
        }
    })
    .catch(err => {
        console.error("FATAL ERROR:", err);
        process.exit(1);
    });
