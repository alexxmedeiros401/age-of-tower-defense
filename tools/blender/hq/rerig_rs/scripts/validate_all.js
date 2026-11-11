// Khronos glTF validator on unit files: npm install gltf-validator; node validate_all.js FILE.glb [FILE2.glb]
// (GLTF_VALIDATOR may point at the module's folder when it is not installed next to this script)
const validator = require(process.env.GLTF_VALIDATOR || 'gltf-validator');
const fs = require('fs');
(async () => {
  for (const f of process.argv.slice(2)) {
    const r = await validator.validateBytes(new Uint8Array(fs.readFileSync(f)), { maxIssues: 500 });
    console.log(f);
    for (const m of r.issues.messages) if (m.severity <= 1) console.log('   ', m.severity, m.code, m.pointer, m.message);
  }
})();
