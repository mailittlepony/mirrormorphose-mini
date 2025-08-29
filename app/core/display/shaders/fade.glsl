//!PARAM fade
//!DESC Fade in or out intensity
//!TYPE float
//!MINIMUM 0
//!MAXIMUM 1
0.0

//!HOOK OUTPUT
//!BIND HOOKED

vec4 hook() {
    vec4 color = HOOKED_texOff(0);
    color.rgb *= fade;
    return color;
}
