//!HOOK OUTPUT
//!BIND HOOKED

vec4 hook() {
    vec4 color = HOOKED_texOff(0);
    return vec4(color.g, color.b, color.r, 1.0);
}
