#include "grafik.h"

#include <d3dcompiler.h>

#include <algorithm>
#include <climits>
#include <cstdio>
#include <cstring>

#include "golgelendirici.h"
#include "gunluk.h"
#include "imgui_impl_dx12.h"

#define CIK(p) IID_PPV_ARGS((p).ReleaseAndGetAddressOf())

namespace op4 {
namespace {

std::string HrMetni(HRESULT hr) {
    char b[32];
    std::snprintf(b, sizeof(b), "0x%08lX", static_cast<unsigned long>(hr));
    return b;
}

struct KareSabitleri {
    float vp[16];
    float tersVp[16];
    float goz[4];
    float isik[4];
    float ust[4];
    float alt[4];
    float izgara[4];
    float cizgi[4];
};
static_assert(sizeof(KareSabitleri) <= 256, "sabit tamponu 256 bayta sığmalı");

D3D12_HEAP_PROPERTIES Yigin(D3D12_HEAP_TYPE t) {
    D3D12_HEAP_PROPERTIES h{};
    h.Type = t;
    h.CreationNodeMask = 1;
    h.VisibleNodeMask = 1;
    return h;
}

D3D12_RESOURCE_DESC TamponTanimi(UINT64 boyut) {
    D3D12_RESOURCE_DESC d{};
    d.Dimension = D3D12_RESOURCE_DIMENSION_BUFFER;
    d.Width = boyut;
    d.Height = 1;
    d.DepthOrArraySize = 1;
    d.MipLevels = 1;
    d.Format = DXGI_FORMAT_UNKNOWN;
    d.SampleDesc.Count = 1;
    d.Layout = D3D12_TEXTURE_LAYOUT_ROW_MAJOR;
    return d;
}

D3D12_RESOURCE_DESC DokuTanimi(UINT g, UINT y, DXGI_FORMAT f, UINT ornek, D3D12_RESOURCE_FLAGS bayrak) {
    D3D12_RESOURCE_DESC d{};
    d.Dimension = D3D12_RESOURCE_DIMENSION_TEXTURE2D;
    d.Width = g;
    d.Height = y;
    d.DepthOrArraySize = 1;
    d.MipLevels = 1;
    d.Format = f;
    d.SampleDesc.Count = ornek;
    d.Layout = D3D12_TEXTURE_LAYOUT_UNKNOWN;
    d.Flags = bayrak;
    return d;
}

bool Derle(const char* giris, const char* hedef, ComPtr<ID3DBlob>& kod, std::string& hata) {
    ComPtr<ID3DBlob> hatalar;
    HRESULT hr = D3DCompile(kGolgelendirici, sizeof(kGolgelendirici) - 1, "op4.hlsl", nullptr, nullptr, giris, hedef,
                            D3DCOMPILE_OPTIMIZATION_LEVEL3, 0, kod.ReleaseAndGetAddressOf(), hatalar.GetAddressOf());
    if (FAILED(hr)) {
        hata = std::string("gölgelendirici derlenemedi (") + giris + "): " +
               (hatalar ? std::string(static_cast<const char*>(hatalar->GetBufferPointer()), hatalar->GetBufferSize())
                        : HrMetni(hr));
        return false;
    }
    return true;
}

// Sahne renkleri (sRGB).
constexpr float kArkaUst[4] = {0.70f, 0.77f, 0.85f, 1.0f};
constexpr float kArkaAlt[4] = {0.95f, 0.96f, 0.975f, 1.0f};
constexpr float kCelik[4] = {0.50f, 0.60f, 0.73f, 1.0f};
constexpr float kKenar[4] = {0.08f, 0.11f, 0.16f, 0.80f};
constexpr float kEksen[4] = {0.10f, 0.30f, 0.62f, 1.0f};

}  // namespace

Grafik::~Grafik() {
    if (kuyruk_ && cit_) GpuBekle();
    if (citOlayi_) CloseHandle(citOlayi_);
    if (beklemeNesnesi_) CloseHandle(beklemeNesnesi_);
}

const char* Grafik::OzellikDuzeyi() const {
    switch (static_cast<int>(duzey_)) {
        case 0xc200: return "12_2";
        case 0xc100: return "12_1";
        case 0xc000: return "12_0";
        case 0xb100: return "11_1";
        default: return "11_0";
    }
}

HataKatmani Grafik::HataKatmaniYokla() {
    HataKatmani k;
    ComPtr<ID3D12Debug> d;
    const HRESULT hr = D3D12GetDebugInterface(CIK(d));
    k.var = SUCCEEDED(hr);
    k.hr = static_cast<long>(hr);
    return k;
}

HataKatmani Grafik::HataKatmaniIletileri() const {
    HataKatmani k;
    k.var = katmanEtkin_;
    k.hr = katmanHr_;
    k.etkin = katmanEtkin_ && iletiKuyrugu_;
    if (!k.etkin) return k;
    const UINT64 n = iletiKuyrugu_->GetNumStoredMessages();
    std::vector<char> tampon;
    for (UINT64 i = 0; i < n; ++i) {
        SIZE_T boy = 0;
        if (FAILED(iletiKuyrugu_->GetMessage(i, nullptr, &boy)) || boy < sizeof(D3D12_MESSAGE)) continue;
        tampon.assign(boy, 0);
        auto* m = reinterpret_cast<D3D12_MESSAGE*>(tampon.data());
        if (FAILED(iletiKuyrugu_->GetMessage(i, m, &boy))) continue;
        const char* duzey = "bilgi";
        switch (m->Severity) {
            case D3D12_MESSAGE_SEVERITY_CORRUPTION:
            case D3D12_MESSAGE_SEVERITY_ERROR:
                ++k.hata;
                duzey = m->Severity == D3D12_MESSAGE_SEVERITY_ERROR ? "HATA" : "BOZULMA";
                break;
            case D3D12_MESSAGE_SEVERITY_WARNING:
                ++k.uyari;
                duzey = "uyarı";
                break;
            default:
                ++k.bilgi;
                break;
        }
        if (m->Severity <= D3D12_MESSAGE_SEVERITY_WARNING && k.ornekler.size() < 12) {
            const SIZE_T u = m->DescriptionByteLength > 0 ? m->DescriptionByteLength - 1 : 0;
            k.ornekler.push_back(std::string(duzey) + " #" + std::to_string(static_cast<int>(m->ID)) + ": " +
                                 std::string(m->pDescription ? m->pDescription : "", m->pDescription ? u : 0));
        }
    }
    k.dusen = iletiKuyrugu_->GetNumMessagesDiscardedByMessageCountLimit();
    return k;
}

bool Grafik::Baslat(bool warpZorla, std::string& hata) {
    UINT fabrikaBayragi = 0;
#ifdef OP4_HATA_AYIKLAMA
    katmanIste_ = true;
#endif
    if (katmanIste_) {
        ComPtr<ID3D12Debug> d;
        const HRESULT h = D3D12GetDebugInterface(CIK(d));
        katmanHr_ = static_cast<long>(h);
        if (SUCCEEDED(h)) {
            d->EnableDebugLayer();
            katmanEtkin_ = true;
            fabrikaBayragi |= DXGI_CREATE_FACTORY_DEBUG;
            Gunluk("D3D12 hata ayıklama katmanı açıldı");
        } else {
            Gunluk("Uyarı: D3D12 hata ayıklama katmanı bu makinede yok (%s); katmansız sürülüyor", HrMetni(h).c_str());
        }
    }
    HRESULT hr = CreateDXGIFactory2(fabrikaBayragi, CIK(fabrika_));
    if (FAILED(hr) && fabrikaBayragi != 0) {
        // DXGI hata ayıklama bileşeni (dxgidebug.dll) ayrı kurulabilir; yoksa yalnız D3D12 katmanıyla sürülür.
        Gunluk("Uyarı: DXGI hata ayıklama fabrikası açılamadı (%s)", HrMetni(hr).c_str());
        hr = CreateDXGIFactory2(0, CIK(fabrika_));
    }
    if (FAILED(hr)) {
        hata = "DXGI fabrikası oluşturulamadı: " + HrMetni(hr);
        return false;
    }
    // Bağdaştırıcı sırası: (1) yüksek başarımlı donanım GPU'su, (2) WARP, (3) listedeki herhangi biri (ör. Wine/vkd3d).
    // warpZorla: (1) atlanır (başsız test / CI: aynı sonucu her makinede veren yazılım çizici).
    auto dene = [&](IDXGIAdapter1* a) {
        return SUCCEEDED(D3D12CreateDevice(a, D3D_FEATURE_LEVEL_11_0, CIK(aygit_)));
    };
    auto listele = [&](bool yazilimDahil) {
        for (UINT i = 0; !aygit_; ++i) {
            ComPtr<IDXGIAdapter1> a;
            ComPtr<IDXGIFactory6> f6;
            HRESULT h = SUCCEEDED(fabrika_.As(&f6))
                            ? f6->EnumAdapterByGpuPreference(i, DXGI_GPU_PREFERENCE_HIGH_PERFORMANCE, CIK(a))
                            : static_cast<IDXGIFactory1*>(fabrika_.Get())->EnumAdapters1(i, a.ReleaseAndGetAddressOf());
            if (h == DXGI_ERROR_NOT_FOUND || FAILED(h)) break;
            DXGI_ADAPTER_DESC1 t{};
            a->GetDesc1(&t);
            if (!yazilimDahil && (t.Flags & DXGI_ADAPTER_FLAG_SOFTWARE)) continue;
            if (dene(a.Get())) {
                bagdastirici_ = a;
                warp_ = (t.Flags & DXGI_ADAPTER_FLAG_SOFTWARE) != 0;
            }
        }
    };
    if (!warpZorla) listele(false);
    if (!aygit_) {
        ComPtr<IDXGIAdapter1> a;
        hr = fabrika_->EnumWarpAdapter(CIK(a));
        if (SUCCEEDED(hr) && dene(a.Get())) {
            bagdastirici_ = a;
            warp_ = true;
        } else {
            Gunluk("Uyarı: WARP bağdaştırıcısı kullanılamadı (%s); listedeki bağdaştırıcılar deneniyor", HrMetni(hr).c_str());
        }
    }
    if (!aygit_) listele(true);
    if (!aygit_) {
        hata = "Direct3D 12 aygıtı oluşturulamadı (uygun bağdaştırıcı yok)";
        return false;
    }
    if (katmanEtkin_ && SUCCEEDED(aygit_.As(&iletiKuyrugu_))) {
        iletiKuyrugu_->SetMessageCountLimit(4096);
        iletiKuyrugu_->SetMuteDebugOutput(FALSE);
    }
    DXGI_ADAPTER_DESC1 t{};
    bagdastirici_->GetDesc1(&t);
    bagdastiriciAdi_ = Utf8(t.Description);
    // GPU'suz makinelerde (sanal makine, CI, bazı uzak masaüstü oturumları) "Microsoft Basic Render Driver" donanım
    // bağdaştırıcısı gibi listelenir (SOFTWARE bayrağı yok) ama WARP'tır: MSAA ve etiket buna göre seçilir.
    if (t.VendorId == 0x1414 && t.DeviceId == 0x8C) warp_ = true;
    {
        const D3D_FEATURE_LEVEL duzeyler[] = {static_cast<D3D_FEATURE_LEVEL>(0xc200), D3D_FEATURE_LEVEL_12_1,
                                              D3D_FEATURE_LEVEL_12_0, D3D_FEATURE_LEVEL_11_1, D3D_FEATURE_LEVEL_11_0};
        D3D12_FEATURE_DATA_FEATURE_LEVELS fl{};
        fl.NumFeatureLevels = 5;
        fl.pFeatureLevelsRequested = duzeyler;
        if (SUCCEEDED(aygit_->CheckFeatureSupport(D3D12_FEATURE_FEATURE_LEVELS, &fl, sizeof(fl))))
            duzey_ = fl.MaxSupportedFeatureLevel;
    }
    // MSAA: donanımda 8×, WARP'ta 4× (yazılım çiziciyi boğmamak için) — desteklenen en yükseği.
    ornek_ = 1;
    const UINT adaylar[] = {8, 4, 2};
    for (UINT n : adaylar) {
        if (warp_ && n > 4) continue;
        D3D12_FEATURE_DATA_MULTISAMPLE_QUALITY_LEVELS r{}, d{};
        r.Format = RENK_BICIMI;
        r.SampleCount = n;
        d.Format = DERINLIK_BICIMI;
        d.SampleCount = n;
        if (SUCCEEDED(aygit_->CheckFeatureSupport(D3D12_FEATURE_MULTISAMPLE_QUALITY_LEVELS, &r, sizeof(r))) &&
            r.NumQualityLevels > 0 &&
            SUCCEEDED(aygit_->CheckFeatureSupport(D3D12_FEATURE_MULTISAMPLE_QUALITY_LEVELS, &d, sizeof(d))) &&
            d.NumQualityLevels > 0) {
            ornek_ = n;
            break;
        }
    }
    Gunluk("DirectX 12: bağdaştırıcı \"%s\"%s, özellik düzeyi %s, ayrık bellek %llu MB, MSAA %u×",
           bagdastiriciAdi_.c_str(), warp_ ? " (WARP yazılım çizici)" : "", OzellikDuzeyi(),
           static_cast<unsigned long long>(t.DedicatedVideoMemory / (1024 * 1024)), ornek_);

    D3D12_COMMAND_QUEUE_DESC kt{};
    kt.Type = D3D12_COMMAND_LIST_TYPE_DIRECT;
    if (FAILED(hr = aygit_->CreateCommandQueue(&kt, CIK(kuyruk_)))) {
        hata = "komut kuyruğu: " + HrMetni(hr);
        return false;
    }
    for (KareBaglami& k : kareler_) {
        if (FAILED(hr = aygit_->CreateCommandAllocator(D3D12_COMMAND_LIST_TYPE_DIRECT, CIK(k.ayirici)))) {
            hata = "komut ayırıcı: " + HrMetni(hr);
            return false;
        }
        D3D12_HEAP_PROPERTIES yy = Yigin(D3D12_HEAP_TYPE_UPLOAD);
        D3D12_RESOURCE_DESC td = TamponTanimi(256);
        if (FAILED(hr = aygit_->CreateCommittedResource(&yy, D3D12_HEAP_FLAG_NONE, &td,
                                                        D3D12_RESOURCE_STATE_GENERIC_READ, nullptr,
                                                        CIK(k.sabitler)))) {
            hata = "sabit tamponu: " + HrMetni(hr);
            return false;
        }
        D3D12_RANGE okunmaz{0, 0};
        k.sabitler->Map(0, &okunmaz, reinterpret_cast<void**>(&k.sabitPtr));
    }
    if (FAILED(hr = aygit_->CreateCommandList(0, D3D12_COMMAND_LIST_TYPE_DIRECT, kareler_[0].ayirici.Get(), nullptr,
                                              CIK(liste_)))) {
        hata = "komut listesi: " + HrMetni(hr);
        return false;
    }
    liste_->Close();
    if (FAILED(hr = aygit_->CreateFence(0, D3D12_FENCE_FLAG_NONE, CIK(cit_)))) {
        hata = "çit: " + HrMetni(hr);
        return false;
    }
    citOlayi_ = CreateEventW(nullptr, FALSE, FALSE, nullptr);

    D3D12_DESCRIPTOR_HEAP_DESC yt{};
    yt.Type = D3D12_DESCRIPTOR_HEAP_TYPE_RTV;
    yt.NumDescriptors = KARE_SAYISI + 2;  // arka tamponlar + MSAA + ekran dışı
    aygit_->CreateDescriptorHeap(&yt, CIK(rtvYigini_));
    rtvAdim_ = aygit_->GetDescriptorHandleIncrementSize(D3D12_DESCRIPTOR_HEAP_TYPE_RTV);
    yt.Type = D3D12_DESCRIPTOR_HEAP_TYPE_DSV;
    yt.NumDescriptors = 1;
    aygit_->CreateDescriptorHeap(&yt, CIK(dsvYigini_));
    yt.Type = D3D12_DESCRIPTOR_HEAP_TYPE_CBV_SRV_UAV;
    yt.NumDescriptors = 64;
    yt.Flags = D3D12_DESCRIPTOR_HEAP_FLAG_SHADER_VISIBLE;
    if (FAILED(hr = aygit_->CreateDescriptorHeap(&yt, CIK(srvYigini_)))) {
        hata = "tanımlayıcı yığını: " + HrMetni(hr);
        return false;
    }
    srv_.yigin = srvYigini_.Get();
    srv_.cpu0 = srvYigini_->GetCPUDescriptorHandleForHeapStart();
    srv_.gpu0 = srvYigini_->GetGPUDescriptorHandleForHeapStart();
    srv_.adim = aygit_->GetDescriptorHandleIncrementSize(D3D12_DESCRIPTOR_HEAP_TYPE_CBV_SRV_UAV);
    for (UINT i = 64; i > 0; --i) srv_.bos.push_back(i - 1);

    return BoruHatlariKur(hata);
}

bool Grafik::BoruHatlariKur(std::string& hata) {
    D3D12_ROOT_PARAMETER p[2]{};
    p[0].ParameterType = D3D12_ROOT_PARAMETER_TYPE_CBV;
    p[0].Descriptor.ShaderRegister = 0;
    p[0].ShaderVisibility = D3D12_SHADER_VISIBILITY_ALL;
    p[1].ParameterType = D3D12_ROOT_PARAMETER_TYPE_32BIT_CONSTANTS;
    p[1].Constants.ShaderRegister = 1;
    p[1].Constants.Num32BitValues = 4;
    p[1].ShaderVisibility = D3D12_SHADER_VISIBILITY_ALL;
    D3D12_ROOT_SIGNATURE_DESC rd{};
    rd.NumParameters = 2;
    rd.pParameters = p;
    rd.Flags = D3D12_ROOT_SIGNATURE_FLAG_ALLOW_INPUT_ASSEMBLER_INPUT_LAYOUT;
    ComPtr<ID3DBlob> imza, hatalar;
    HRESULT hr = D3D12SerializeRootSignature(&rd, D3D_ROOT_SIGNATURE_VERSION_1, imza.GetAddressOf(), hatalar.GetAddressOf());
    if (FAILED(hr)) {
        hata = "kök imza: " + HrMetni(hr);
        return false;
    }
    if (FAILED(hr = aygit_->CreateRootSignature(0, imza->GetBufferPointer(), imza->GetBufferSize(), CIK(kokImza_)))) {
        hata = "kök imza oluşturma: " + HrMetni(hr);
        return false;
    }

    double t0 = GecenMs();
    ComPtr<ID3DBlob> vsKati, psKati, vsCizgi, psCizgi, vsTam, psArka, psIzgara;
    if (!Derle("vs_kati", "vs_5_0", vsKati, hata) || !Derle("ps_kati", "ps_5_0", psKati, hata) ||
        !Derle("vs_cizgi", "vs_5_0", vsCizgi, hata) || !Derle("ps_cizgi", "ps_5_0", psCizgi, hata) ||
        !Derle("vs_tam", "vs_5_0", vsTam, hata) || !Derle("ps_arka", "ps_5_0", psArka, hata) ||
        !Derle("ps_izgara", "ps_5_0", psIzgara, hata))
        return false;
    Gunluk("Gölgelendiriciler derlendi (%.1f ms)", GecenMs() - t0);

    const D3D12_INPUT_ELEMENT_DESC katiGirdi[] = {
        {"POSITION", 0, DXGI_FORMAT_R32G32B32_FLOAT, 0, 0, D3D12_INPUT_CLASSIFICATION_PER_VERTEX_DATA, 0},
        {"NORMAL", 0, DXGI_FORMAT_R32G32B32_FLOAT, 0, 12, D3D12_INPUT_CLASSIFICATION_PER_VERTEX_DATA, 0},
    };
    const D3D12_INPUT_ELEMENT_DESC cizgiGirdi[] = {
        {"POSITION", 0, DXGI_FORMAT_R32G32B32_FLOAT, 0, 0, D3D12_INPUT_CLASSIFICATION_PER_VERTEX_DATA, 0},
    };
    enum Derinlik { YOK, YAZ, OKU };
    auto yap = [&](ID3DBlob* vs, ID3DBlob* ps, const D3D12_INPUT_ELEMENT_DESC* girdi, UINT girdiSayisi,
                   D3D12_PRIMITIVE_TOPOLOGY_TYPE tur, bool karistir, Derinlik derinlik,
                   ComPtr<ID3D12PipelineState>& pso, const char* ad) -> bool {
        D3D12_GRAPHICS_PIPELINE_STATE_DESC d{};
        d.pRootSignature = kokImza_.Get();
        d.VS = {vs->GetBufferPointer(), vs->GetBufferSize()};
        d.PS = {ps->GetBufferPointer(), ps->GetBufferSize()};
        d.InputLayout = {girdi, girdiSayisi};
        d.PrimitiveTopologyType = tur;
        d.NumRenderTargets = 1;
        d.RTVFormats[0] = RENK_BICIMI;
        d.DSVFormat = DERINLIK_BICIMI;
        d.SampleDesc.Count = ornek_;
        d.SampleMask = UINT_MAX;
        D3D12_RASTERIZER_DESC& r = d.RasterizerState;
        r.FillMode = D3D12_FILL_MODE_SOLID;
        r.CullMode = D3D12_CULL_MODE_NONE;
        r.DepthClipEnable = TRUE;
        r.MultisampleEnable = ornek_ > 1 ? TRUE : FALSE;  // MSAA'da çizgiler dörtgen olarak (yumuşak) taranır
        r.AntialiasedLineEnable = ornek_ > 1 ? FALSE : TRUE;
        D3D12_RENDER_TARGET_BLEND_DESC& b = d.BlendState.RenderTarget[0];
        b.BlendEnable = karistir ? TRUE : FALSE;
        b.SrcBlend = karistir ? D3D12_BLEND_SRC_ALPHA : D3D12_BLEND_ONE;
        b.DestBlend = karistir ? D3D12_BLEND_INV_SRC_ALPHA : D3D12_BLEND_ZERO;
        b.BlendOp = D3D12_BLEND_OP_ADD;
        b.SrcBlendAlpha = D3D12_BLEND_ONE;
        b.DestBlendAlpha = karistir ? D3D12_BLEND_INV_SRC_ALPHA : D3D12_BLEND_ZERO;
        b.BlendOpAlpha = D3D12_BLEND_OP_ADD;
        b.LogicOp = D3D12_LOGIC_OP_NOOP;
        b.RenderTargetWriteMask = D3D12_COLOR_WRITE_ENABLE_ALL;
        D3D12_DEPTH_STENCIL_DESC& z = d.DepthStencilState;
        z.DepthEnable = derinlik != YOK ? TRUE : FALSE;
        z.DepthWriteMask = derinlik == YAZ ? D3D12_DEPTH_WRITE_MASK_ALL : D3D12_DEPTH_WRITE_MASK_ZERO;
        z.DepthFunc = derinlik == YAZ ? D3D12_COMPARISON_FUNC_GREATER : D3D12_COMPARISON_FUNC_GREATER_EQUAL;  // ters-Z
        z.StencilEnable = FALSE;
        z.FrontFace = {D3D12_STENCIL_OP_KEEP, D3D12_STENCIL_OP_KEEP, D3D12_STENCIL_OP_KEEP, D3D12_COMPARISON_FUNC_ALWAYS};
        z.BackFace = z.FrontFace;
        HRESULT h = aygit_->CreateGraphicsPipelineState(&d, CIK(pso));
        if (FAILED(h)) {
            hata = std::string("boru hattı (") + ad + "): " + HrMetni(h);
            return false;
        }
        return true;
    };
    const auto UCGEN = D3D12_PRIMITIVE_TOPOLOGY_TYPE_TRIANGLE;
    const auto CIZGI = D3D12_PRIMITIVE_TOPOLOGY_TYPE_LINE;
    return yap(vsTam.Get(), psArka.Get(), nullptr, 0, UCGEN, false, YOK, psoArka_, "arka plan") &&
           yap(vsKati.Get(), psKati.Get(), katiGirdi, 2, UCGEN, false, YAZ, psoKati_, "katı") &&
           yap(vsCizgi.Get(), psCizgi.Get(), cizgiGirdi, 1, CIZGI, true, OKU, psoCizgi_, "çizgi") &&
           yap(vsTam.Get(), psIzgara.Get(), nullptr, 0, UCGEN, true, OKU, psoIzgara_, "ızgara");
}

void Grafik::Bariyer(ID3D12Resource* r, D3D12_RESOURCE_STATES once, D3D12_RESOURCE_STATES sonra) {
    if (once == sonra) return;
    D3D12_RESOURCE_BARRIER b{};
    b.Type = D3D12_RESOURCE_BARRIER_TYPE_TRANSITION;
    b.Transition.pResource = r;
    b.Transition.Subresource = D3D12_RESOURCE_BARRIER_ALL_SUBRESOURCES;
    b.Transition.StateBefore = once;
    b.Transition.StateAfter = sonra;
    liste_->ResourceBarrier(1, &b);
}

void Grafik::GpuBekle() {
    kuyruk_->Signal(cit_.Get(), ++citDegeri_);
    if (cit_->GetCompletedValue() < citDegeri_) {
        cit_->SetEventOnCompletion(citDegeri_, citOlayi_);
        WaitForSingleObject(citOlayi_, INFINITE);
    }
}

void Grafik::KareBekle(KareBaglami& k) {
    if (cit_->GetCompletedValue() < k.cit) {
        cit_->SetEventOnCompletion(k.cit, citOlayi_);
        WaitForSingleObject(citOlayi_, INFINITE);
    }
}

bool Grafik::TamponYukle(const void* veri, size_t boyut, ComPtr<ID3D12Resource>& hedef, std::string& hata) {
    hedef.Reset();
    if (boyut == 0) return true;
    D3D12_HEAP_PROPERTIES vy = Yigin(D3D12_HEAP_TYPE_DEFAULT), yy = Yigin(D3D12_HEAP_TYPE_UPLOAD);
    D3D12_RESOURCE_DESC td = TamponTanimi(boyut);
    ComPtr<ID3D12Resource> yukleme;
    // Tamponlar COMMON durumunda oluşturulur (başka başlangıç durumu yok sayılır; hata ayıklama katmanı uyarısı #1328);
    // kopyalamada örtük olarak COPY_DEST'e yükselir, ardından aynı listede bariyerle köşe / indis durumuna geçer.
    HRESULT hr = aygit_->CreateCommittedResource(&vy, D3D12_HEAP_FLAG_NONE, &td, D3D12_RESOURCE_STATE_COMMON,
                                                 nullptr, CIK(hedef));
    if (SUCCEEDED(hr))
        hr = aygit_->CreateCommittedResource(&yy, D3D12_HEAP_FLAG_NONE, &td, D3D12_RESOURCE_STATE_GENERIC_READ,
                                             nullptr, CIK(yukleme));
    if (FAILED(hr)) {
        hata = "köşe tamponu: " + HrMetni(hr);
        return false;
    }
    void* p = nullptr;
    yukleme->Map(0, nullptr, &p);
    std::memcpy(p, veri, boyut);
    yukleme->Unmap(0, nullptr);
    GpuBekle();
    kareler_[0].ayirici->Reset();
    liste_->Reset(kareler_[0].ayirici.Get(), nullptr);
    liste_->CopyBufferRegion(hedef.Get(), 0, yukleme.Get(), 0, boyut);
    Bariyer(hedef.Get(), D3D12_RESOURCE_STATE_COPY_DEST,
            D3D12_RESOURCE_STATE_VERTEX_AND_CONSTANT_BUFFER | D3D12_RESOURCE_STATE_INDEX_BUFFER);
    liste_->Close();
    ID3D12CommandList* l[] = {liste_.Get()};
    kuyruk_->ExecuteCommandLists(1, l);
    GpuBekle();
    return true;
}

bool Grafik::SahneYukle(const Ag& ag, std::string& hata) {
    indisSayisi_ = static_cast<UINT>(ag.indisler.size());
    kenarSayisi_ = static_cast<UINT>(ag.kenarlar.size());
    eksenSayisi_ = static_cast<UINT>(ag.eksenler.size());
    return TamponYukle(ag.koseler.data(), ag.koseler.size() * sizeof(Kose), koseTamponu_, hata) &&
           TamponYukle(ag.indisler.data(), ag.indisler.size() * sizeof(uint32_t), indisTamponu_, hata) &&
           TamponYukle(ag.kenarlar.data(), ag.kenarlar.size() * sizeof(V3), kenarTamponu_, hata) &&
           TamponYukle(ag.eksenler.data(), ag.eksenler.size() * sizeof(V3), eksenTamponu_, hata);
}

bool Grafik::HedefleriKur(UINT g, UINT y, std::string& hata) {
    msaaRenk_.Reset();
    msaaDerinlik_.Reset();
    D3D12_HEAP_PROPERTIES vy = Yigin(D3D12_HEAP_TYPE_DEFAULT);
    D3D12_RESOURCE_DESC rt = DokuTanimi(g, y, RENK_BICIMI, ornek_, D3D12_RESOURCE_FLAG_ALLOW_RENDER_TARGET);
    D3D12_CLEAR_VALUE rtTemiz{};
    rtTemiz.Format = RENK_BICIMI;
    std::memcpy(rtTemiz.Color, kArkaAlt, sizeof(kArkaAlt));
    const D3D12_RESOURCE_STATES kaynakDurumu =
        ornek_ > 1 ? D3D12_RESOURCE_STATE_RESOLVE_SOURCE : D3D12_RESOURCE_STATE_COPY_SOURCE;
    HRESULT hr = aygit_->CreateCommittedResource(&vy, D3D12_HEAP_FLAG_NONE, &rt, kaynakDurumu, &rtTemiz, CIK(msaaRenk_));
    if (FAILED(hr)) {
        hata = "MSAA renk hedefi: " + HrMetni(hr);
        return false;
    }
    D3D12_RESOURCE_DESC dt = DokuTanimi(g, y, DERINLIK_BICIMI, ornek_,
                                        D3D12_RESOURCE_FLAG_ALLOW_DEPTH_STENCIL | D3D12_RESOURCE_FLAG_DENY_SHADER_RESOURCE);
    D3D12_CLEAR_VALUE dTemiz{};
    dTemiz.Format = DERINLIK_BICIMI;
    dTemiz.DepthStencil.Depth = 0.0f;  // ters-Z: uzak = 0
    hr = aygit_->CreateCommittedResource(&vy, D3D12_HEAP_FLAG_NONE, &dt, D3D12_RESOURCE_STATE_DEPTH_WRITE, &dTemiz,
                                         CIK(msaaDerinlik_));
    if (FAILED(hr)) {
        hata = "derinlik hedefi: " + HrMetni(hr);
        return false;
    }
    D3D12_CPU_DESCRIPTOR_HANDLE rtv = rtvYigini_->GetCPUDescriptorHandleForHeapStart();
    rtv.ptr += static_cast<SIZE_T>(KARE_SAYISI) * rtvAdim_;
    aygit_->CreateRenderTargetView(msaaRenk_.Get(), nullptr, rtv);
    aygit_->CreateDepthStencilView(msaaDerinlik_.Get(), nullptr, dsvYigini_->GetCPUDescriptorHandleForHeapStart());
    genislik_ = g;
    yukseklik_ = y;
    return true;
}

bool Grafik::TakasZinciriKur(HWND pencere, UINT g, UINT y, std::string& hata) {
    g = std::max(g, 8u);
    y = std::max(y, 8u);
    DXGI_SWAP_CHAIN_DESC1 sd{};
    sd.Width = g;
    sd.Height = y;
    sd.Format = RENK_BICIMI;
    sd.SampleDesc.Count = 1;
    sd.BufferUsage = DXGI_USAGE_RENDER_TARGET_OUTPUT;
    sd.BufferCount = KARE_SAYISI;
    sd.SwapEffect = DXGI_SWAP_EFFECT_FLIP_DISCARD;
    sd.Scaling = DXGI_SCALING_NONE;  // yeniden boyutlandırmada gerilmiş görüntü yerine kenara yaslı
    sd.AlphaMode = DXGI_ALPHA_MODE_UNSPECIFIED;
    sd.Flags = DXGI_SWAP_CHAIN_FLAG_FRAME_LATENCY_WAITABLE_OBJECT;
    ComPtr<IDXGISwapChain1> s1;
    HRESULT hr = fabrika_->CreateSwapChainForHwnd(kuyruk_.Get(), pencere, &sd, nullptr, nullptr, s1.GetAddressOf());
    if (FAILED(hr)) {
        sd.Scaling = DXGI_SCALING_STRETCH;
        hr = fabrika_->CreateSwapChainForHwnd(kuyruk_.Get(), pencere, &sd, nullptr, nullptr, s1.GetAddressOf());
    }
    if (FAILED(hr) || FAILED(s1.As(&takas_))) {
        hata = "takas zinciri: " + HrMetni(hr);
        return false;
    }
    fabrika_->MakeWindowAssociation(pencere, DXGI_MWA_NO_ALT_ENTER);
    // En düşük gecikme: CPU en çok bir kare önde. Kaydırma / döndürmede imleç ile görüntü arasındaki gecikmeyi
    // (sürüklemede "lastik" etkisi) en aza indirir.
    takas_->SetMaximumFrameLatency(1);
    beklemeNesnesi_ = takas_->GetFrameLatencyWaitableObject();
    for (UINT i = 0; i < KARE_SAYISI; ++i) {
        takas_->GetBuffer(i, CIK(arkaTampon_[i]));
        D3D12_CPU_DESCRIPTOR_HANDLE rtv = rtvYigini_->GetCPUDescriptorHandleForHeapStart();
        rtv.ptr += static_cast<SIZE_T>(i) * rtvAdim_;
        aygit_->CreateRenderTargetView(arkaTampon_[i].Get(), nullptr, rtv);
    }
    return HedefleriKur(g, y, hata);
}

bool Grafik::BoyutDegistir(UINT g, UINT y) {
    g = std::max(g, 8u);
    y = std::max(y, 8u);
    if (!takas_ || (g == genislik_ && y == yukseklik_)) return true;
    GpuBekle();
    for (auto& a : arkaTampon_) a.Reset();
    HRESULT hr = takas_->ResizeBuffers(KARE_SAYISI, g, y, RENK_BICIMI, DXGI_SWAP_CHAIN_FLAG_FRAME_LATENCY_WAITABLE_OBJECT);
    if (FAILED(hr)) {
        Gunluk("HATA: takas zinciri boyutlandırılamadı (%s)", HrMetni(hr).c_str());
        return false;
    }
    for (UINT i = 0; i < KARE_SAYISI; ++i) {
        takas_->GetBuffer(i, CIK(arkaTampon_[i]));
        D3D12_CPU_DESCRIPTOR_HANDLE rtv = rtvYigini_->GetCPUDescriptorHandleForHeapStart();
        rtv.ptr += static_cast<SIZE_T>(i) * rtvAdim_;
        aygit_->CreateRenderTargetView(arkaTampon_[i].Get(), nullptr, rtv);
    }
    std::string hata;
    if (!HedefleriKur(g, y, hata)) {
        Gunluk("HATA: %s", hata.c_str());
        return false;
    }
    return true;
}

bool Grafik::EkranDisiKur(UINT g, UINT y, std::string& hata) {
    D3D12_HEAP_PROPERTIES vy = Yigin(D3D12_HEAP_TYPE_DEFAULT), oy = Yigin(D3D12_HEAP_TYPE_READBACK);
    D3D12_RESOURCE_DESC rt = DokuTanimi(g, y, RENK_BICIMI, 1, D3D12_RESOURCE_FLAG_ALLOW_RENDER_TARGET);
    HRESULT hr = aygit_->CreateCommittedResource(&vy, D3D12_HEAP_FLAG_NONE, &rt, D3D12_RESOURCE_STATE_COPY_SOURCE,
                                                 nullptr, CIK(ekranDisi_));
    if (FAILED(hr)) {
        hata = "ekran dışı hedef: " + HrMetni(hr);
        return false;
    }
    UINT64 toplam = 0;
    aygit_->GetCopyableFootprints(&rt, 0, 1, 0, &okumaIzi_, nullptr, nullptr, &toplam);
    D3D12_RESOURCE_DESC ot = TamponTanimi(toplam);
    hr = aygit_->CreateCommittedResource(&oy, D3D12_HEAP_FLAG_NONE, &ot, D3D12_RESOURCE_STATE_COPY_DEST, nullptr,
                                         CIK(okumaTamponu_));
    if (FAILED(hr)) {
        hata = "okuma tamponu: " + HrMetni(hr);
        return false;
    }
    D3D12_CPU_DESCRIPTOR_HANDLE rtv = rtvYigini_->GetCPUDescriptorHandleForHeapStart();
    rtv.ptr += static_cast<SIZE_T>(KARE_SAYISI + 1) * rtvAdim_;
    aygit_->CreateRenderTargetView(ekranDisi_.Get(), nullptr, rtv);
    return HedefleriKur(g, y, hata);
}

void Grafik::ImGuiBilgisi(ImGui_ImplDX12_InitInfo& b) {
    b.Device = aygit_.Get();
    b.CommandQueue = kuyruk_.Get();
    b.NumFramesInFlight = KARE_SAYISI;
    b.RTVFormat = RENK_BICIMI;
    b.DSVFormat = DXGI_FORMAT_UNKNOWN;
    b.UserData = &srv_;
    b.SrvDescriptorHeap = srvYigini_.Get();
    b.SrvDescriptorAllocFn = [](ImGui_ImplDX12_InitInfo* i, D3D12_CPU_DESCRIPTOR_HANDLE* c, D3D12_GPU_DESCRIPTOR_HANDLE* g) {
        auto* s = static_cast<SrvAyirici*>(i->UserData);
        UINT n = s->bos.back();
        s->bos.pop_back();
        c->ptr = s->cpu0.ptr + static_cast<SIZE_T>(n) * s->adim;
        g->ptr = s->gpu0.ptr + static_cast<UINT64>(n) * s->adim;
    };
    b.SrvDescriptorFreeFn = [](ImGui_ImplDX12_InitInfo* i, D3D12_CPU_DESCRIPTOR_HANDLE c, D3D12_GPU_DESCRIPTOR_HANDLE) {
        auto* s = static_cast<SrvAyirici*>(i->UserData);
        s->bos.push_back(static_cast<UINT>((c.ptr - s->cpu0.ptr) / s->adim));
    };
}

void Grafik::SahneKaydet(KareBaglami& k, const Kamera& kam, const SahneAyari& a, GorusAlani gorus,
                         ID3D12Resource* hedef, D3D12_RESOURCE_STATES hedefDurumu) {
    gorus.g = std::max(1.0f, std::min(gorus.g, static_cast<float>(genislik_) - gorus.x));
    gorus.y2 = std::max(1.0f, std::min(gorus.y2, static_cast<float>(yukseklik_) - gorus.y));

    // Kare sabitleri.
    KareSabitleri s{};
    M4 vp = kam.GorunumIzdusum(gorus.g / gorus.y2), ters;
    Ters(vp, ters);
    std::memcpy(s.vp, vp.m, sizeof(s.vp));
    std::memcpy(s.tersVp, ters.m, sizeof(s.tersVp));
    V3 goz = kam.Goz();
    s.goz[0] = goz.x; s.goz[1] = goz.y; s.goz[2] = goz.z; s.goz[3] = 1;
    V3 sag, yukari;
    kam.EkranEksenleri(sag, yukari);
    V3 isik = Birim(sag * -0.45f + yukari * 0.80f + Birim(goz - kam.hedef) * 0.55f);  // gözün sol-üst arkasından
    s.isik[0] = isik.x; s.isik[1] = isik.y; s.isik[2] = isik.z;
    std::memcpy(s.ust, kArkaUst, sizeof(s.ust));
    std::memcpy(s.alt, kArkaAlt, sizeof(s.alt));
    s.izgara[0] = 1.0f;
    s.izgara[1] = 5.0f;
    s.izgara[2] = std::max(40.0f, kam.uzaklik * 3.0f);
    s.izgara[3] = std::max(80.0f, kam.uzaklik * 7.0f);
    s.cizgi[0] = 1.0015f;
    std::memcpy(k.sabitPtr, &s, sizeof(s));

    const D3D12_RESOURCE_STATES kaynakDurumu =
        ornek_ > 1 ? D3D12_RESOURCE_STATE_RESOLVE_SOURCE : D3D12_RESOURCE_STATE_COPY_SOURCE;
    const D3D12_RESOURCE_STATES cozumDurumu =
        ornek_ > 1 ? D3D12_RESOURCE_STATE_RESOLVE_DEST : D3D12_RESOURCE_STATE_COPY_DEST;
    Bariyer(msaaRenk_.Get(), kaynakDurumu, D3D12_RESOURCE_STATE_RENDER_TARGET);
    D3D12_CPU_DESCRIPTOR_HANDLE rtv = rtvYigini_->GetCPUDescriptorHandleForHeapStart();
    rtv.ptr += static_cast<SIZE_T>(KARE_SAYISI) * rtvAdim_;
    D3D12_CPU_DESCRIPTOR_HANDLE dsv = dsvYigini_->GetCPUDescriptorHandleForHeapStart();
    liste_->ClearRenderTargetView(rtv, kArkaAlt, 0, nullptr);
    liste_->ClearDepthStencilView(dsv, D3D12_CLEAR_FLAG_DEPTH, 0.0f, 0, 0, nullptr);
    liste_->OMSetRenderTargets(1, &rtv, FALSE, &dsv);
    D3D12_VIEWPORT v{gorus.x, gorus.y, gorus.g, gorus.y2, 0.0f, 1.0f};
    D3D12_RECT kirp{static_cast<LONG>(gorus.x), static_cast<LONG>(gorus.y), static_cast<LONG>(gorus.x + gorus.g),
                    static_cast<LONG>(gorus.y + gorus.y2)};
    liste_->RSSetViewports(1, &v);
    liste_->RSSetScissorRects(1, &kirp);
    liste_->SetGraphicsRootSignature(kokImza_.Get());
    liste_->SetGraphicsRootConstantBufferView(0, k.sabitler->GetGPUVirtualAddress());
    auto renk = [&](const float c[4]) { liste_->SetGraphicsRoot32BitConstants(1, 4, c, 0); };

    liste_->SetPipelineState(psoArka_.Get());
    liste_->IASetPrimitiveTopology(D3D_PRIMITIVE_TOPOLOGY_TRIANGLELIST);
    liste_->DrawInstanced(3, 1, 0, 0);

    if (a.kesitGorunumu && indisSayisi_ > 0) {
        D3D12_VERTEX_BUFFER_VIEW vb{koseTamponu_->GetGPUVirtualAddress(),
                                    static_cast<UINT>(koseTamponu_->GetDesc().Width), sizeof(Kose)};
        D3D12_INDEX_BUFFER_VIEW ib{indisTamponu_->GetGPUVirtualAddress(), indisSayisi_ * 4u, DXGI_FORMAT_R32_UINT};
        liste_->SetPipelineState(psoKati_.Get());
        liste_->IASetVertexBuffers(0, 1, &vb);
        liste_->IASetIndexBuffer(&ib);
        renk(kCelik);
        liste_->DrawIndexedInstanced(indisSayisi_, 1, 0, 0, 0);
        if (a.kenarlar && kenarSayisi_ > 0) {
            D3D12_VERTEX_BUFFER_VIEW kb{kenarTamponu_->GetGPUVirtualAddress(), kenarSayisi_ * 12u, 12u};
            liste_->SetPipelineState(psoCizgi_.Get());
            liste_->IASetPrimitiveTopology(D3D_PRIMITIVE_TOPOLOGY_LINELIST);
            liste_->IASetVertexBuffers(0, 1, &kb);
            renk(kKenar);
            liste_->DrawInstanced(kenarSayisi_, 1, 0, 0);
        }
    } else if (eksenSayisi_ > 0) {
        D3D12_VERTEX_BUFFER_VIEW eb{eksenTamponu_->GetGPUVirtualAddress(), eksenSayisi_ * 12u, 12u};
        liste_->SetPipelineState(psoCizgi_.Get());
        liste_->IASetPrimitiveTopology(D3D_PRIMITIVE_TOPOLOGY_LINELIST);
        liste_->IASetVertexBuffers(0, 1, &eb);
        renk(kEksen);
        liste_->DrawInstanced(eksenSayisi_, 1, 0, 0);
    }
    if (a.izgara) {
        liste_->SetPipelineState(psoIzgara_.Get());
        liste_->IASetPrimitiveTopology(D3D_PRIMITIVE_TOPOLOGY_TRIANGLELIST);
        liste_->DrawInstanced(3, 1, 0, 0);
    }

    Bariyer(msaaRenk_.Get(), D3D12_RESOURCE_STATE_RENDER_TARGET, kaynakDurumu);
    Bariyer(hedef, hedefDurumu, cozumDurumu);
    if (ornek_ > 1)
        liste_->ResolveSubresource(hedef, 0, msaaRenk_.Get(), 0, RENK_BICIMI);
    else
        liste_->CopyResource(hedef, msaaRenk_.Get());
    Bariyer(hedef, cozumDurumu, D3D12_RESOURCE_STATE_RENDER_TARGET);
}

bool Grafik::PencereKaresi(const Kamera& kam, const SahneAyari& a, GorusAlani gorus, ImDrawData* arayuz) {
    if (!takas_) return false;
    KareBaglami& k = kareler_[kareNo_ % KARE_SAYISI];
    WaitForSingleObjectEx(beklemeNesnesi_, 1000, TRUE);
    KareBekle(k);
    k.ayirici->Reset();
    liste_->Reset(k.ayirici.Get(), nullptr);
    UINT i = takas_->GetCurrentBackBufferIndex();
    ID3D12Resource* arka = arkaTampon_[i].Get();
    SahneKaydet(k, kam, a, gorus, arka, D3D12_RESOURCE_STATE_PRESENT);
    if (arayuz) {
        D3D12_CPU_DESCRIPTOR_HANDLE rtv = rtvYigini_->GetCPUDescriptorHandleForHeapStart();
        rtv.ptr += static_cast<SIZE_T>(i) * rtvAdim_;
        liste_->OMSetRenderTargets(1, &rtv, FALSE, nullptr);
        ID3D12DescriptorHeap* y[] = {srvYigini_.Get()};
        liste_->SetDescriptorHeaps(1, y);
        ImGui_ImplDX12_RenderDrawData(arayuz, liste_.Get());
    }
    Bariyer(arka, D3D12_RESOURCE_STATE_RENDER_TARGET, D3D12_RESOURCE_STATE_PRESENT);
    liste_->Close();
    ID3D12CommandList* l[] = {liste_.Get()};
    kuyruk_->ExecuteCommandLists(1, l);
    HRESULT hr = takas_->Present(1, 0);
    kuyruk_->Signal(cit_.Get(), ++citDegeri_);
    k.cit = citDegeri_;
    ++kareNo_;
    if (hr == DXGI_ERROR_DEVICE_REMOVED || hr == DXGI_ERROR_DEVICE_RESET) {
        Gunluk("HATA: grafik aygıtı kaldırıldı (%s)", HrMetni(aygit_->GetDeviceRemovedReason()).c_str());
        return false;
    }
    return hr != DXGI_STATUS_OCCLUDED;
}

bool Grafik::EkranDisiKaresi(const Kamera& kam, const SahneAyari& a, GorusAlani gorus, ImDrawData* arayuz,
                             std::vector<uint8_t>* rgba) {
    if (!ekranDisi_) return false;
    GpuBekle();
    KareBaglami& k = kareler_[0];
    k.ayirici->Reset();
    liste_->Reset(k.ayirici.Get(), nullptr);
    SahneKaydet(k, kam, a, gorus, ekranDisi_.Get(), D3D12_RESOURCE_STATE_COPY_SOURCE);
    if (arayuz) {
        D3D12_CPU_DESCRIPTOR_HANDLE rtv = rtvYigini_->GetCPUDescriptorHandleForHeapStart();
        rtv.ptr += static_cast<SIZE_T>(KARE_SAYISI + 1) * rtvAdim_;
        liste_->OMSetRenderTargets(1, &rtv, FALSE, nullptr);
        ID3D12DescriptorHeap* y[] = {srvYigini_.Get()};
        liste_->SetDescriptorHeaps(1, y);
        ImGui_ImplDX12_RenderDrawData(arayuz, liste_.Get());
    }
    Bariyer(ekranDisi_.Get(), D3D12_RESOURCE_STATE_RENDER_TARGET, D3D12_RESOURCE_STATE_COPY_SOURCE);
    if (rgba) {
        D3D12_TEXTURE_COPY_LOCATION hedef{}, kaynak{};
        hedef.pResource = okumaTamponu_.Get();
        hedef.Type = D3D12_TEXTURE_COPY_TYPE_PLACED_FOOTPRINT;
        hedef.PlacedFootprint = okumaIzi_;
        kaynak.pResource = ekranDisi_.Get();
        kaynak.Type = D3D12_TEXTURE_COPY_TYPE_SUBRESOURCE_INDEX;
        kaynak.SubresourceIndex = 0;
        liste_->CopyTextureRegion(&hedef, 0, 0, 0, &kaynak, nullptr);
    }
    liste_->Close();
    ID3D12CommandList* l[] = {liste_.Get()};
    kuyruk_->ExecuteCommandLists(1, l);
    GpuBekle();
    HRESULT neden = aygit_->GetDeviceRemovedReason();
    if (FAILED(neden)) {
        Gunluk("HATA: grafik aygıtı kaldırıldı (%s)", HrMetni(neden).c_str());
        return false;
    }
    if (rgba) {
        const UINT g = okumaIzi_.Footprint.Width, y = okumaIzi_.Footprint.Height;
        rgba->resize(static_cast<size_t>(g) * y * 4);
        uint8_t* p = nullptr;
        D3D12_RANGE okunan{0, static_cast<SIZE_T>(okumaIzi_.Offset + static_cast<UINT64>(okumaIzi_.Footprint.RowPitch) * y)};
        if (FAILED(okumaTamponu_->Map(0, &okunan, reinterpret_cast<void**>(&p)))) return false;
        for (UINT r = 0; r < y; ++r)
            std::memcpy(rgba->data() + static_cast<size_t>(r) * g * 4,
                        p + okumaIzi_.Offset + static_cast<size_t>(r) * okumaIzi_.Footprint.RowPitch,
                        static_cast<size_t>(g) * 4);
        D3D12_RANGE yazilmaz{0, 0};
        okumaTamponu_->Unmap(0, &yazilmaz);
    }
    return true;
}

}  // namespace op4
