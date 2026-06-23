# CODESYS MCP Connection & Workspace Info

This file documents the local CODESYS project path and connection details so that any AI agent or developer can quickly connect to the project.

## Project Details

- **Target Project File**: `D:\Projects\CEX_15\апп 511\PLC\abak_app511_10v 0.0.4.project`
- **MCP Server Name**: `codesys_local`

## Quick Connection Commands

To open the project or query its structure via the MCP server:

### 1. Open the project
Use the `open_project` tool from the `codesys_local` server:
```json
{
  "filePath": "D:/Projects/CEX_15/апп 511/PLC/abak_app511_10v 0.0.4.project"
}
```

### 2. View Project Structure
Read the MCP resource:
`codesys://project/D%3A%2FProjects%2FCEX_15%2F%D0%B0%D0%BF%D0%BF%20511%2FPLC%2Fabak_app511_10v%200.0.4.project/structure`

---

## Technical Note: Performance & Latency

### Why are commands slow (15–30+ seconds)?
The `@codesys/mcp-toolkit` is designed as a **stateless batch runner**:
1. Every time a tool is called or a resource is read, the Node.js wrapper spawns a fresh `CODESYS.exe --noUI --runscript="..."` process.
2. **Launch overhead**: CODESYS is a heavy IDE. Initializing its modules, libraries, and scripting engine in headless mode takes **10–25 seconds** on most machines.
3. **Load overhead**: Loading a large project file takes additional time.
4. Once loaded, the script completes in milliseconds, and the CODESYS process exits.

Therefore, expect each tool call to take some time. This is normal and is caused by the way the CODESYS Scripting Engine CLI operates.
