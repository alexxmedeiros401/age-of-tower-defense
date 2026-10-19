shader_type spatial;
// The painted ground of a lava map (v0.9.21). It draws like the plain ground material, but the glowing cracks and
// molten pools painted into it are alive: waves of heat roll slowly through them, they brighten and dim, and they
// shimmer. `lava_mask` marks the painted lava (tools/lava_mask.py writes ground_<map>_lava.png).
render_mode diffuse_burley, specular_schlick_ggx;
uniform sampler2D ground : source_color, filter_linear_mipmap_anisotropic, repeat_disable;
uniform sampler2D lava_mask : filter_linear, repeat_disable;
uniform vec3 tint : source_color = vec3(0.9, 0.9, 0.88);     // the plain ground's albedo colour (sRGB, as there)
uniform vec3 hot : source_color = vec3(1.0, 0.72, 0.22);
uniform vec3 warm : source_color = vec3(1.0, 0.3, 0.04);
uniform float glow = 1.7;
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

void fragment() {
	vec3 g = texture(ground, UV).rgb * tint;
	float m = texture(lava_mask, UV).r;
	ALBEDO = g;
	ROUGHNESS = 1.0;
	if (m > 0.02) {
		float t = TIME;
		vec2 p = wp.xz;
		// slow waves of heat travelling across the field, and a faster flicker along each crack
		float wave = vnoise(p * 0.45 + vec2(t * 0.22, t * 0.11)) * 0.6 + vnoise(p * 1.3 - vec2(t * 0.35, -t * 0.2)) * 0.4;
		float pulse = smoothstep(0.25, 0.85, wave);
		float shimmer = 0.82 + 0.18 * sin(t * 4.0 + vnoise(p * 6.0) * 12.0);
		vec3 col = mix(warm, hot, pulse);
		ALBEDO = mix(g, g * vec3(0.45, 0.32, 0.25), m * 0.75);   // the painted glow dims, so the live glow leads
		EMISSION = col * glow * m * (0.25 + 0.95 * pulse) * shimmer;
	}
}
