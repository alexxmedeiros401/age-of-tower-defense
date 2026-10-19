shader_type spatial;
// A robot's energy shield (v0.9.27): a glowing rim where the shell turns away from the camera, nearly clear where it
// faces it (so the robot inside stays readable), with faint bands drifting up it. game.gd sets `strength` from how much
// shield is left.
render_mode unshaded, cull_back, depth_draw_never, blend_add, shadows_disabled;
uniform vec4 col : source_color = vec4(0.35, 0.85, 1.0, 1.0);
uniform float strength = 1.0;
varying vec3 wp;

void vertex() {
	wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	float rim = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 2.2);
	float bands = 0.5 + 0.5 * sin(wp.y * 12.0 - TIME * 3.0);
	ALBEDO = col.rgb;
	ALPHA = clamp((0.04 + 0.8 * rim + 0.18 * bands * rim) * strength, 0.0, 1.0);
}
