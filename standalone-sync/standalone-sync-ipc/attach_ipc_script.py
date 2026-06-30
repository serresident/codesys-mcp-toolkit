import os
import sys
import time

try:
    import uiautomation as auto
except ImportError:
    print("Error: uiautomation module not found. Run 'pip install uiautomation'")
    sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print("Usage: python attach_ipc_script.py <path_to_script>")
        return
        
    script_path = sys.argv[1]
    
    # Increase timeout just in case
    auto.SetGlobalSearchTimeout(5)
    
    # Try finding the window
    window = auto.WindowControl(searchDepth=1, RegexName=r'.*Abak\.IDE.*')
    if not window.Exists():
        print("Error: Abak.IDE window not found.")
        sys.exit(1)
        
    print(f"Found window: {window.Name}")
    window.SetFocus()
    time.sleep(0.1)
    
    # Walk the menu using UIA
    try:
        menu_bar = window.MenuBarControl()
        if menu_bar.Exists(0, 0):
            tools_menu = menu_bar.MenuItemControl(Name="Инструменты")
            if tools_menu.Exists(0, 0):
                tools_menu.Click()
                time.sleep(0.01)
                
                scripts_menu = auto.MenuItemControl(Name="Скрипты")
                if scripts_menu.Exists(0, 0):
                    scripts_menu.Click()
                    time.sleep(0.01)
                    
                    run_script_btn = auto.MenuItemControl(Name="Выполнить скрипт...")
                    if run_script_btn.Exists(0, 0):
                        run_script_btn.Click()
                        time.sleep(0.03)
                        
                        # File dialog - use clipboard to avoid dropped characters
                        auto.SetClipboardText(script_path)
                        auto.SendKeys('{Ctrl}v{Enter}')
                        print("Successfully executed script via UIA.")
                        return
    except Exception as e:
        print(f"UIA Navigation failed: {e}")
        
    # Fallback to SendKeys if UIA fails to find menu items
    print("Falling back to F10 SendKeys method...")
    window.SetFocus()
    time.sleep(0.03)
    
    # Focus menu bar
    auto.SendKeys('{F10}')
    time.sleep(0.03)
    
    # Navigate to Инструменты (8th item) -> Скрипты (7th item) -> Выполнить скрипт (1st)
    for _ in range(7):
        auto.SendKeys('{Right}', waitTime=0.01)
        
    for _ in range(6):
        auto.SendKeys('{Down}', waitTime=0.01)
        
    auto.SendKeys('{Right}')
    time.sleep(0.03)
    
    auto.SendKeys('{Enter}')
    time.sleep(0.1)
    
    # Type path and Enter using clipboard to avoid dropped keystrokes
    auto.SetClipboardText(script_path)
    auto.SendKeys('{Ctrl}v{Enter}')
    print("Fallback executed.")

if __name__ == "__main__":
    main()
