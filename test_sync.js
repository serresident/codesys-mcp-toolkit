const { spawn } = require('child_process');

console.log("Spawning MCP Server...");
const child = spawn('node', ['./dist/bin.js', '--codesys-path', 'C:\\Program Files (x86)\\Abak.IDE.1.0.0\\CODESYS\\Common\\abak.ide.exe', '--codesys-profile', 'Abak.IDE V1.0.0.0'], { stdio: ['pipe', 'pipe', 'pipe'] });

let responseId = 1;
const pendingRequests = new Map();

child.stderr.on('data', (data) => {
    console.log(`[SERVER LOG] ${data.toString().trim()}`);
});

child.stdout.on('data', (data) => {
    const raw = data.toString().trim();
    console.log(`<- ${raw}`);
    try {
        const parsed = JSON.parse(raw);
        if (parsed.id && pendingRequests.has(parsed.id)) {
            const resolve = pendingRequests.get(parsed.id);
            pendingRequests.delete(parsed.id);
            resolve(parsed);
        }
    } catch (e) {
        // Multi-line JSON or partial logs
    }
});

child.on('exit', (code) => {
    console.log(`Server exited with code ${code}`);
});

function sendRequest(method, params) {
    return new Promise((resolve) => {
        const id = responseId++;
        const msg = { jsonrpc: "2.0", id, method, params };
        pendingRequests.set(id, resolve);
        const payload = JSON.stringify(msg) + '\n';
        console.log(`-> ${payload.trim()}`);
        child.stdin.write(payload);
    });
}

async function runTests() {
    try {
        // 1. Initialize
        await sendRequest("initialize", {
            protocolVersion: "2024-11-05",
            capabilities: {},
            clientInfo: { name: "test-client", version: "1.0" }
        });
        await sendRequest("notifications/initialized", {});

        console.log("\n--- TEST 1: Open project by passing a DIRECTORY path ---");
        const openResult = await sendRequest("tools/call", {
            name: "open_project",
            arguments: {
                filePath: "D:\\Projects\\CEX_15\\апп 511\\PLC"
            }
        });
        console.log("Open project result:", JSON.stringify(openResult, null, 2));

        console.log("\n--- TEST 2: Export project sources into a directory ---");
        const exportResult = await sendRequest("tools/call", {
            name: "export_project_sources",
            arguments: {
                projectFilePath: "D:\\Projects\\CEX_15\\апп 511\\PLC",
                exportDirPath: "D:\\Projects\\CEX_15\\апп 511\\PLC\\project_sources"
            }
        });
        console.log("Export result:", JSON.stringify(exportResult, null, 2));

        // Modify PLC_PRG on disk
        const fs = require('fs');
        const stPath = "D:\\Projects\\CEX_15\\апп 511\\PLC\\project_sources\\PLC_PRG.prg.st";
        let content = fs.readFileSync(stPath, 'utf8');
        console.log("Modifying PLC_PRG.prg.st on disk to add comment...");
        content = content.replace("PROGRAM PLC_PRG", "PROGRAM PLC_PRG // Antigravity Sync Test");
        fs.writeFileSync(stPath, content, 'utf8');

        console.log("\n--- TEST 3: Import project sources from directory ---");
        const importResult = await sendRequest("tools/call", {
            name: "import_project_sources",
            arguments: {
                projectFilePath: "D:\\Projects\\CEX_15\\апп 511\\PLC",
                importDirPath: "D:\\Projects\\CEX_15\\апп 511\\PLC\\project_sources"
            }
        });
        console.log("Import result:", JSON.stringify(importResult, null, 2));

        console.log("\n--- TEST 4: Export again to verify the change was imported ---");
        // Overwrite the file with empty string so we are sure the next export brings the comment from CODESYS
        fs.writeFileSync(stPath, "", 'utf8');
        const exportResult2 = await sendRequest("tools/call", {
            name: "export_project_sources",
            arguments: {
                projectFilePath: "D:\\Projects\\CEX_15\\апп 511\\PLC",
                exportDirPath: "D:\\Projects\\CEX_15\\апп 511\\PLC\\project_sources"
            }
        });
        console.log("Second Export result:", JSON.stringify(exportResult2, null, 2));

        // Read and verify
        const reExportedContent = fs.readFileSync(stPath, 'utf8');
        if (reExportedContent.includes("// Antigravity Sync Test")) {
            console.log("\n>>> SUCCESS: Round-trip synchronization verified! Comment found in re-exported POU. <<<");
        } else {
            console.log("\n>>> FAILURE: Comment not found in re-exported POU. <<<");
        }

        console.log("\nTerminating server...");
        child.kill();
    } catch (err) {
        console.error("Test execution failed:", err);
        child.kill();
    }
}

// Start tests in 1 second
setTimeout(runTests, 1000);
