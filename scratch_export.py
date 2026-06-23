# -*- coding: utf-8 -*-
import sys
import scriptengine as script_engine
import os

try:
    proj_path = r"D:\Projects\CEX_15\апп 511\PLC\abak_app511_10v 0.0.4.project"
    print("Opening project: " + proj_path)
    proj = script_engine.projects.open(proj_path)
    if not proj:
        raise Exception("Failed to open project")
        
    print("Searching for Application...")
    apps = proj.find("Application", True)
    if not apps:
        raise Exception("No Application found")
        
    app = apps[0]
    xml_path = r"D:\Projects\CEX_15\апп 511\PLC\export_test.xml"
    print("Exporting Application to XML: " + xml_path)
    
    # We export the Application recursively with folder structure and plain text declarations
    proj.export_xml([app], xml_path, recursive=True, export_folder_structure=True, declarations_as_plaintext=True)
    print("SCRIPT_SUCCESS: Export completed successfully!")
    sys.exit(0)
except Exception as e:
    print("SCRIPT_ERROR: " + str(e))
    sys.exit(1)
