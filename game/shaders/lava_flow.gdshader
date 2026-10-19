shader_type spatial;
// Glowing lava on scenery (v0.9.21): the volcano's crater pool and the lava running down its sides, glowing seams in
// basalt, embers in charred trees. Replaces the scenery kit's flat "glow lava" material. On slopes molten streaks and
// dark crust slide downhill; on flat parts (the crater pool) crust plates drift on the melt with glowing cracks;
// everywhere it breathes and flickers. World-space, so it works on the kit's MultiMeshes.
render_mode diffuse_burley, specular_schlick_ggx;
uniform vec3 hot : source_color = vec3(1.0, 0.78, 0.25);
uniform vec3 warm : source_color = vec3(1.0, 0.28, 0.03);
uniform vec3 crust : source_color = vec3(0.09, 0.04, 0.025);
uniform float glow = 1.35;
uniform float flow = 0.55;
uniform bool plates = false;                 // crust plates on flat parts (the volcano's crater pool)
varying vec3 wp;
varying vec3 wn;

void vertex() {
	wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wn = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

vec2 h22(vec2 p) {
	p = vec2(dot(p, vec2(127.1, 311.7)), dot(p, vec2(269.5, 183.3)));
	return fract(sin(p) * 43758.5453);
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

// distance to the nearest crack between drifting crust plates (Voronoi F2 - F1)
float seams(vec2 p, float t) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	float d1 = 8.0;
	float d2 = 8.0;
	for (int y = -1; y <= 1; y++) {
		for (int x = -1; x <= 1; x++) {
			vec2 g = vec2(float(x), float(y));
			vec2 o = 0.5 + 0.38 * sin(t * 0.35 + 6.2831 * h22(i + g));
			float d = length(g + o - f);
			if (d < d1) {
				d2 = d1;
				d1 = d;
			} else if (d < d2) {
				d2 = d;
			}
		}
	}
	return d2 - d1;
}

void fragment() {
	float t = TIME;
	// pooled or running? Judged from the true face normal: the kit's pool shares smoothed normals with the crater wall
	vec3 fn = normalize(cross(dFdx(wp), dFdy(wp)));
	float slope = clamp(1.0 - abs(fn.y), 0.0, 1.0);
	float breathe = 0.82 + 0.18 * sin(t * 1.3 + wp.x * 0.7 + wp.z * 0.5);
	float molten;
	float heat;
	if (slope > 0.12 || !plates) {
		// running downhill: streaks along the slope; crust lumps ride down on the melt
		vec2 side = normalize(vec2(wn.x, wn.z) + vec2(1e-4, 0.0));
		float across = dot(wp.xz, vec2(-side.y, side.x));
		vec2 q = vec2(across * 1.2, wp.y * 1.1 + t * flow);
		float n = vnoise(q) * 0.65 + vnoise(q * 2.1 + 4.1) * 0.35;
		heat = smoothstep(0.2, 0.85, n);                       // pulses of hotter melt sliding down
		molten = 1.0 - smoothstep(0.3, 0.1, n) * 0.55;          // now and then a cooler, darker lump
	} else {
		// pooled: crust plates drift on the melt, split by glowing cracks
		vec2 q = wp.xz * 2.4 + vec2(sin(t * 0.11), cos(t * 0.09)) * 0.6;
		float s = seams(q, t);
		float n = vnoise(wp.xz * 1.3 - t * 0.08);
		heat = smoothstep(0.3, 0.8, n);
		molten = max(1.0 - smoothstep(0.05, 0.14 + 0.22 * heat, s), smoothstep(0.35, 0.75, n) * 0.85);
	}
	vec3 col = mix(warm, hot, heat);
	ALBEDO = mix(crust, col * 0.25, molten);
	EMISSION = col * glow * (0.45 + 0.75 * heat) * breathe * molten + warm * 0.12 * (1.0 - molten);
	ROUGHNESS = 0.9;
	SPECULAR = 0.15;
}
