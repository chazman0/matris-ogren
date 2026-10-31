// op4 arayüzü — Türkçe → İngilizce çeviri tablosu (dil.h). Anahtar: arayüzdeki Türkçe kaynak metin.
#include <cstddef>

namespace op4 {

struct CeviriGirdisi {
    const char* tr;
    const char* en;
};

namespace {
const CeviriGirdisi kTablo[] = {
    {"Dosya", "File"},
};
}  // namespace

const CeviriGirdisi* CeviriTablosu(size_t& n) {
    n = sizeof(kTablo) / sizeof(kTablo[0]);
    return kTablo;
}

}  // namespace op4
