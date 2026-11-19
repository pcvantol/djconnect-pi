#version 440
layout(location = 0) in vec2 qt_TexCoord0;
layout(location = 0) out vec4 fragColor;
layout(std140, binding = 0) uniform buf {
    mat4 qt_Matrix;
    float qt_Opacity;
    vec2 dimensions;
    float radius;
    float strength;
    vec4 backdropRect;
    float tintAmount;
    float edgeLight;
    vec4 materialTint;
};
layout(binding = 1) uniform sampler2D source;
float distanceToEdge(vec2 p) {
    vec2 q = abs(p) - dimensions * 0.5 + vec2(radius);
    return length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - radius;
}
void main() {
    vec2 p = (qt_TexCoord0 - 0.5) * dimensions;
    float d = distanceToEdge(p);
    vec2 n = normalize(vec2(distanceToEdge(p+vec2(1,0))-distanceToEdge(p-vec2(1,0)), distanceToEdge(p+vec2(0,1))-distanceToEdge(p-vec2(0,1))) + vec2(0.0001));
    float rim = smoothstep(-46.0, -2.0, d);
    vec2 uv = clamp(qt_TexCoord0 - n * rim * strength / dimensions, vec2(0.001), vec2(0.999));
    vec4 base = texture(source, backdropRect.xy + uv * backdropRect.zw);
    vec3 col = mix(base.rgb, materialTint.rgb, tintAmount);
    float light = pow(max(dot(n, normalize(vec2(-0.5,-1.0))),0.0), 2.0);
    float edge = exp(-abs(d+1.3) * 0.65);
    col += vec3(0.50,0.62,0.85) * edge * (0.12+edgeLight*light);
    col += vec3(0.07,0.06,0.13) * rim * light;
    float alpha = 1.0 - smoothstep(-1.0, 1.0, d);
    fragColor = vec4(col * alpha, alpha) * qt_Opacity;
}
