// op4 C — arayüz yerelleştirmesi (kaynak/arayuz/dil.*, dil_tablosu.cpp): komut kataloğunun görünen bütün metinleri
// (sekmeler, şerit grupları, etiketler, ipuçları) ve şablon başlıkları İngilizce tabloda bulunur; biçim dizgilerinin
// belirteçleri iki dilde aynıdır; sayı biçimi (ondalık virgül / nokta, ince boşluklu binlik, kot).
// dil.cpp ve dil_tablosu.cpp ImGui'ye bağlı olmadığından sınamaya doğrudan katılır.
#include <doctest/doctest.h>

#include <nlohmann/json.hpp>
#include <regex>
#include <set>
#include <string>

#include "../../kaynak/arayuz/dil.cpp"
#include "../../kaynak/arayuz/dil_tablosu.cpp"
#include "cekirdek/komut.h"
#include "sinama_yardim.h"

using namespace op4;

namespace {
std::string Belirtecler(const std::string& s) {
    std::string o;
    static const std::regex r("%[-+ #0]*[0-9.*]*(zu|lld|ll|l)?[diufsxXcp%]");
    for (auto i = std::sregex_iterator(s.begin(), s.end(), r); i != std::sregex_iterator(); ++i) o += i->str() + "|";
    return o;
}
}  // namespace

TEST_CASE("arayüz dili: komut kataloğu ve şablonların görünen metinleri İngilizce tabloda") {
    KomutYoneticisi k;
    std::string hata;
    REQUIRE_MESSAGE(k.KatalogYukle(sinama::Op4Dosyasi("veri/komutlar.json"), hata), hata);
    size_t n = 0;
    const CeviriGirdisi* t = CeviriTablosu(n);
    std::set<std::string> anahtar;
    for (size_t i = 0; i < n; ++i) {
        CHECK_MESSAGE(anahtar.insert(t[i].tr).second, "yinelenen anahtar: " << t[i].tr);
        CHECK_MESSAGE(Belirtecler(t[i].tr) == Belirtecler(t[i].en), "biçim belirteçleri farklı: " << t[i].tr);
    }
    // Dil bağımsız etiketler (simge / kısaltma) çevrilmez.
    const std::set<std::string> notr = {"N / V / M"};
    auto denetle = [&](const std::string& s, const char* nerede) {
        if (s.empty() || notr.count(s)) return;
        CHECK_MESSAGE(anahtar.count(s), nerede << ": çevirisi yok: " << s);
    };
    for (const std::string& s : k.Sekmeler()) denetle(s, "sekme");
    for (const KomutTanimi& d : k.Tanimlar()) {
        denetle(d.etiket, "etiket");
        denetle(d.ipucu, "ipucu");
        if (d.serit) denetle(d.serit->grup, "şerit grubu");
    }
    const std::string dizin = sinama::Op4Dosyasi("veri/sablonlar/dizin.json");
    REQUIRE(!dizin.empty());
    const nlohmann::json j = nlohmann::json::parse(dizin);
    for (const nlohmann::json& s : j["sablonlar"]) {
        std::string b = s["baslik"].get<std::string>();
        const size_t p = b.find(" (");
        if (p != std::string::npos) b.resize(p);
        denetle(b, "şablon");
    }
    DilAyarla(ArayuzDili::Ingilizce);
    CHECK(std::string(Tr("Dosya")) == "File");
    CHECK(Trf("%zu seçili", size_t{6}) == "6 selected");
    CHECK(std::string(Tr("bilinmeyen metin")) == "bilinmeyen metin");
    DilAyarla(ArayuzDili::Turkce);
    CHECK(std::string(Tr("Dosya")) == "Dosya");
}

TEST_CASE("arayüz dili: sayı biçimi") {
    SayiBicimiAyarla(',', true);
    CHECK(Sayi(3.25, 2) == "3,25");
    CHECK(Sayi(1842.0, 0) == "1 842");
    CHECK(Sayi(123.0, 0) == "123");
    CHECK(Kot(9.0) == "+9,00");
    CHECK(Kot(0.0) == "±0,00");
    SayiBicimiAyarla('.', false);
    CHECK(Sayi(12345.678, 3) == "12345.678");
    CHECK(Kot(-1.5) == "−1.50");
    SayiBicimiAyarla(',', true);
}
