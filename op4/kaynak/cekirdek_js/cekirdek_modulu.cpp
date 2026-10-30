// op4 model çekirdeği modülü (B). TASLAK (sözleşme S23): çekirdeği oluşturur, Hizmetler::cekirdek'e bağlar; geri al /
// yinele komutlarını bağlar. Platformdan bağımsızdır (Linux sınamaları da kullanır). Uygulayan: B, F1 iş 1.3.
#include <memory>

#include "cekirdek/kabuk.h"

namespace op4 {

void CekirdekModuluKur(Hizmetler& h, ModulOrtami& o) {
    CekirdekAyari ayar;
    ayar.deterministikSaat = o.testKipi;
    ayar.gunluk = o.gunluk;
    std::string hata;
    std::shared_ptr<ModelCekirdegi> c(ModelCekirdegiOlustur(ayar, hata).release());
    if (!c) {
        if (o.gunluk) o.gunluk("HATA: model çekirdeği kurulamadı: " + hata);
        return;
    }
    h.cekirdek = o.Tut(c);

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
}

}  // namespace op4
