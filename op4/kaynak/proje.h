// op4 — proje dosyası (.op4, UTF-8 JSON) kaydet / aç ve Windows dosya pencereleri.
// İskelet aşamasında yalnız kamera ve görünüm ayarları taşınır; "model" alanı genel modelin (yapi_serbest, surum 3)
// JSON'u için ayrılmıştır ve sonraki adımda doldurulacak.
#pragma once

#include <windows.h>

#include <string>

#include "grafik.h"
#include "kamera.h"

namespace op4 {

struct Proje {
    std::wstring yol;  // boş: kaydedilmemiş
    Kamera kamera;
    SahneAyari ayar;
};

bool ProjeKaydet(const std::wstring& yol, const Proje& p, std::string& hata);
bool ProjeAc(const std::wstring& yol, Proje& p, std::string& hata);
// Dosya seçme penceresi (IFileOpenDialog / IFileSaveDialog). İptal: false.
bool DosyaSec(HWND sahip, bool kaydet, const std::wstring& oneri, std::wstring& yol);

}  // namespace op4
