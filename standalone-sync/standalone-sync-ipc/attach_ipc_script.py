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
    
    # Мгновенный вызов диалога выполнения скрипта через горячую клавишу
    # (Требует предварительной настройки в Abak.IDE: Инструменты -> Кастомизация -> Клавиатура -> Скрипты -> Выполнить скрипт)
    auto.SendKeys('{Ctrl}{Shift}{F7}')
    time.sleep(0.3)
    
    # Вставляем путь через буфер обмена
    auto.SetClipboardText(script_path)
    auto.SendKeys('{Ctrl}v')
    time.sleep(0.1)
    auto.SendKeys('{Enter}')
    
    print("Automation executed successfully via hotkey.")

if __name__ == "__main__":
    main()
