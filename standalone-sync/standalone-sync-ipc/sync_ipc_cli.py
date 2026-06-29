# -*- coding: utf-8 -*-
# sync_ipc_cli.py
# Command Line Interface client to communicate with Abak.IDE running ipc_listener.py
# Useful for both human developers and AI agents (Antigravity) to sync code over IPC.

import sys
import os
import json
import time
import tempfile
import argparse

temp_dir = tempfile.gettempdir()
req_path = os.path.join(temp_dir, "codesys_ipc_req.json")
res_path = os.path.join(temp_dir, "codesys_ipc_res.json")
log_path = os.path.join(temp_dir, "codesys_ipc.log")

def main():
    parser = argparse.ArgumentParser(description="CODESYS IPC Sync CLI Client")
    parser.add_argument("--action", required=True, choices=["export", "import", "compile", "stop"], help="Action to perform")
    parser.add_argument("--sources", help="Custom path to ST sources directory")
    parser.add_argument("--add-context", action="store_true", default=True, help="Add server and context folder during export (default: True)")
    parser.add_argument("--no-context", dest="add_context", action="store_false", help="Do not add server and context folder during export")
    args = parser.parse_args()

    action = args.action
    sources_path = args.sources

    # Resolve default sources directory if not specified
    if not sources_path and action in ["export", "import"]:
        curr_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sources_path = os.path.join(curr_dir, "sources_st", "511_05")
        if not os.path.exists(sources_path):
            print("ERROR: Default sources path 'sources_st/511_05' not found. Please provide --sources.")
            sys.exit(1)

    if sources_path:
        sources_path = os.path.abspath(sources_path)

    print("=== STARTING IPC ACTION: %s ===" % action.upper())
    if sources_path:
        print("Sources Directory: %s" % sources_path)

    # Clean up old files to avoid state contamination
    if os.path.exists(res_path):
        try: os.remove(res_path)
        except: pass
    if os.path.exists(log_path):
        try: os.remove(log_path)
        except: pass

    # Write request file
    req_data = {
        "action": action,
        "sources_path": sources_path,
        "add_context": args.add_context
    }
    
    try:
        with open(req_path, "w") as f:
            json.dump(req_data, f)
    except Exception as e:
        print("ERROR: Failed to write request file: %s" % e)
        sys.exit(1)

    print("Request sent to Abak.IDE. Waiting for execution...")

    log_offset = 0
    success = False
    
    try:
        while True:
            # Poll log file
            if os.path.exists(log_path):
                try:
                    with open(log_path, "r") as f:
                        file_len = os.path.getsize(log_path)
                        if file_len < log_offset:
                            log_offset = 0
                        f.seek(log_offset)
                        new_data = f.read()
                        log_offset = f.tell()
                    if new_data:
                        sys.stdout.write(new_data)
                        sys.stdout.flush()
                except Exception:
                    pass

            # Check response
            if os.path.exists(res_path):
                time.sleep(0.1) # short flush delay
                if os.path.exists(log_path):
                    try:
                        with open(log_path, "r") as f:
                            f.seek(log_offset)
                            new_data = f.read()
                        if new_data:
                            sys.stdout.write(new_data)
                            sys.stdout.flush()
                    except Exception:
                        pass
                
                try:
                    with open(res_path, "r") as f:
                        res = json.load(f)
                    success = res.get("success", False)
                    error_err = res.get("error", "")
                    
                    if success:
                        print("\n=== IPC ACTION COMPLETED SUCCESSFULLY ===")
                    else:
                        print("\n=== IPC ACTION FAILED: %s ===" % error_err)
                except Exception as e:
                    print("\nERROR: Failed to read response: %s" % e)
                finally:
                    # Clean up response/log files
                    try: os.remove(res_path)
                    except: pass
                    try: os.remove(log_path)
                    except: pass
                break
                
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\nCLI operation interrupted by user.")
        sys.exit(130)

    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
