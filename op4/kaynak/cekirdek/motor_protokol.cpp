// op4 çekirdek — hesap motoru tel protokolü kodlayıcısı / çözücüsü (sözleşme S12; tam uygulama).
// Sayı yazımı Python kodlayıcısıyla (op4/motor/op4_protokol.py) bayt bayt aynıdır: sure_ms "%.1f", oran tamsayı.
#include "cekirdek/motor_protokol.h"

#include <cmath>
#include <cstdio>
#include <cstdlib>

#include <nlohmann/json.hpp>

namespace op4::motor_protokolu {
namespace {

std::string Ondalik1(double v) {
    if (!std::isfinite(v)) v = 0;
    char b[64];
    std::snprintf(b, sizeof(b), "%.1f", v);
    return b;
}

std::string Tam(double oran) {
    if (!std::isfinite(oran)) oran = 0;
    return std::to_string(static_cast<long long>(std::llround(oran)));
}

void Ekle32(std::string& s, uint32_t n) {
    s += static_cast<char>(n & 0xFF);
    s += static_cast<char>((n >> 8) & 0xFF);
    s += static_cast<char>((n >> 16) & 0xFF);
    s += static_cast<char>((n >> 24) & 0xFF);
}

bool OnekAl(std::string_view& s, std::string_view onek) {
    if (s.substr(0, onek.size()) != onek) return false;
    s.remove_prefix(onek.size());
    return true;
}

}  // namespace

std::string JsonKacis(std::string_view s) {
    std::string o;
    o.reserve(s.size() + 8);
    for (const char ch : s) {
        const auto c = static_cast<unsigned char>(ch);
        switch (c) {
            case '"': o += "\\\""; break;
            case '\\': o += "\\\\"; break;
            case '\b': o += "\\b"; break;
            case '\f': o += "\\f"; break;
            case '\n': o += "\\n"; break;
            case '\r': o += "\\r"; break;
            case '\t': o += "\\t"; break;
            default:
                if (c < 0x20) {
                    char b[8];
                    std::snprintf(b, sizeof(b), "\\u%04x", static_cast<unsigned>(c));
                    o += b;
                } else {
                    o += ch;
                }
        }
    }
    return o;
}

bool CerceveEkle(std::string& cikti, std::string_view govde) {
    if (govde.empty() || govde.size() > EN_BUYUK_CERCEVE) return false;
    cikti.reserve(cikti.size() + 4 + govde.size());
    Ekle32(cikti, static_cast<uint32_t>(govde.size()));
    cikti.append(govde.data(), govde.size());
    return true;
}

CerceveDurumu CerceveAl(std::string& tampon, std::string& govde) {
    if (tampon.size() < 4) return CerceveDurumu::Eksik;
    const auto b = [&](size_t i) { return static_cast<uint32_t>(static_cast<unsigned char>(tampon[i])); };
    const uint32_t n = b(0) | (b(1) << 8) | (b(2) << 16) | (b(3) << 24);
    if (n == 0 || n > EN_BUYUK_CERCEVE) return CerceveDurumu::Bozuk;
    if (tampon.size() < 4 + static_cast<size_t>(n)) return CerceveDurumu::Eksik;
    govde.assign(tampon, 4, n);
    tampon.erase(0, 4 + static_cast<size_t>(n));
    return CerceveDurumu::Tamam;
}

std::string IstekIletisi(uint64_t id, std::string_view islem, std::string_view istekJson) {
    std::string s = "{\"tur\":\"istek\",\"id\":" + std::to_string(id) + ",\"islem\":\"" + JsonKacis(islem) + "\",\"istek\":";
    s.append(istekJson.data(), istekJson.size());
    s += '}';
    return s;
}

std::string IptalIletisi(uint64_t id) { return "{\"tur\":\"iptal\",\"id\":" + std::to_string(id) + "}"; }

std::string KapatIletisi() { return "{\"tur\":\"kapat\"}"; }

std::string HazirIletisi(std::string_view rol, bool basarili, long long pid, std::string_view python, double sureMs,
                         std::string_view surumJson, std::string_view hata) {
    std::string s = "{\"tur\":\"hazir\",\"rol\":\"" + JsonKacis(rol) + "\",\"basarili\":" + (basarili ? "true" : "false") +
                    ",\"pid\":" + std::to_string(pid) + ",\"python\":\"" + JsonKacis(python) + "\",\"sure_ms\":" +
                    Ondalik1(sureMs) + ",\"surum\":";
    s += surumJson.empty() ? std::string_view("{}") : surumJson;
    s += ",\"hata\":\"" + JsonKacis(hata) + "\"}";
    return s;
}

std::string DurumIletisi(std::string_view metin, double oran) {
    return "{\"tur\":\"durum\",\"metin\":\"" + JsonKacis(metin) + "\",\"oran\":" + Tam(oran) + "}";
}

std::string IlerlemeIletisi(uint64_t id, std::string_view metin, double oran) {
    return "{\"tur\":\"ilerleme\",\"id\":" + std::to_string(id) + ",\"metin\":\"" + JsonKacis(metin) + "\",\"oran\":" +
           Tam(oran) + "}";
}

std::string GunlukIletisi(std::string_view duzey, std::string_view metin) {
    return "{\"tur\":\"gunluk\",\"duzey\":\"" + JsonKacis(duzey) + "\",\"metin\":\"" + JsonKacis(metin) + "\"}";
}

std::string YanitIletisi(uint64_t id, double sureMs, std::string_view calistirMetni) {
    std::string s = "{\"tur\":\"yanit\",\"id\":" + std::to_string(id) + ",\"sure_ms\":" + Ondalik1(sureMs) + ",\"yanit\":";
    s.append(calistirMetni.data(), calistirMetni.size());
    s += '}';
    return s;
}

std::string HataYaniti(std::string_view ileti, std::string_view hataTuru) {
    return "{\"hata\":\"" + JsonKacis(ileti) + "\",\"hata_turu\":\"" + JsonKacis(hataTuru) + "\"}";
}

bool IletiCoz(std::string_view govde, GelenIleti& ileti, std::string& hata) {
    ileti = GelenIleti{};
    // yanit: bağlayıcı önek ile dilimlenir (gövde ayrıştırılmaz).
    std::string_view s = govde;
    if (OnekAl(s, "{\"tur\":\"yanit\",\"id\":")) {
        const size_t v1 = s.find(',');
        if (v1 == std::string_view::npos) {
            hata = "yanit iletisinde id sonrası ',' yok";
            return false;
        }
        const std::string idMetni(s.substr(0, v1));
        char* son = nullptr;
        ileti.id = std::strtoull(idMetni.c_str(), &son, 10);
        if (idMetni.empty() || *son != '\0') {
            hata = "yanit iletisinde geçersiz id";
            return false;
        }
        s.remove_prefix(v1);
        if (!OnekAl(s, ",\"sure_ms\":")) {
            hata = "yanit iletisinde sure_ms yok";
            return false;
        }
        const size_t v2 = s.find(",\"yanit\":");
        if (v2 == std::string_view::npos || s.empty() || s.back() != '}') {
            hata = "yanit iletisinde 'yanit' son alan değil";
            return false;
        }
        ileti.sureMs = std::strtod(std::string(s.substr(0, v2)).c_str(), nullptr);
        s.remove_prefix(v2 + 9);
        s.remove_suffix(1);
        ileti.yanit.assign(s.data(), s.size());
        ileti.tur = IletiTuru::Yanit;
        return true;
    }
    nlohmann::json j = nlohmann::json::parse(govde, nullptr, false);
    if (j.is_discarded() || !j.is_object()) {
        hata = "ileti JSON nesnesi değil";
        return false;
    }
    auto metin = [&](const char* ad) { return j.contains(ad) && j[ad].is_string() ? j[ad].get<std::string>() : std::string(); };
    const std::string tur = metin("tur");
    auto sayi = [&](const char* ad) { return j.contains(ad) && j[ad].is_number() ? j[ad].get<double>() : 0.0; };
    if (tur == "hazir") {
        ileti.tur = IletiTuru::Hazir;
        ileti.rol = metin("rol");
        ileti.basarili = j.contains("basarili") && j["basarili"].is_boolean() && j["basarili"].get<bool>();
        ileti.pid = j.contains("pid") && j["pid"].is_number_integer() ? j["pid"].get<long long>() : 0;
        ileti.python = metin("python");
        ileti.sureMs = sayi("sure_ms");
        ileti.surum = j.contains("surum") ? j["surum"].dump() : "{}";
        ileti.hata = metin("hata");
    } else if (tur == "durum") {
        ileti.tur = IletiTuru::Durum;
        ileti.metin = metin("metin");
        ileti.oran = sayi("oran");
    } else if (tur == "ilerleme") {
        ileti.tur = IletiTuru::Ilerleme;
        ileti.id = j.contains("id") && j["id"].is_number_unsigned() ? j["id"].get<uint64_t>() : 0;
        ileti.metin = metin("metin");
        ileti.oran = sayi("oran");
    } else if (tur == "gunluk") {
        ileti.tur = IletiTuru::Gunluk;
        ileti.duzey = metin("duzey");
        ileti.metin = metin("metin");
    } else {
        ileti.tur = IletiTuru::Bilinmiyor;
        ileti.metin = tur;
    }
    return true;
}

}  // namespace op4::motor_protokolu
