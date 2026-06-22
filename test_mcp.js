const { spawn } = require('child_process');

const child = spawn('node', ['./dist/bin.js'], { stdio: ['pipe', 'pipe', 'pipe'] });

child.stderr.on('data', (data) => {
  console.log(`[STDERR] ${data.toString()}`);
});

child.stdout.on('data', (data) => {
  console.log(`[STDOUT] ${data.toString()}`);
});

child.on('exit', (code) => {
  console.log(`Child exited with code ${code}`);
});

// Send initialize request
const initMsg = {
  jsonrpc: "2.0",
  id: 1,
  method: "initialize",
  params: {
    protocolVersion: "2024-11-05",
    capabilities: {},
    clientInfo: { name: "test", version: "1.0" }
  }
};

const msgStr = JSON.stringify(initMsg) + '\n';
console.log(`[STDIN] sending: ${msgStr}`);
child.stdin.write(msgStr);
