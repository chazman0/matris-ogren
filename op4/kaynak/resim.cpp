#include "resim.h"

#include <wincodec.h>
#include <windows.h>
#include <wrl/client.h>

#include <cstdio>

namespace op4 {
namespace {

using Microsoft::WRL::ComPtr;

std::string Hr(const char* ne, HRESULT hr) {
    char b[160];
    std::snprintf(b, sizeof(b), "%s (0x%08lX)", ne, static_cast<unsigned long>(hr));
    return b;
}

ComPtr<IWICImagingFactory> Fabrika(std::string& hata) {
    ComPtr<IWICImagingFactory> f;
    HRESULT hr = CoCreateInstance(CLSID_WICImagingFactory, nullptr, CLSCTX_INPROC_SERVER, IID_PPV_ARGS(f.GetAddressOf()));
    if (FAILED(hr)) hata = Hr("WIC fabrikası oluşturulamadı", hr);
    return f;
}

}  // namespace

bool PngBoyutu(const std::wstring& yol, int& g, int& y) {
    std::string hata;
    ComPtr<IWICImagingFactory> f = Fabrika(hata);
    if (!f) return false;
    ComPtr<IWICBitmapDecoder> c;
    ComPtr<IWICBitmapFrameDecode> kare;
    UINT gg = 0, yy = 0;
    if (FAILED(f->CreateDecoderFromFilename(yol.c_str(), nullptr, GENERIC_READ, WICDecodeMetadataCacheOnDemand,
                                            c.GetAddressOf())) ||
        FAILED(c->GetFrame(0, kare.GetAddressOf())) || FAILED(kare->GetSize(&gg, &yy)))
        return false;
    g = static_cast<int>(gg);
    y = static_cast<int>(yy);
    return true;
}

bool PngOku(const std::wstring& yol, Resim& r, std::string& hata, int hedefG, int hedefY) {
    ComPtr<IWICImagingFactory> f = Fabrika(hata);
    if (!f) return false;
    ComPtr<IWICBitmapDecoder> c;
    HRESULT hr = f->CreateDecoderFromFilename(yol.c_str(), nullptr, GENERIC_READ, WICDecodeMetadataCacheOnDemand,
                                              c.GetAddressOf());
    if (FAILED(hr)) {
        hata = Hr("resim açılamadı", hr);
        return false;
    }
    ComPtr<IWICBitmapFrameDecode> kare;
    if (FAILED(hr = c->GetFrame(0, kare.GetAddressOf()))) {
        hata = Hr("resim karesi okunamadı", hr);
        return false;
    }
    ComPtr<IWICFormatConverter> donustur;
    f->CreateFormatConverter(donustur.GetAddressOf());
    if (FAILED(hr = donustur->Initialize(kare.Get(), GUID_WICPixelFormat32bppPBGRA, WICBitmapDitherTypeNone, nullptr, 0.0,
                                         WICBitmapPaletteTypeCustom))) {
        hata = Hr("piksel biçimi dönüştürülemedi", hr);
        return false;
    }
    IWICBitmapSource* kaynak = donustur.Get();
    ComPtr<IWICBitmapScaler> olcek;
    UINT g = 0, y = 0;
    kaynak->GetSize(&g, &y);
    if (hedefG > 0 && hedefY > 0 && (static_cast<UINT>(hedefG) != g || static_cast<UINT>(hedefY) != y)) {
        f->CreateBitmapScaler(olcek.GetAddressOf());
        if (SUCCEEDED(olcek->Initialize(kaynak, static_cast<UINT>(hedefG), static_cast<UINT>(hedefY),
                                        WICBitmapInterpolationModeFant))) {
            kaynak = olcek.Get();
            g = static_cast<UINT>(hedefG);
            y = static_cast<UINT>(hedefY);
        }
    }
    r.g = static_cast<int>(g);
    r.y = static_cast<int>(y);
    r.bgra.assign(static_cast<size_t>(g) * y * 4, 0);
    if (FAILED(hr = kaynak->CopyPixels(nullptr, g * 4, static_cast<UINT>(r.bgra.size()), r.bgra.data()))) {
        hata = Hr("pikseller okunamadı", hr);
        return false;
    }
    return true;
}

bool PngYaz(const std::wstring& yol, int g, int y, const uint8_t* piksel, bool bgr, std::string& hata) {
    ComPtr<IWICImagingFactory> f = Fabrika(hata);
    if (!f) return false;
    std::vector<uint8_t> satirlar(static_cast<size_t>(g) * y * 3);
    for (size_t i = 0, n = static_cast<size_t>(g) * y; i < n; ++i) {
        const uint8_t* p = piksel + i * 4;
        uint8_t* q = satirlar.data() + i * 3;
        q[0] = bgr ? p[0] : p[2];
        q[1] = p[1];
        q[2] = bgr ? p[2] : p[0];
    }
    ComPtr<IWICStream> akis;
    ComPtr<IWICBitmapEncoder> kodlayici;
    ComPtr<IWICBitmapFrameEncode> kare;
    HRESULT hr = f->CreateStream(akis.GetAddressOf());
    if (SUCCEEDED(hr)) hr = akis->InitializeFromFilename(yol.c_str(), GENERIC_WRITE);
    if (SUCCEEDED(hr)) hr = f->CreateEncoder(GUID_ContainerFormatPng, nullptr, kodlayici.GetAddressOf());
    if (SUCCEEDED(hr)) hr = kodlayici->Initialize(akis.Get(), WICBitmapEncoderNoCache);
    if (SUCCEEDED(hr)) hr = kodlayici->CreateNewFrame(kare.GetAddressOf(), nullptr);
    if (SUCCEEDED(hr)) hr = kare->Initialize(nullptr);
    if (SUCCEEDED(hr)) hr = kare->SetSize(static_cast<UINT>(g), static_cast<UINT>(y));
    WICPixelFormatGUID bicim = GUID_WICPixelFormat24bppBGR;
    if (SUCCEEDED(hr)) hr = kare->SetPixelFormat(&bicim);
    if (SUCCEEDED(hr) && bicim != GUID_WICPixelFormat24bppBGR) hr = E_FAIL;
    if (SUCCEEDED(hr))
        hr = kare->WritePixels(static_cast<UINT>(y), static_cast<UINT>(g) * 3, static_cast<UINT>(satirlar.size()),
                               satirlar.data());
    if (SUCCEEDED(hr)) hr = kare->Commit();
    if (SUCCEEDED(hr)) hr = kodlayici->Commit();
    if (FAILED(hr)) {
        hata = Hr("PNG yazılamadı", hr);
        return false;
    }
    return true;
}

}  // namespace op4
