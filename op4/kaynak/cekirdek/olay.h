// op4 çekirdek sözleşmesi — olay (gözlemci listesi) (sözleşme S2).
//
// Paketler birbirinin koduna dokunmadan haberleşir: model değişince (çekirdek), seçim değişince (arayüz), sonuç gelince
// (çözüm), belge kaydedilince (dosya) ilgili Olay yayınlanır; ilgilenen modül abone olur. Bütün olaylar UI iş parçacığında
// yayınlanır ve dinlenir (iş parçacığı güvenli DEĞİLDİR; başka iş parçacığı sonucu UI kuyruğuna koyar, bkz. Hizmetler).
// Yayın sırası abone olma sırasıdır. Yayın sırasında abone eklemek ya da bırakmak güvenlidir (o yayını etkilemez).
#pragma once

#include <cstdint>
#include <functional>
#include <utility>
#include <vector>

namespace op4 {

template <class... A>
class Olay {
public:
    using Isleyici = std::function<void(const A&...)>;
    using Abonelik = uint64_t;  // 0 geçersiz

    Abonelik Abone(Isleyici f) {
        const Abonelik no = ++sonNo_;
        aboneler_.emplace_back(no, std::move(f));
        return no;
    }
    void Birak(Abonelik no) {
        for (auto i = aboneler_.begin(); i != aboneler_.end(); ++i)
            if (i->first == no) {
                aboneler_.erase(i);
                return;
            }
    }
    void Yay(const A&... a) const {
        const auto kopya = aboneler_;  // yayın sırasında liste değişebilir
        for (const auto& [no, f] : kopya)
            if (f) f(a...);
    }
    size_t AboneSayisi() const { return aboneler_.size(); }

private:
    std::vector<std::pair<Abonelik, Isleyici>> aboneler_;
    Abonelik sonNo_ = 0;
};

}  // namespace op4
