// op4 çekirdek — seçme dizini. TASLAK (sözleşme S8): izdüşüm ve ışın yardımcıları ile Sinir() tamdır; BVH sorguları
// (EnYakin, Adaylar, Pencere, IsinVurusu) boş döner. Uygulayan: C (arayuz-goruntu), Faz 1 iş 1.4.
#include "cekirdek/secme.h"

#include <cmath>

namespace op4 {
namespace {

// 4×4 genel ters (kofaktör), double. Tekilse false.
bool Ters4(const std::array<double, 16>& m, std::array<double, 16>& t) {
    std::array<double, 16> inv{};
    inv[0] = m[5] * m[10] * m[15] - m[5] * m[11] * m[14] - m[9] * m[6] * m[15] + m[9] * m[7] * m[14] + m[13] * m[6] * m[11] - m[13] * m[7] * m[10];
    inv[4] = -m[4] * m[10] * m[15] + m[4] * m[11] * m[14] + m[8] * m[6] * m[15] - m[8] * m[7] * m[14] - m[12] * m[6] * m[11] + m[12] * m[7] * m[10];
    inv[8] = m[4] * m[9] * m[15] - m[4] * m[11] * m[13] - m[8] * m[5] * m[15] + m[8] * m[7] * m[13] + m[12] * m[5] * m[11] - m[12] * m[7] * m[9];
    inv[12] = -m[4] * m[9] * m[14] + m[4] * m[10] * m[13] + m[8] * m[5] * m[14] - m[8] * m[6] * m[13] - m[12] * m[5] * m[10] + m[12] * m[6] * m[9];
    inv[1] = -m[1] * m[10] * m[15] + m[1] * m[11] * m[14] + m[9] * m[2] * m[15] - m[9] * m[3] * m[14] - m[13] * m[2] * m[11] + m[13] * m[3] * m[10];
    inv[5] = m[0] * m[10] * m[15] - m[0] * m[11] * m[14] - m[8] * m[2] * m[15] + m[8] * m[3] * m[14] + m[12] * m[2] * m[11] - m[12] * m[3] * m[10];
    inv[9] = -m[0] * m[9] * m[15] + m[0] * m[11] * m[13] + m[8] * m[1] * m[15] - m[8] * m[3] * m[13] - m[12] * m[1] * m[11] + m[12] * m[3] * m[9];
    inv[13] = m[0] * m[9] * m[14] - m[0] * m[10] * m[13] - m[8] * m[1] * m[14] + m[8] * m[2] * m[13] + m[12] * m[1] * m[10] - m[12] * m[2] * m[9];
    inv[2] = m[1] * m[6] * m[15] - m[1] * m[7] * m[14] - m[5] * m[2] * m[15] + m[5] * m[3] * m[14] + m[13] * m[2] * m[7] - m[13] * m[3] * m[6];
    inv[6] = -m[0] * m[6] * m[15] + m[0] * m[7] * m[14] + m[4] * m[2] * m[15] - m[4] * m[3] * m[14] - m[12] * m[2] * m[7] + m[12] * m[3] * m[6];
    inv[10] = m[0] * m[5] * m[15] - m[0] * m[7] * m[13] - m[4] * m[1] * m[15] + m[4] * m[3] * m[13] + m[12] * m[1] * m[7] - m[12] * m[3] * m[5];
    inv[14] = -m[0] * m[5] * m[14] + m[0] * m[6] * m[13] + m[4] * m[1] * m[14] - m[4] * m[2] * m[13] - m[12] * m[1] * m[6] + m[12] * m[2] * m[5];
    inv[3] = -m[1] * m[6] * m[11] + m[1] * m[7] * m[10] + m[5] * m[2] * m[11] - m[5] * m[3] * m[10] - m[9] * m[2] * m[7] + m[9] * m[3] * m[6];
    inv[7] = m[0] * m[6] * m[11] - m[0] * m[7] * m[10] - m[4] * m[2] * m[11] + m[4] * m[3] * m[10] + m[8] * m[2] * m[7] - m[8] * m[3] * m[6];
    inv[11] = -m[0] * m[5] * m[11] + m[0] * m[7] * m[9] + m[4] * m[1] * m[11] - m[4] * m[3] * m[9] - m[8] * m[1] * m[7] + m[8] * m[3] * m[5];
    inv[15] = m[0] * m[5] * m[10] - m[0] * m[6] * m[9] - m[4] * m[1] * m[10] + m[4] * m[2] * m[9] + m[8] * m[1] * m[6] - m[8] * m[2] * m[5];
    const double det = m[0] * inv[0] + m[1] * inv[4] + m[2] * inv[8] + m[3] * inv[12];
    if (std::fabs(det) < 1e-300) return false;
    for (size_t i = 0; i < 16; ++i) t[i] = inv[i] / det;
    return true;
}

void Carp4(const std::array<double, 16>& m, const double v[4], double o[4]) {
    for (int r = 0; r < 4; ++r) o[r] = m[r * 4] * v[0] + m[r * 4 + 1] * v[1] + m[r * 4 + 2] * v[2] + m[r * 4 + 3] * v[3];
}

}  // namespace

bool GorusIzdusumu::Izdusur(V3d p, double& px, double& py) const {
    const double v[4] = {p.x, p.y, p.z, 1.0};
    double o[4];
    Carp4(gorunumIzdusum, v, o);
    if (o[3] <= 1e-12) return false;
    px = (o[0] / o[3] * 0.5 + 0.5) * genislik;
    py = (0.5 - o[1] / o[3] * 0.5) * yukseklik;
    return true;
}

Isin PikselIsini(const GorusIzdusumu& g, double px, double py) {
    std::array<double, 16> t{};
    if (!Ters4(g.gorunumIzdusum, t)) return {g.goz, {0, 0, -1}};
    const double nx = px / g.genislik * 2.0 - 1.0, ny = 1.0 - py / g.yukseklik * 2.0;
    // Ters-Z: yakın düzlem derinlik 1, uzak (sonsuz) 0. İki noktayı geri izdüşür.
    auto geri = [&](double z) {
        const double v[4] = {nx, ny, z, 1.0};
        double o[4];
        Carp4(t, v, o);
        return o[3] != 0.0 ? V3d{o[0] / o[3], o[1] / o[3], o[2] / o[3]} : V3d{o[0], o[1], o[2]};
    };
    const V3d yakin = geri(1.0), uzak = geri(0.5);
    return {g.ortografik ? yakin : g.goz, Birim(uzak - yakin)};
}

struct SecmeDizini::Ic {
    SahnePtr sahne = BosSahne();
};

SecmeDizini::SecmeDizini() : ic_(std::make_unique<Ic>()) {}
SecmeDizini::~SecmeDizini() = default;
SecmeDizini::SecmeDizini(SecmeDizini&&) noexcept = default;
SecmeDizini& SecmeDizini::operator=(SecmeDizini&&) noexcept = default;

void SecmeDizini::Kur(SahnePtr sahne) { ic_->sahne = sahne ? std::move(sahne) : BosSahne(); }
uint64_t SecmeDizini::SahneSurumu() const { return ic_->sahne->surum; }
const SahnePtr& SecmeDizini::Sahne() const { return ic_->sahne; }

std::optional<SecmeVurusu> SecmeDizini::EnYakin(const GorusIzdusumu&, double, double, const SecmeAyari&) const {
    return std::nullopt;  // TASLAK (C)
}
std::vector<SecmeVurusu> SecmeDizini::Adaylar(const GorusIzdusumu&, double, double, const SecmeAyari&) const {
    return {};  // TASLAK (C)
}
std::vector<ElemanKimligi> SecmeDizini::Pencere(const GorusIzdusumu&, double, double, double, double, PencereKipi,
                                                const SecmeAyari&) const {
    return {};  // TASLAK (C)
}
std::optional<SecmeVurusu> SecmeDizini::IsinVurusu(const Isin&, const SecmeAyari&) const {
    return std::nullopt;  // TASLAK (C)
}

Kutu3d SecmeDizini::Sinir(const std::vector<ElemanKimligi>& kimlikler) const {
    Kutu3d k;
    for (const ElemanKimligi& e : kimlikler) k.Kapsa(ic_->sahne->Sinir(e));
    return k;
}

}  // namespace op4
