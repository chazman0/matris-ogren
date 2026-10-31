// op4 arayüzü — çizim yardımcıları ve özel bileşenler (Atölye tuval.py karşılıkları: taban, simge, sevron, onay kutusu,
// radyo, anahtar, kısayol rozeti, düğme, açılır kutu, giriş kutusu, dikey yazı, gölge). Koordinatlar MANTIKSAL pikseldir
// (taslak uret.py ile aynı sayılar); her çağrı ölçekle (DPI / 96) çarpar. Metin konumu TABAN ÇİZGİSİdir; Taban(y, h, boy)
// h yüksekliğindeki satırda dikey ortalanmış taban çizgisini verir (Inter büyük harf ≈ 0,727 em).
#pragma once

#include <string>
#include <string_view>
#include <vector>

#include "arayuz/tema.h"
#include "arayuz/yazi.h"
#include "imgui.h"

namespace op4 {

inline float Taban(float y, float h, float boy) { return y + h / 2 + 0.36f * boy; }

struct Ciz {
    ImDrawList* dl = nullptr;
    float olcek = 1.0f;
    const Yazilar* yazi = nullptr;

    float S(float v) const { return v * olcek; }
    ImVec2 P(float x, float y) const { return ImVec2(x * olcek, y * olcek); }
    const tema::Renkler& R() const { return tema::Etkin().r; }

    ImFont* F(tema::Agirlik a) const { return yazi ? yazi->Al(a) : ImGui::GetFont(); }
    float Gen(std::string_view s, float boy, tema::Agirlik a = tema::Agirlik::Normal) const;
    // Sığmayan metni "…" ile kısaltır.
    std::string Kes(std::string_view s, float maxw, float boy, tema::Agirlik a = tema::Agirlik::Normal) const;
    float Yazi(float x, float taban, std::string_view s, float boy, tema::Agirlik a, uint32_t renk, float maxw = -1) const;
    float YaziOrta(float x, float taban, std::string_view s, float boy, tema::Agirlik a, uint32_t renk) const;
    float YaziSag(float x, float taban, std::string_view s, float boy, tema::Agirlik a, uint32_t renk) const;
    // Saat yönünde 90° döndürülmüş yazı (yukarıdan aşağı okunur); (x, y) döndürülmüş kutunun sol üstü.
    void YaziDikey(float x, float y, std::string_view s, float boy, tema::Agirlik a, uint32_t renk) const;

    void Dikd(float x, float y, float w, float h, uint32_t renk) const;
    void Yatay(float x0, float x1, float y, uint32_t renk, float lw = 1) const { Dikd(x0, y, x1 - x0, lw, renk); }
    void Dusey(float x, float y0, float y1, uint32_t renk, float lw = 1) const { Dikd(x, y0, lw, y1 - y0, renk); }
    // Yuvarlatılmış dikdörtgen: dolgu ve / veya kenar (kenar içe çizilir). Renk 0 = yok.
    void Yuv(float x, float y, float w, float h, float r, uint32_t dolgu, uint32_t kenar = 0, float lw = 1) const;
    void Golge(float x, float y, float w, float h, float r = 4, float yaricap = 6, float alfa = 0.18f, float dy = 2) const;
    void Daire(float cx, float cy, float r, uint32_t dolgu, uint32_t kenar = 0, float lw = 1) const;
    void Cizgi(float x0, float y0, float x1, float y1, uint32_t renk, float lw = 1) const;
    void Gradyan(float x, float y, float w, float h, uint32_t ust, uint32_t alt) const;
    // Simge: (cx, cy) merkez (Atölye tuval.simge). Ikon: sol üst köşe.
    void Simge(std::string_view ad, float cx, float cy, float boy, uint32_t renk, float kalem = 1.5f) const;
    void Ikon(std::string_view ad, float x, float y, float boy, uint32_t renk, float kalem = 1.5f) const {
        Simge(ad, x + boy / 2, y + boy / 2, boy, renk, kalem);
    }
    void Sevron(float cx, float cy, int yon, float boy = 10, uint32_t renk = 0) const;  // yon 0 aşağı, 1 sağ, 2 üst, 3 sol

    // ---- bileşenler ----
    void OnayKutusu(float x, float y, bool isaretli, float boy = 12, bool soluk = false) const;
    void Radyo(float cx, float cy, bool secili, float r = 6) const;
    void Anahtar(float x, float y, bool acik, float w = 26, float h = 14, bool soluk = false) const;
    float Kisayol(float x, float y, std::string_view metin, float boy = 10, float h = 15) const;  // genişlik
    void Dugme(float x, float y, float w, float h, std::string_view metin, bool birincil = false, float boy = 12,
               bool soluk = false, bool uzerinde = false) const;
    void Acilir(float x, float y, float w, float h, std::string_view metin, float boy = 12, bool odak = false,
                bool salt = false, uint32_t renk = 0) const;
    void Giris(float x, float y, float w, float h, std::string_view metin, float boy = 12, bool odak = false,
               uint32_t renk = 0, bool sag = false) const;
    // Rozet (yuvarlak): döndürür genişlik.
    float Rozet(float x, float y, std::string_view s, float boy, uint32_t zemin, uint32_t renk, float h = 14) const;
    // İpucu kartı: beyaz kart, vurgu kenarı (imleç ipucu) — (x, y) sol üst.
    void IpucuKarti(float x, float y, std::string_view s, float boy = 10) const;
};

// Etkileşim: mantıksal dikdörtgende görünmez düğme (ImGui öğesi). Döndürür: tıklandı mı.
bool Tiklama(const Ciz& c, const char* id, float x, float y, float w, float h, int fareTuslari = 1);
// Segmentli denetim (Atölye · Modern §6): zemin2 iz (6 px), 2 px iç boşluk; seçili parça beyaz kabarık hap (nötr tür)
// ya da vurgu dolgulu (vurgu türü: yalnız işlem kapsamını değiştiren anahtarlar, kat kapsamı). esitW > 0 ise toplam
// genişlik eşit bölünür, değilse her parça metin + 2·dolgu. Döndürür: tıklanan parça (yoksa -1); toplamW çizilen genişlik.
int Segmentli(const Ciz& c, const char* id, float x, float y, float h, const std::vector<std::string>& ogeler, int secili,
              bool vurgu, float boy = 11, float esitW = 0, float* toplamW = nullptr, bool etkin = true);
// Çip (§6): 20 px, 6 px; açık (vurgu tonu + nokta), kapalı (1 px çizgi, metin3). Döndürür genişlik.
float Cip(const Ciz& c, float x, float y, float h, std::string_view metin, bool acik, bool nokta = true, float boy = 10);
// Üzerinde bekleyince ipucu (son öğe için; gecikmeli koyu balon, ekranda kalır).
void OgeIpucu(const Ciz& c, std::string_view metin, std::string_view kisayol = {});

}  // namespace op4
