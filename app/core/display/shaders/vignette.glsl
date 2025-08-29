//!HOOK OUTPUT
//!BIND HOOKED
//!DESC simple vignette

vec4 hook() {
    vec2 uv = HOOKED_pos;
    vec2 center = vec2(0.5, 0.5);
    float dist = distance(uv, center);

    float radius = 0.55;
    float softness = 0.75;

    float vignette = smoothstep(radius - softness, radius, dist); // 0=center, 1=edge
    vec4 color = HOOKED_texOff(0);
    return vec4(color.rgb * (1.0 - vignette), color.a);
}
