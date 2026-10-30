// op4 model çekirdeği modülü (B; sözleşme S23, kabul B8). QuickJS çekirdeğini kurar, Hizmetler::cekirdek'e bağlar; geri al /
// yinele / denetle komutlarını bağlar. Platformdan bağımsızdır (Linux sınamaları da kullanır).
//
// Ayarlar: geri al sınırları Ayarlar::cekirdek'ten (geriAlAdim, geriAlMb). Geliştirici kipi: OP4_JS_DIZINI ortam değişkeni
// depo kökünü gösterirse JS kaynakları gömülü olanlar yerine oradan okunur (docs/*.js, op4/js/*.js düzenle-yeniden aç).
// Menü adları: "Geri al: <ad>" metni için C GeriAlBilgisi().geriAlAdi / yineleAdi'yı kullanır (komut kaydının etiketi sabittir).
#include <cstdlib>
#include <memory>
#include <string>

#include "cekirdek/kabuk.h"

namespace op4 {

namespace {

std::string OrtamDegiskeni(const char* ad) {
#if defined(_MSC_VER)
    char* d = nullptr;
    size_t n = 0;
    std::string s;
    if (_dupenv_s(&d, &n, ad) == 0 && d) s = d;
    std::free(d);
    return s;
#else
    const char* d = std::getenv(ad);
    return d ? std::string(d) : std::string();
#endif
}

void DenetimYaz(Hizmetler& h, const DenetimSonucu& d) {
    if (!h.bildirim) return;
    if (d.gecerli && d.uyarilar.empty()) {
        h.bildirim->KomutYaz("Denetim: sorun bulunmadı.");
    } else {
        h.bildirim->KomutYaz("Denetim: " + std::to_string(d.uyarilar.size()) + " uyarı.");
        for (const std::string& u : d.uyarilar) h.bildirim->KomutYaz("  " + u);
    }
    if (d.serbestDugum) h.bildirim->KomutYaz("Serbest (aksa bağlı olmayan) düğüm: " + std::to_string(d.serbestDugum));
}

}  // namespace

void CekirdekModuluKur(Hizmetler& h, ModulOrtami& o) {
    CekirdekAyari ayar;
    ayar.deterministikSaat = o.testKipi;
    ayar.gunluk = o.gunluk;
    ayar.jsDizini = OrtamDegiskeni("OP4_JS_DIZINI");
    if (h.ayarlar) {
        ayar.geriAlAdim = h.ayarlar->cekirdek.geriAlAdim;
        ayar.geriAlMb = h.ayarlar->cekirdek.geriAlMb;
    }
    std::string hata;
    std::shared_ptr<ModelCekirdegi> c(ModelCekirdegiOlustur(ayar, hata).release());
    if (!c) {
        if (o.gunluk) o.gunluk("HATA: model çekirdeği kurulamadı: " + hata);
        return;
    }
    h.cekirdek = o.Tut(c);
    if (!h.komutlar) return;

    KomutIsleyici geriAl;
    geriAl.calistir = [](KomutBaglami& b) { GeriAlUygula(b.h); };
    geriAl.kullanilamazNedeni = [](const Hizmetler& x) {
        return x.cekirdek && x.cekirdek->GeriAlBilgisi().geriAlinabilir ? std::string() : std::string("Geri alınacak işlem yok");
    };
    h.komutlar->Bagla("duzenle.geri_al", geriAl);
    KomutIsleyici yinele;
    yinele.calistir = [](KomutBaglami& b) { YineleUygula(b.h); };
    yinele.kullanilamazNedeni = [](const Hizmetler& x) {
        return x.cekirdek && x.cekirdek->GeriAlBilgisi().yinelenebilir ? std::string() : std::string("Yinelenecek işlem yok");
    };
    h.komutlar->Bagla("duzenle.yinele", yinele);
    KomutIsleyici denetle;
    denetle.calistir = [](KomutBaglami& b) {
        if (b.h.cekirdek) DenetimYaz(b.h, b.h.cekirdek->Denetle());
    };
    denetle.kullanilamazNedeni = [](const Hizmetler& x) {
        return x.cekirdek && !x.cekirdek->Ozet().bos ? std::string() : std::string("Model boş: denetlenecek eleman yok");
    };
    h.komutlar->Bagla("model.denetle", denetle);
}

}  // namespace op4
