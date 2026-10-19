shader_type spatial;
// The painted ground of a map with rivers and lakes (v0.9.28). It draws like the plain ground material, but the water
// painted into it moves: wavelets drift downstream along each river (the flow map in water_mask's G and B), lakes and
// ponds ripple slowly, the sun glints off the crests and foam trails along the banks. `water_mask` comes from
// tools/water_mask.py (ground_<map>_water.png).
render_mode diffuse_burley, specular_schlick_ggx;
uniform sampler2D ground : source_color, filter_linear_mipmap_anisotropic, repeat_disable;
uniform sampler2D water_mask : filter_linear, repeat_disable;
uniform vec3 tint : source_color = vec3(0.9, 0.9, 0.88);     // the plain ground's albedo colour (sRGB, as there)
uniform float flow_speed = 0.6;       // world units per second the wavelets drift downstream
uniform vec3 glint_col : source_color = vec3(0.92, 0.97, 1.0);
uniform vec3 foam_col : source_color = vec3(0.86, 0.93, 0.94);
varying vec3 wp;

void vertex() {
	wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

float h21(vec2 p) {
	return fract(sin(dot(p, vec2(41.3, 289.1))) * 15731.743);
}

float vnoise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(h21(i), h21(i + vec2(1.0, 0.0)), f.x), mix(h21(i + vec2(0.0, 1.0)), h21(i + vec2(1.0, 1.0)), f.x), f.y);
}

// wavelets: stretched across the flow a little, so they read as ripples on moving water
float wavelets(vec2 p) {
	return vnoise(p * 1.6) * 0.5 + vnoise(p * 3.9 + vec2(3.7, 1.1)) * 0.32 + vnoise(p * 8.7 - vec2(1.3, 5.2)) * 0.18;
}

void fragment() {
	vec3 g = texture(ground, UV).rgb * tint;
	vec4 m = texture(water_mask, UV);
	ALBEDO = g;
	ROUGHNESS = 1.0;
	float w = m.r;
	if (w > 0.02) {
		float t = TIME;
		vec2 p = wp.xz;
		vec2 flow = (m.gb - 0.5) * 2.0;
		float fl = length(flow);
		// flow-map advection: two copies of the wavelets slide downstream half a cycle apart and cross-fade, so the
		// pattern moves with the current for ever without stretching
		float cyc = 1.6;
		float ph0 = fract(t / cyc);
		float ph1 = fract(t / cyc + 0.5);
		float a0 = wavelets(p - flow * flow_speed * cyc * ph0);
		float a1 = wavelets(p - flow * flow_speed * cyc * ph1 + vec2(7.3, 2.1));
		float run = mix(a0, a1, abs(1.0 - 2.0 * ph0));
		// still water: slow ripples drifting two ways
		float pool = wavelets(p * 0.9 + vec2(t * 0.07, t * 0.045)) * 0.55 + wavelets(p * 1.7 - vec2(t * 0.05, -t * 0.08)) * 0.45;
		float r = mix(pool, run, clamp(fl * 2.5, 0.0, 1.0));
		// troughs darker, crests lighter, glints on the sharpest crests (twinkling)
		vec3 wc = g * (0.8 + 0.42 * r);
		float glint = smoothstep(0.74, 0.9, r) * (0.55 + 0.45 * sin(t * 5.0 + p.x * 2.3 - p.y * 1.7));
		wc += glint_col * glint * 0.5;
		// foam along the banks, drifting with the water
		float edge = smoothstep(0.25, 0.55, w) * (1.0 - smoothstep(0.6, 0.92, w));
		wc = mix(wc, foam_col, edge * smoothstep(0.5, 0.72, r) * 0.65);
		ALBEDO = mix(g, wc, w);
		ROUGHNESS = mix(1.0, 0.18, w);
		SPECULAR = mix(0.5, 0.75, w);
	}
}
