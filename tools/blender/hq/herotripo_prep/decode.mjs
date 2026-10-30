// node decode.mjs IN.glb OUT.glb : decode EXT_meshopt_compression and dequantize (KHR_mesh_quantization) to plain float glTF.
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { dequantize } from '@gltf-transform/functions';
import { MeshoptDecoder } from 'meshoptimizer';
await MeshoptDecoder.ready;
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'meshopt.decoder': MeshoptDecoder });
const doc = await io.read(process.argv[2]);
await doc.transform(dequantize());
for (const ext of doc.getRoot().listExtensionsUsed()) {
  if (['EXT_meshopt_compression', 'KHR_mesh_quantization'].includes(ext.extensionName)) ext.dispose();
}
await io.write(process.argv[3], doc);
console.log('ok', process.argv[3]);
