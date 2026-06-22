import subprocess
import json
import time

def send_msg(proc, msg):
    line = json.dumps(msg)
    print(f"-> {line}")
    proc.stdin.write(line + '\n')
    proc.stdin.flush()

print("Запуск MCP сервера...")
proc = subprocess.Popen(
    ['node', './dist/server.js'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    encoding='utf-8'
)

# 1. Initialize
send_msg(proc, {
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {"name": "test-client", "version": "1.0.0"}
  }
})

line = proc.stdout.readline()
print(f"<- {line.strip()}")

send_msg(proc, {
  "jsonrpc": "2.0",
  "method": "notifications/initialized"
})

print("Запрос на открытие проекта...")
# 2. Call tool
send_msg(proc, {
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "open_project",
    "arguments": {
      "filePath": "D:\\Projects\\CEX_15\\апп 511\\PLC\\abak_app511_10v 0.0.4.project"
    }
  }
})

while True:
    line = proc.stdout.readline()
    if line:
        print(f"<- {line.strip()}")
        if '"id":2' in line or '"id": 2' in line:
            break
    else:
        break

print("Остановка сервера...")
proc.terminate()
