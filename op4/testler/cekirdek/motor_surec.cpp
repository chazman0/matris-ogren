// A sınamaları: alt süreç + iki boru (platform/surec.h, S14; surec_posix.cpp / surec_win.cpp). Python yorumlayıcısı küçük
// betiklerle çocuk süreç olarak kullanılır (motor_sinama_yardim.h).
#include <doctest/doctest.h>
#include <nlohmann/json.hpp>

#include <fstream>
#include <sstream>
#include <string>

#include "motor_sinama_yardim.h"
#include "platform/surec.h"

using namespace op4;
using nlohmann::json;

namespace {

// Çocuk: istek borusunu sonuna dek okur, ters çevirip yanıt borusuna yazar; argv / ortam / cwd / açık fd'leri JSON olarak
// başa ekler. stdout / stderr'e birer satır yazar. Çıkış kodu OP4_CIKIS.
const char* const kBetik = R"PY(
import json, os, sys
def ac(h, yaz):
    h = int(h)
    if os.name == "nt":
        import msvcrt
        h = msvcrt.open_osfhandle(h, os.O_WRONLY if yaz else os.O_RDONLY)
    return os.fdopen(h, "wb" if yaz else "rb", 0)
r, w = ac(sys.argv[1], False), ac(sys.argv[2], True)
print("stdout satiri", flush=True)
sys.stderr.write("stderr satiri\n"); sys.stderr.flush()
fdler = sorted(int(x) for x in os.listdir("/proc/self/fd")) if os.path.isdir("/proc/self/fd") else []
veri = r.read()
bilgi = {"argv": sys.argv[3:], "ortam": os.environ.get("OP4_DENEME"), "cwd": os.getcwd(), "fd": fdler}
w.write((json.dumps(bilgi, ensure_ascii=False) + "\n").encode("utf-8") + veri[::-1])
w.close()
sys.exit(int(os.environ.get("OP4_CIKIS", "0")))
)PY";

std::string HepsiniOku(Surec& s) {
    std::string t;
    char b[4096];
    for (;;) {
        const long long n = s.Oku(b, sizeof(b));
        if (n <= 0) break;
        t.append(b, static_cast<size_t>(n));
    }
    return t;
}

}  // namespace

TEST_CASE("S14 Surec: borular, yer tutucular, argv, ortam, cwd, stdout/stderr dosyası, çıkış kodu") {
    if (!sinama::PythonVar()) return;
    sinama::GeciciDizin d("surec");
    const std::string cikti = d.Utf8() + "/cocuk çıktısı.log";
    SurecAyari a;
    a.program = sinama::PythonYolu();
    const std::string tuhaf = "a b \"c\" ş\\ ğ\\\\";
    a.argumanlar = {"-c", kBetik, "{istek}", "{yanit}", tuhaf, "", "son"};
    a.ortam = {{"OP4_DENEME", "Şükrü ğ"}, {"OP4_CIKIS", "5"}, {"PYTHONUTF8", "1"}};
    a.calismaDizini = d.Utf8();
    a.ciktiDosyasi = cikti;
    auto s = SurecOlustur();
    std::string hata;
    REQUIRE_MESSAGE(s->Baslat(a, hata), hata);
    CHECK(s->Kimlik() > 0);
    CHECK(s->Calisiyor());
    std::string h2;
    CHECK_FALSE(s->Baslat(a, h2));  // ikinci kez başlatılamaz
    const std::string veri = "merhaba dünya";
    REQUIRE(s->Yaz(veri.data(), veri.size()));
    s->YazmayiKapat();
    const std::string gelen = HepsiniOku(*s);
    int kod = -1;
    REQUIRE(s->Bekle(10000, kod));
    CHECK(kod == 5);
    CHECK_FALSE(s->Calisiyor());
    const size_t sat = gelen.find('\n');
    REQUIRE(sat != std::string::npos);
    const json bilgi = json::parse(gelen.substr(0, sat));
    CHECK(bilgi["argv"] == json::array({tuhaf, "", "son"}));
    CHECK(bilgi["ortam"] == "Şükrü ğ");
    CHECK(std::filesystem::equivalent(std::filesystem::path(std::u8string(
                                          reinterpret_cast<const char8_t*>(bilgi["cwd"].get<std::string>().c_str()))),
                                      d.yol));
#ifndef _WIN32
    // Çocuk yalnız 0, 1, 2 ve iki boru ucunu (3, 4) devralır (+ listdir'in kendi tanımlayıcısı).
    std::vector<int> fd = bilgi["fd"].get<std::vector<int>>();
    CHECK(fd.size() <= 6);
    for (const int x : fd) CHECK((x <= 4 || x == fd.back()));
#endif
    std::string ters(veri.rbegin(), veri.rend());
    CHECK(gelen.substr(sat + 1) == ters);
    std::ifstream f(std::filesystem::path(std::u8string(reinterpret_cast<const char8_t*>(cikti.c_str()))));
    std::stringstream ss;
    ss << f.rdbuf();
    CHECK(ss.str().find("stdout satiri") != std::string::npos);
    CHECK(ss.str().find("stderr satiri") != std::string::npos);
}

TEST_CASE("S14 Surec: bulunamayan program, sonlandırma, kapanan boruya yazma") {
    auto s = SurecOlustur();
    std::string hata;
    SurecAyari yok;
    yok.program = "/yok/boyle/bir/program";
    CHECK_FALSE(s->Baslat(yok, hata));
    CHECK(hata.find("bulunamadı") != std::string::npos);
    CHECK_FALSE(s->Calisiyor());
    int kod = 0;
    CHECK(s->Bekle(0, kod));
    if (!sinama::PythonVar()) return;
    SurecAyari a;
    a.program = sinama::PythonYolu();
    a.argumanlar = {"-c", "import time; time.sleep(60)", "{istek}", "{yanit}"};
    auto u = SurecOlustur();
    REQUIRE_MESSAGE(u->Baslat(a, hata), hata);
    CHECK(u->Calisiyor());
    CHECK_FALSE(u->Bekle(50, kod));
    const double t0 = sinama::SimdiMs();
    u->Sonlandir();
    REQUIRE(u->Bekle(5000, kod));
    CHECK(sinama::SimdiMs() - t0 < 3000);
    CHECK(kod != 0);
    CHECK_FALSE(u->Calisiyor());
    char b[8];
    CHECK(u->Oku(b, sizeof(b)) == 0);  // karşı uç kapandı
    // Ölmüş çocuğun borusuna yazmak süreci düşürmez (SIGPIPE yok sayılır), false döner.
    std::string buyuk(1 << 20, 'x');
    bool yazildi = true;
    for (int i = 0; i < 4 && yazildi; ++i) yazildi = u->Yaz(buyuk.data(), buyuk.size());
    CHECK_FALSE(yazildi);
}
