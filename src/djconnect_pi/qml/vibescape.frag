#version 440
// Native GLSL port of Apple3c223b9 VibeScape.metal: local procedural visuals.
layout(location=0) in vec2 qt_TexCoord0;
layout(location=0) out vec4 fragColor;
layout(std140,binding=0) uniform buf {
    mat4 qt_Matrix;
    float qt_Opacity;
    vec4 resolutionTime;
    vec4 composition;
    vec4 paletteMotion;
    vec4 shape;
    vec4 secondary;
    vec4 accent;
    vec4 touch0;
    vec4 touch1;
    vec4 touch2;
    vec4 touch3;
};
float smoothUnion(float a, float b, float k) {
    float h = clamp(0.5 + 0.5 * (b-a)/k, 0.0, 1.0);
    return mix(b,a,h) - k*h*(1.0-h);
}
float screenImpulse(vec2 point, vec4 touch) {
    if (touch.w < 0.5) return 0;
    float radius = length(point-touch.xy);
    float falloff = exp(-radius*radius/0.045);
    // One soft dent instead of alternating rings. Repeated nearby inputs must
    // not produce bright/dark rebounds while a finger rests on the liquid.
    float onset = touch.w > 1.0 ? 0.08 : 0.16;
    float envelope = smoothstep(0.0,onset,touch.z)*exp(-touch.z*1.8)
                   *(1.0-smoothstep(2.0,2.6,touch.z));
    return -0.075*touch.w*falloff*envelope;
}
float combinedImpulse(vec2 point) {
    float value = screenImpulse(point,touch0)+screenImpulse(point,touch1)
                +screenImpulse(point,touch2)+screenImpulse(point,touch3);
    // Smooth saturation also keeps overlapping swipe samples from stacking
    // into a large, rapidly changing surface normal.
    float limit = 0.10*max(1.0,max(max(touch0.w,touch1.w),max(touch2.w,touch3.w)));
    return limit*tanh(value/limit);
}
float impulse(vec3 p) {
    float eyeZ = 4.1+shape.x*0.3;
    vec2 projected = p.xy*(2.6/1.05)/max(0.5,eyeZ-p.z);
    return combinedImpulse(projected);
}
float field(vec3 p) {
    vec3 original = p;
    float t = resolutionTime.z;
    vec4 c = composition;
    float strength = shape.z;
    p += strength * 0.20 * sin(p.yzx * (1.8 + shape.w) + vec3(t*0.7,t*0.5,t*0.6));
    float shift = (c.x-0.5)*0.55;
    float a = length(p-vec3(-0.42+shift,0.88+sin(t*0.35)*0.12,0.0))-0.72;
    float b = length(p-vec3(0.06+shift,0.51,0.08+cos(t*0.43)*0.12))-(0.50+c.y*0.10);
    float drip = length((p-vec3(0.20+shift,0.10+sin(t*0.46)*0.08,0.04))*vec3(1,0.85,1)) - (0.23+c.z*0.10);
    float liquid = smoothUnion(smoothUnion(a,b,0.40),drip,0.36);
    // Cropped foreground pools make this a full canvas, not an isolated knot.
    float lower = length(p-vec3(-0.95,-2.05+sin(t*0.20)*0.12,0.25))-1.20;
    float upper = length(p-vec3(1.38,1.78,-0.30))-0.96;
    liquid = min(liquid,min(lower,upper));
    float bubble = length(p-vec3(0.70+sin(t*0.54+c.w*6)*0.10,1.17,0.40))-0.13;
    float bubble2 = length(p-vec3(0.73,-1.06+cos(t*0.48)*0.12,0.55))-(0.19+c.w*0.06);
    float bubble3 = length(p-vec3(-0.80+cos(t*0.40)*0.08,-0.10,0.45))-0.09;
    float surface = min(liquid,min(bubble,min(bubble2,bubble3)));
    return surface + impulse(original);
}
vec3 backdrop(vec2 uv) {
    float t = resolutionTime.z;
    vec3 primary = pow(paletteMotion.xyz,vec3(2.2));
    vec3 secondary = pow(secondary.xyz,vec3(2.2));
    vec3 accent = pow(accent.xyz,vec3(2.2));
    vec3 col = mix(secondary,primary,0.25)*0.003;
    float sweep = -0.34 + 0.21*sin(uv.x*2.6+t*0.24) + 0.10*sin(uv.x*5.0-t*0.17);
    sweep += 0.55*combinedImpulse(uv);
    float lane = (uv.y-sweep)*22.0;
    float spacing = abs(fract(lane)-0.5);
    float width = max(22.0/resolutionTime.y,0.025);
    float core = exp(-spacing*spacing/(width*width));
    float glow = exp(-spacing*spacing/0.035);
    float envelope = exp(-pow((uv.y-sweep)/0.34,4.0));
    vec3 ribbon = mix(primary,secondary,smoothstep(-0.65,0.55,uv.x));
    ribbon = mix(ribbon,accent,0.4+0.35*sin(uv.x*2.8+t*0.20));
    col += ribbon*(core*1.5+glow*0.16)*envelope;
    vec2 lower = uv-vec2(-0.5,-0.9);
    vec2 upper = uv-vec2(0.5,0.8);
    col += accent*0.035*exp(-dot(lower,lower)*3.0);
    col += primary*0.035*exp(-dot(upper,upper)*4.0);
    return col;
}
vec3 environment(vec3 r) {
    vec3 primary = pow(paletteMotion.xyz,vec3(2.2));
    vec3 secondary = pow(secondary.xyz,vec3(2.2));
    vec3 accent = pow(accent.xyz,vec3(2.2));
    float sharp = mix(85.0,18.0,shape.y);
    float left = max(dot(r,normalize(vec3(-0.8,0.25,0.6))),0.0);
    float right = max(dot(r,normalize(vec3(0.8,-0.15,0.6))),0.0);
    float top = max(dot(r,normalize(vec3(0.1,0.95,0.15))),0.0);
    vec3 col = secondary*0.014;
    col += primary*(pow(left,sharp)*8.0+pow(left,6.0)*0.5);
    col += secondary*(pow(right,sharp*0.7)*7.0+pow(right,5.0)*0.3);
    col += accent*(pow(top,sharp*0.5)*6.0+pow(top,8.0)*0.35);
    float strip = exp(-pow(r.x+0.45*r.y-0.12,2.0)*150.0);
    float strip2 = exp(-pow(r.x-0.55*r.y+0.22,2.0)*180.0);
    col += primary*strip*4.0 + secondary*strip2*3.2;
    col += vec3(0.7,0.8,1.0)*pow(max(dot(r,normalize(vec3(-0.25,0.5,0.8))),0.0),sharp*2.0)*0.25;
    return col;
}
void main() {
    vec2 uv = (vec2(qt_TexCoord0.x,1.0-qt_TexCoord0.y)*2.0-1.0)*vec2(resolutionTime.x/resolutionTime.y,1.0);
    vec3 eye = vec3(0,0,4.1+shape.x*0.3);
    vec3 ray = normalize(vec3(uv*1.05,-2.6));
    float d = 0; float distance = 0;
    int steps = resolutionTime.w > 0.5 ? 88 : 52;
    for (int i=0;i<steps;++i) {
        d=field(eye+ray*distance);
        if (d<0.0025 || distance>8.0) break;
        distance += max(d*0.60,0.001);
    }
    vec3 color = backdrop(uv);
    if (d<0.006 && distance<8.0) {
        vec3 p=eye+ray*distance;
        const float e=0.002;
        vec3 n=normalize(vec3(field(p+vec3(e,0,0))-field(p-vec3(e,0,0)),
                                 field(p+vec3(0,e,0))-field(p-vec3(0,e,0)),
                                 field(p+vec3(0,0,e))-field(p-vec3(0,0,e))));
        float fresnel=pow(1.0-max(dot(n,-ray),0.0),3.0);
        vec3 reflection=environment(reflect(ray,n));
        vec3 refracted=backdrop(uv+n.xy*0.13);
        color=reflection*0.90+refracted*0.20;
        color+=pow(mix(paletteMotion.xyz,accent.xyz,smoothstep(-1.0,1.0,n.y)),vec3(2.2))*fresnel*0.30;
        color+=secondary.xyz*0.008;
    }
    color *= 0.65+0.35*exp(-dot(uv,uv)*0.25);
    color=color/(color+0.65);
    fragColor = vec4(pow(max(color,vec3(0)),vec3(1.0/2.2)),1) * qt_Opacity;
}
