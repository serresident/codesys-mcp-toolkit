# -*- coding: utf-8 -*-
import sys
import scriptengine as script_engine

try:
    proj = script_engine.projects.open(r"D:\Projects\CEX_15\апп 511\PLC\abak_app511_10v 0.0.4.project")
    apps = proj.find("Application", True)
    app = apps[0]
    
    # Find FB_InfluxBuffer
    fbs = proj.find("FB_InfluxBuffer", True)
    if fbs:
        fb = fbs[0]
        print("FB Name: %s, type GUID: %s" % (fb.get_name(), fb.type))
        for child in fb.get_children(False):
            print("Child Name: %s, type GUID: %s" % (child.get_name(), child.type))
            
    sys.exit(0)
except Exception as e:
    print("Error: " + str(e))
    sys.exit(1)
