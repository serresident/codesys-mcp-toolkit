const fs = require('fs');
const path = require('path');
const { executeCodesysScript } = require('./dist/codesys_interop.js');

const scriptContent = fs.readFileSync('./scratch_export.py', 'utf8');
const codesysPath = 'C:\\Program Files (x86)\\Abak.IDE.1.0.0\\CODESYS\\Common\\abak.ide.exe';
const profileName = 'Abak.IDE V1.0.0.0';

console.log("Executing script via interop...");
executeCodesysScript(scriptContent, codesysPath, profileName)
    .then(result => {
        console.log("SUCCESS:", result.success);
        console.log("OUTPUT:\n", result.output);
    })
    .catch(err => {
        console.error("ERROR:", err);
    });
