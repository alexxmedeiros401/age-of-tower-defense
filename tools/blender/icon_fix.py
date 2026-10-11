"""Icons and portraits render in Blender, which reads vertex colours as linear. v2 models store sRGB vertex
colours (that is what Godot shows), so put a 2.2 gamma between the colour attribute and the shader to make
icons match the game."""
import bpy


def srgb_vertex_colors():
    for m in bpy.data.materials:
        if not m.use_nodes:
            continue
        nt = m.node_tree
        for n in list(nt.nodes):
            if n.bl_idname not in ("ShaderNodeVertexColor", "ShaderNodeAttribute"):
                continue
            for link in list(n.outputs[0].links):
                if link.to_node.bl_idname == "ShaderNodeGamma":
                    continue
                g = nt.nodes.new("ShaderNodeGamma")
                g.inputs[1].default_value = 2.2
                to = link.to_socket
                nt.links.remove(link)
                nt.links.new(n.outputs[0], g.inputs[0])
                nt.links.new(g.outputs[0], to)
