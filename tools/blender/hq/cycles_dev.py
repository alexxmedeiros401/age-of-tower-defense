"""Which Cycles device to render and bake on: the GPU when the AOTD_GPU environment variable names a Cycles compute
backend (CUDA, OPTIX, HIP, ONEAPI, METAL) and a device of that kind is present (the linked PC's job runner sets it),
else the CPU, as always. Turns the backend's devices on in the preferences each call (a factory reset clears them)."""
import os
import bpy


def device():
    want = os.environ.get("AOTD_GPU", "").strip().upper()
    if not want:
        return "CPU"
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = want
        prefs.get_devices()
        found = False
        for d in prefs.devices:
            d.use = d.type == want
            found = found or d.use
        if found:
            return "GPU"
        print("[cycles_dev] no %s device, rendering on the CPU" % want, flush=True)
    except Exception as e:
        print("[cycles_dev] %s unavailable (%s), rendering on the CPU" % (want, e), flush=True)
    return "CPU"


def use(sc=None):
    """Point the scene's Cycles at device()."""
    sc = sc or bpy.context.scene
    sc.cycles.device = device()
    return sc.cycles.device
