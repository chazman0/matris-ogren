// op4 — HLSL gölgelendiricileri (MIMARI §6.1, D12; F1 iş 1.1). Tek kaynak: derlemede Windows SDK fxc.exe ile vs_5_1 /
// ps_5_1'e derlenir ve bayt kodu op4.exe'ye gömülür (cmake/Golgelendiriciler.cmake); aynı metin çalışma anı yedeği için
// golgelendirici.h'ye (kGolgelendirici) de gömülür. Giriş noktaları vs_* ve ps_* adlı işlevlerdir (kendiliğinden bulunur).
// Renkler sRGB olarak verilir; aydınlatma doğrusal uzayda yapılır ve çıkışta elle gama uygulanır (hedef UNORM).

cbuffer Kare : register(b0)
{
    row_major float4x4 g_vp;
    row_major float4x4 g_tersVp;
    float4 g_goz;       // xyz: göz
    float4 g_isik;      // xyz: ışığa doğru birim yön
    float4 g_ust;       // arka plan üst rengi (sRGB)
    float4 g_alt;       // arka plan alt rengi (sRGB)
    float4 g_izgara;    // x: ince aralık, y: kalın aralık, z: solma başı, w: solma sonu (m)
    float4 g_cizgi;     // x: derinlik öne çekme çarpanı
};

cbuffer Cizim : register(b1)
{
    float4 g_renk;      // sRGB + alfa
};

float3 Dogrusal(float3 c) { return pow(max(c, 0.0), 2.2); }
float3 Ekrana(float3 c) { return pow(saturate(c), 1.0 / 2.2); }

// ---------------------------------------------------------------- katı (kesit) ağları
struct KatiGiris { float3 p : POSITION; float3 n : NORMAL; };
struct KatiAra { float4 p : SV_Position; float3 w : DUNYA; float3 n : NORMAL; };

KatiAra vs_kati(KatiGiris g)
{
    KatiAra o;
    o.p = mul(g_vp, float4(g.p, 1.0));
    o.w = g.p;
    o.n = g.n;
    return o;
}

float4 ps_kati(KatiAra i) : SV_Target
{
    float3 n = normalize(i.n);
    float3 v = normalize(g_goz.xyz - i.w);
    if (dot(n, v) < 0.0) n = -n;                       // iki yüzlü (arka yüz ayıklanmaz)
    float3 l = normalize(g_isik.xyz);
    float3 l2 = normalize(float3(-l.x, -l.y, 0.35));  // dolgu ışığı
    float3 temel = Dogrusal(g_renk.rgb);
    float dif = saturate(dot(n, l));
    float dif2 = saturate(dot(n, l2)) * 0.30;
    float yarim = lerp(0.16, 0.38, n.z * 0.5 + 0.5);  // gök / zemin ortam ışığı
    float3 h = normalize(l + v);
    float par = pow(saturate(dot(n, h)), 56.0) * 0.30;
    float kenar = pow(1.0 - saturate(dot(n, v)), 3.0) * 0.10;  // hafif kenar ışığı: siluet okunurluğu
    float3 c = temel * (yarim + dif * 0.85 + dif2) + par + kenar;
    return float4(Ekrana(c), 1.0);
}

// ---------------------------------------------------------------- çizgiler (kenarlar, çubuk eksenleri)
float4 vs_cizgi(float3 p : POSITION) : SV_Position
{
    float4 c = mul(g_vp, float4(p, 1.0));
    c.z *= g_cizgi.x;  // ters-Z: biraz öne çek (yüzeyle çakışan kenarlar kaybolmasın)
    return c;
}

float4 ps_cizgi() : SV_Target { return g_renk; }

// ---------------------------------------------------------------- tam ekran: arka plan ve sonsuz ızgara
struct TamAra { float4 p : SV_Position; float2 ndc : NDC; };

TamAra vs_tam(uint id : SV_VertexID)
{
    float2 t = float2((id << 1) & 2, id & 2);
    TamAra o;
    o.p = float4(t * float2(2.0, -2.0) + float2(-1.0, 1.0), 0.0, 1.0);
    o.ndc = o.p.xy;
    return o;
}

float4 ps_arka(TamAra i) : SV_Target
{
    float t = saturate(i.ndc.y * 0.5 + 0.5);
    float3 c = lerp(Dogrusal(g_alt.rgb), Dogrusal(g_ust.rgb), t * t * (3.0 - 2.0 * t));
    return float4(Ekrana(c), 1.0);
}

float Cizgi(float2 c, float kalinlik)
{
    float2 w = max(fwidth(c), 1e-7);
    float2 g = abs(frac(c - 0.5) - 0.5) / w;           // en yakın çizgiye piksel uzaklığı
    return 1.0 - saturate(min(g.x, g.y) - 0.5 * kalinlik + 0.5);
}

struct IzgaraCikis { float4 c : SV_Target; float d : SV_Depth; };

IzgaraCikis ps_izgara(TamAra i)
{
    float4 a = mul(g_tersVp, float4(i.ndc, 1.0, 1.0)); a.xyz /= a.w;   // yakın düzlem
    float4 b = mul(g_tersVp, float4(i.ndc, 0.5, 1.0)); b.xyz /= b.w;   // ışın yönü için ikinci nokta
    float3 d = b.xyz - a.xyz;
    if (abs(d.z) < 1e-9) discard;
    float t = -a.z / d.z;
    if (t <= 0.0) discard;
    float3 h = a.xyz + d * t;                                          // z = 0 düzlemi
    float4 k = mul(g_vp, float4(h, 1.0));

    float2 c1 = h.xy / g_izgara.x;
    float2 c5 = h.xy / g_izgara.y;
    float w1 = max(fwidth(c1.x), fwidth(c1.y));
    float w5 = max(fwidth(c5.x), fwidth(c5.y));
    float ince = Cizgi(c1, 1.0) * (1.0 - smoothstep(0.06, 0.22, w1)) * 0.22;
    float kalin = Cizgi(c5, 1.4) * (1.0 - smoothstep(0.08, 0.30, w5)) * 0.45;
    float2 ew = max(fwidth(h.xy), 1e-7);
    float ex = 1.0 - saturate(abs(h.y) / ew.y - 0.6);  // X ekseni (y = 0)
    float ey = 1.0 - saturate(abs(h.x) / ew.x - 0.6);  // Y ekseni (x = 0)

    float uz = length(h - g_goz.xyz);
    float sol = 1.0 - smoothstep(g_izgara.z, g_izgara.w, uz);

    float3 renk = float3(0.20, 0.25, 0.32);
    float alfa = max(ince, kalin);
    if (ex > 0.01) { renk = lerp(renk, float3(0.80, 0.18, 0.15), ex); alfa = max(alfa, ex * 0.85); }
    if (ey > 0.01) { renk = lerp(renk, float3(0.15, 0.62, 0.22), ey); alfa = max(alfa, ey * 0.85); }
    alfa *= sol;
    if (alfa < 0.004) discard;

    IzgaraCikis o;
    o.c = float4(renk, alfa);
    o.d = k.z / k.w;
    return o;
}
