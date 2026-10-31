// op4 çekirdek — komut satırı / hızlı başlat modeli (MIMARI §5.4, §12.1; ARAYUZ_ILKELERI 3 ve 25). Sahibi: C.
//
// Platformdan bağımsızdır; ImGui çizimi kaynak/arayuz/komut_cubugu.cpp'dedir. Tanımlar komut kayıt defterindendir (S20):
// Türkçe ad + İngilizce takma adlar, Türkçe katlamalı önek ve alt dizi tamamlama. Bu sınıf yalnız oturum durumunu tutar:
// satır geçmişi (yukarı / aşağı ok), son çalıştırılan komutlar ("Son" sekmesi) ve öneri listesi süzgeci.
#pragma once

#include <cstddef>
#include <cstdint>
#include <deque>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

#include "cekirdek/komut.h"

namespace op4 {

// Hızlı başlat sonuç sekmeleri (ARAYUZ_ILKELERI 3).
enum class OneriKumesi : uint8_t { Tumu = 0, Son = 1, Serit = 2, Menu = 3 };

class KomutSatiri {
public:
    explicit KomutSatiri(size_t enFazlaGecmis = 100) : enFazla_(enFazlaGecmis) {}

    // ---- satır geçmişi -------------------------------------------------------------------------------------------------
    void GecmiseEkle(std::string_view satir);           // boş ve ardışık tekrar eklenmez
    const std::deque<std::string>& Gecmis() const { return gecmis_; }  // en eski başta
    // Yukarı ok: bir önceki satır (ilk basışta şimdiki girdi saklanır); geçmiş bitince nullopt.
    std::optional<std::string> Onceki(std::string_view simdiki);
    // Aşağı ok: bir sonraki; en sona gelince saklanan girdi döner; gezinmiyorsa nullopt.
    std::optional<std::string> Sonraki();
    void GezinmeyiBitir() { konum_ = -1; }

    // ---- son komutlar --------------------------------------------------------------------------------------------------
    void KomutCalisti(std::string_view id);              // en yeni başa; tekrarsız; en çok 12
    const std::deque<std::string>& SonKomutlar() const { return son_; }

    // ---- öneriler ------------------------------------------------------------------------------------------------------
    // yazilan boşsa: Son kümesi (yoksa hızlı erişim komutları). Değilse KomutYoneticisi::Tamamla sırası (önek → alt
    // dizi), kümeye göre süzülmüş: Son = son komutlar, Şerit = şeritte yeri olanlar, Menü = menü yolu olanlar.
    std::vector<const KomutTanimi*> Oneriler(const KomutYoneticisi& k, std::string_view yazilan, OneriKumesi kume,
                                             size_t enFazla = 10) const;

    // Enter: satırı çalıştırır (boşsa tekrarlanır son komut). Başarısızsa ileti öğretici hata + yakın komutlar.
    // Başarılıysa satır geçmişe, komut son komutlara eklenir.
    bool Calistir(KomutYoneticisi& k, Hizmetler& h, std::string_view satir, std::string& ileti);
    // Öneri listesinden seçilen komutu çalıştırır (argümansız).
    bool OneriCalistir(KomutYoneticisi& k, Hizmetler& h, const KomutTanimi& t, std::string& ileti);

private:
    size_t enFazla_;
    std::deque<std::string> gecmis_;
    std::deque<std::string> son_;
    int konum_ = -1;      // geçmişte gezinme konumu (−1 = gezinmiyor)
    std::string bekleyen_; // gezinmeye başlarken girdideki metin
};

}  // namespace op4
