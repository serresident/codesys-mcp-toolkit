# -*- coding: utf-8 -*-
import sys
import os
import scriptengine as script_engine

output_file = r"c:\Users\ess2\source\codesys-mcp-toolkit\types_output.txt"
with open(output_file, "w") as f:
    try:
        proj = script_engine.projects.open(r"D:\Projects\CEX_15\апп 511\PLC\abak_app511_10v 0.0.4.project")
        apps = proj.find("Application", True)
        if not apps:
            f.write("Application not found\n")
            sys.exit(1)
        app = apps[0]
        
        f.write("=== Application Children ===\n")
        for child in app.get_children(True): # recursive
            name = child.get_name()
            try:
                t_guid = str(child.type)
            except:
                t_guid = "unknown"
            typename = type(child).__name__
            f.write("Name: %s | TypeName: %s | GUID: %s\n" % (name, typename, t_guid))
        
        f.write("SUCCESS\n")
        sys.exit(0)
    except Exception as e:
        f.write("Error: %s\n" % str(e))
        sys.exit(1)
