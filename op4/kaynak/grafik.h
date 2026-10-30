// op4 — DirectX 12 çizici. Donanım bağdaştırıcısı (yüksek başarım tercihli), yoksa WARP (yazılım) bağdaştırıcısı.
// Sahne çok örnekli (MSAA) renk + D32 ters-Z derinlik hedefine çizilir, tek örnekli hedefe (takas zinciri arka
// tamponu ya da ekran dışı doku) çözülür (resolve); Dear ImGui arayüzü bu tek örnekli hedefin üzerine çizilir.
#pragma once

#include <d3d12.h>
#include <d3d12sdklayers.h>
#include <dxgi1_6.h>
#include <windows.h>
#include <wrl/client.h>

#include <cstdint>
#include <string>
#include <vector>

#include "geometri.h"
#include "kamera.h"

struct ImDrawData;
struct ImGui_ImplDX12_InitInfo;

namespace op4 {

using Microsoft::WRL::ComPtr;

struct SahneAyari {
    bool kesitGorunumu = true;  // false: çubuk (eksen çizgisi) görünümü
    bool kenarlar = true;
    bool izgara = true;
};

// D3D12 hata ayıklama katmanı (d3d12SDKLayers.dll: Windows'un isteğe bağlı "Graphics Tools" özelliği ya da Agility SDK).
// Yoklama: katman bu makinede var mı (`var`, `hr`). Etkin: `--hata-katmani` ile açıldı; ileti kuyruğundaki iletiler
// önem düzeyine göre sayılır (CORRUPTION + ERROR → hata, WARNING → uyarı, INFO + MESSAGE → bilgi).
struct HataKatmani {
    bool var = false;
    bool etkin = false;
    long hr = 0;
    unsigned hata = 0, uyari = 0, bilgi = 0;
    unsigned long long dusen = 0;  // ileti sınırı yüzünden saklanmayanlar
    std::vector<std::string> ornekler;  // ilk birkaç hata / uyarı
};

// Görüş alanı (piksel): sahnenin çizileceği dikdörtgen (arayüz panellerinin dışında kalan merkez alan).
struct GorusAlani {
    float x = 0, y = 0, g = 0, y2 = 0;  // y2 = yükseklik
};

class Grafik {
public:
    static constexpr UINT KARE_SAYISI = 2;  // uçuştaki kare (frames in flight) ve arka tampon sayısı
    static constexpr DXGI_FORMAT RENK_BICIMI = DXGI_FORMAT_R8G8B8A8_UNORM;
    static constexpr DXGI_FORMAT DERINLIK_BICIMI = DXGI_FORMAT_D32_FLOAT;

    ~Grafik();

    static HataKatmani HataKatmaniYokla();             // katmanı açmadan varlığını denetler
    void HataKatmaniIste(bool e) { katmanIste_ = e; }  // Baslat'tan önce; OP4_HATA_AYIKLAMA derlemesinde hep açık
    HataKatmani HataKatmaniIletileri() const;          // etkinse ileti kuyruğunun özeti
    bool Baslat(bool warpZorla, std::string& hata);
    bool SahneYukle(const Ag& ag, std::string& hata);
    bool TakasZinciriKur(HWND pencere, UINT g, UINT y, std::string& hata);
    bool BoyutDegistir(UINT g, UINT y);
    bool EkranDisiKur(UINT g, UINT y, std::string& hata);

    void ImGuiBilgisi(ImGui_ImplDX12_InitInfo& bilgi);  // ImGui_ImplDX12_Init için doldurur

    // Pencere karesi: çizer, sunar (vsync). false: pencere örtülü / küçültülmüş (çizim atlandı).
    bool PencereKaresi(const Kamera& k, const SahneAyari& a, GorusAlani gorus, ImDrawData* arayuz);
    // Ekran dışı kare: çizer, GPU'yu bekler; rgba != nullptr ise RGBA8 piksel (üstten alta, sıkı) döndürür.
    bool EkranDisiKaresi(const Kamera& k, const SahneAyari& a, GorusAlani gorus, ImDrawData* arayuz,
                         std::vector<uint8_t>* rgba);
    void GpuBekle();

    const std::string& BagdastiriciAdi() const { return bagdastiriciAdi_; }
    bool Warp() const { return warp_; }
    UINT OrnekSayisi() const { return ornek_; }
    const char* OzellikDuzeyi() const;
    UINT Genislik() const { return genislik_; }
    UINT Yukseklik() const { return yukseklik_; }
    size_t UcgenSayisi() const { return indisSayisi_ / 3; }

private:
    struct KareBaglami {
        ComPtr<ID3D12CommandAllocator> ayirici;
        ComPtr<ID3D12Resource> sabitler;  // yükleme yığını, kalıcı eşlenmiş
        uint8_t* sabitPtr = nullptr;
        UINT64 cit = 0;
    };
    struct SrvAyirici {
        ID3D12DescriptorHeap* yigin = nullptr;
        D3D12_CPU_DESCRIPTOR_HANDLE cpu0{};
        D3D12_GPU_DESCRIPTOR_HANDLE gpu0{};
        UINT adim = 0;
        std::vector<UINT> bos;
    };

    bool BoruHatlariKur(std::string& hata);
    bool HedefleriKur(UINT g, UINT y, std::string& hata);  // MSAA renk + derinlik
    void SahneKaydet(KareBaglami& k, const Kamera& kam, const SahneAyari& a, GorusAlani gorus,
                     ID3D12Resource* hedef, D3D12_RESOURCE_STATES hedefDurumu);
    void Bariyer(ID3D12Resource* r, D3D12_RESOURCE_STATES once, D3D12_RESOURCE_STATES sonra);
    bool TamponYukle(const void* veri, size_t boyut, ComPtr<ID3D12Resource>& hedef, std::string& hata);
    void KareBekle(KareBaglami& k);

    ComPtr<IDXGIFactory4> fabrika_;
    ComPtr<IDXGIAdapter1> bagdastirici_;
    ComPtr<ID3D12Device> aygit_;
    ComPtr<ID3D12CommandQueue> kuyruk_;
    ComPtr<ID3D12GraphicsCommandList> liste_;
    ComPtr<ID3D12Fence> cit_;
    HANDLE citOlayi_ = nullptr;
    UINT64 citDegeri_ = 0;
    KareBaglami kareler_[KARE_SAYISI];
    UINT64 kareNo_ = 0;

    ComPtr<ID3D12DescriptorHeap> rtvYigini_, dsvYigini_, srvYigini_;
    UINT rtvAdim_ = 0;
    SrvAyirici srv_;

    // takas zinciri
    ComPtr<IDXGISwapChain3> takas_;
    HANDLE beklemeNesnesi_ = nullptr;
    ComPtr<ID3D12Resource> arkaTampon_[KARE_SAYISI];
    // ekran dışı
    ComPtr<ID3D12Resource> ekranDisi_, okumaTamponu_;
    D3D12_PLACED_SUBRESOURCE_FOOTPRINT okumaIzi_{};
    // MSAA
    ComPtr<ID3D12Resource> msaaRenk_, msaaDerinlik_;
    UINT ornek_ = 1;
    UINT genislik_ = 0, yukseklik_ = 0;

    // boru hatları
    ComPtr<ID3D12RootSignature> kokImza_;
    ComPtr<ID3D12PipelineState> psoArka_, psoKati_, psoCizgi_, psoIzgara_;

    // sahne tamponları
    ComPtr<ID3D12Resource> koseTamponu_, indisTamponu_, kenarTamponu_, eksenTamponu_;
    UINT indisSayisi_ = 0, kenarSayisi_ = 0, eksenSayisi_ = 0;

    // hata ayıklama katmanı
    bool katmanIste_ = false, katmanEtkin_ = false;
    long katmanHr_ = 0;
    ComPtr<ID3D12InfoQueue> iletiKuyrugu_;

    std::string bagdastiriciAdi_;
    bool warp_ = false;
    D3D_FEATURE_LEVEL duzey_ = D3D_FEATURE_LEVEL_11_0;
};

}  // namespace op4
