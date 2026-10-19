shader_type spatial;
// A pool of molten lava (v0.9.21): cooled crust plates drift on it, split by glowing cracks that open and close,
// bubbles swell and burst, and the heat breathes. Local coordinates: the pool's disc, radius `radius`.
render_mode cull_back, diffuse_burley, specular_schlick_ggx;
uniform float radius = 1.0;
uniform float seed = 0.0;
uniform float speed = 1.0;
uniform vec3 hot : source_color = vec3(1.0, 0.78, 0.25);
uniform vec3 warm : source_color = vec3(1.0, 0.32, 0.04);
uniform vec3 crust : source_color = vec3(0.07, 0.045, 0.035);
uniform float glow = 2.2;
varying vec2 lp;
void vertex() {
	lp = VERTEX.xz / radius;
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
float fbm(vec2 p) {
	return vnoise(p) * 0.55 + vnoise(p * 2.03 + 3.1) * 0.3 + vnoise(p * 4.1 + 7.7) * 0.15;
}
// Voronoi with wandering cell centres: returns (F1, F2) distances
vec2 plates(vec2 p, float t) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	float d1 = 8.0;
	float d2 = 8.0;
	for (int y = -1; y <= 1; y++) {
		for (int x = -1; x <= 1; x++) {
			vec2 g = vec2(float(x), float(y));
			vec2 o = h22(i + g);
			o = 0.5 + 0.38 * sin(t * 0.35 + 6.2831 * o);
			float d = length(g + o - f);
			if (d < d1) {
				d2 = d1;
				d1 = d;
			} else if (d < d2) {
				d2 = d;
			}
		}
	}
	return vec2(d1, d2);
}
void fragment() {
	float t = TIME * speed + seed * 17.0;
	float r = length(lp);
	// slow convection: the surface creeps outward from the middle and turns a little
	float ang = 0.05 * t;
	mat2 rot = mat2(vec2(cos(ang), sin(ang)), vec2(-sin(ang), cos(ang)));
	vec2 q = rot * lp * (1.0 - 0.06 * sin(t * 0.2));
	vec2 warp = vec2(fbm(q * 1.6 + vec2(t * 0.05, 0.0)), fbm(q * 1.6 + vec2(4.3, t * 0.04))) - 0.5;
	vec2 pp = q * 3.4 + warp * 0.9 + seed;
	vec2 v = plates(pp, t);
	float seam = v.y - v.x;                                   // 0 on a crack between two plates
	float heat = fbm(q * 2.2 - vec2(t * 0.07, t * 0.05) + seed);   // where the crust is thin and the glow breaks through
	float width = 0.07 + 0.24 * smoothstep(0.3, 0.75, heat) + 0.06 * smoothstep(0.55, 0.95, r);
	float crack = 1.0 - smoothstep(width * 0.3, width, seam);
	// thin crust: the glow shows through the plates where the lava is hottest
	float plate_glow = smoothstep(0.45, 0.9, heat) * (0.3 + 0.35 * fbm(pp * 2.3 + 5.0));
	// bubbles: in cells of their own, each swells for a while, then bursts into a ring
	vec2 bp = lp * 2.6 + seed * 3.0;
	vec2 bi = floor(bp);
	vec2 bf = fract(bp) - 0.5;
	float bub = 0.0;
	float ring = 0.0;
	float bh = h21(bi + 11.0);
	if (bh > 0.45) {
		float ph = fract(t * (0.18 + 0.12 * bh) + bh * 7.0);
		vec2 c = (h22(bi + 5.0) - 0.5) * 0.4;
		float d = length(bf - c);
		if (ph < 0.82) {                                     // swelling dome, brightest on top
			float rad = 0.05 + 0.2 * (ph / 0.82);
			bub = sqrt(clamp(1.0 - d / rad, 0.0, 1.0)) * smoothstep(0.0, 0.15, ph);
		} else {                                             // burst: a soft flash that spreads and fades
			float k = (ph - 0.82) / 0.18;
			ring = (1.0 - smoothstep(0.0, 0.25 + 0.25 * k, d)) * (1.0 - k) * (1.0 - k);
		}
	}
	float molten = clamp(max(crack, plate_glow) + bub * 0.9 + ring * 0.8, 0.0, 1.0);
	// the rim: crust piles up and cools at the edge
	float rim = smoothstep(0.78, 1.0, r);
	molten *= 1.0 - rim * 0.85;
	float flick = 0.85 + 0.15 * sin(t * 2.3 + heat * 9.0);
	vec3 lava = mix(warm, hot, clamp(heat * 1.3 - 0.2 + bub * 0.6, 0.0, 1.0));
	vec3 crustc = crust * (0.8 + 0.5 * fbm(pp * 1.7)) * (1.0 + 2.5 * (1.0 - smoothstep(0.0, width * 2.5, seam)) * (1.0 - rim));
	ALBEDO = mix(crustc, lava * 0.35, molten);
	EMISSION = lava * glow * molten * flick + warm * 0.18 * (1.0 - rim) * (1.0 - molten);
	ROUGHNESS = mix(0.85, 0.35, molten);
	SPECULAR = 0.3;
	ALPHA = 1.0 - smoothstep(0.93, 1.0, r);
}
