// op4 platform — atomik yazma işlemleri ve kilitler, POSIX (Linux sınamaları ve çekirdek araçları). Sahibi: D.
// open(O_EXCL) + write + fsync + close → rename (aynı klasör, atomik) → klasör fsync. Yedek (.bak) sert bağlantıyla
// (olmazsa kopyayla) kurulur. POSIX'te paylaşım kilidi yoktur; EBUSY / ETXTBSY geçici durum sayılır.
#include <fcntl.h>
#include <sys/file.h>
#include <sys/stat.h>
#include <unistd.h>

#include <cerrno>
#include <chrono>
#include <cstring>
#include <string>
#include <thread>

#include "platform/dosya_sistemi_atomik.h"

namespace op4 {
namespace {

std::string Neden(int e) {
    switch (e) {
        case ENOSPC: return "disk dolu";
        case EDQUOT: return "disk kotası doldu";
        case EACCES:
        case EPERM: return "erişim izni yok";
        case ENOENT: return "klasör bulunamadı";
        case EROFS: return "salt okunur dosya sistemi";
        case ENAMETOOLONG: return "yol çok uzun";
        default: return std::strerror(e);
    }
}

std::string Klasor(const std::string& yol) {
    const size_t i = yol.find_last_of('/');
    if (i == std::string::npos) return ".";
    return i == 0 ? "/" : yol.substr(0, i);
}

bool GeciciYaz(const std::string& gecici, std::string_view veri, std::string& hata) {
    mode_t kip = 0644;
    const int fd = ::open(gecici.c_str(), O_WRONLY | O_CREAT | O_EXCL | O_CLOEXEC, kip);
    if (fd < 0) {
        hata = "Geçici dosya oluşturulamadı (" + Neden(errno) + "): " + gecici;
        return false;
    }
    size_t yazilan = 0;
    while (yazilan < veri.size()) {
        const ssize_t n = ::write(fd, veri.data() + yazilan, veri.size() - yazilan);
        if (n < 0) {
            if (errno == EINTR) continue;
            hata = "Yazılamadı (" + Neden(errno) + "): " + gecici;
            ::close(fd);
            return false;
        }
        yazilan += static_cast<size_t>(n);
    }
    if (::fsync(fd) != 0) {
        hata = "Diske boşaltılamadı (" + Neden(errno) + "): " + gecici;
        ::close(fd);
        return false;
    }
    if (::close(fd) != 0) {
        hata = "Geçici dosya kapatılamadı (" + Neden(errno) + "): " + gecici;
        return false;
    }
    return true;
}

bool Kopyala(const std::string& kaynak, const std::string& hedef) {
    const int a = ::open(kaynak.c_str(), O_RDONLY | O_CLOEXEC);
    if (a < 0) return false;
    const int b = ::open(hedef.c_str(), O_WRONLY | O_CREAT | O_TRUNC | O_CLOEXEC, 0644);
    if (b < 0) {
        ::close(a);
        return false;
    }
    char tampon[1 << 15];
    bool tamam = true;
    for (;;) {
        const ssize_t n = ::read(a, tampon, sizeof(tampon));
        if (n == 0) break;
        if (n < 0) {
            if (errno == EINTR) continue;
            tamam = false;
            break;
        }
        if (::write(b, tampon, static_cast<size_t>(n)) != n) {
            tamam = false;
            break;
        }
    }
    tamam = ::fsync(b) == 0 && tamam;
    ::close(a);
    ::close(b);
    return tamam;
}

YerineKoymaSonucu YerineKoy(const std::string& gecici, const std::string& hedef, bool bak, std::string& hata) {
    struct stat st {};
    const bool var = ::stat(hedef.c_str(), &st) == 0;
    if (var) ::chmod(gecici.c_str(), st.st_mode & 07777);  // hedefin izinleri korunur
    if (bak && var) {
        const std::string b = hedef + ".bak";
        ::unlink(b.c_str());
        if (::link(hedef.c_str(), b.c_str()) != 0 && !Kopyala(hedef, b)) {
            hata = "Yedek (.bak) oluşturulamadı (" + Neden(errno) + "): " + b;
            return YerineKoymaSonucu::Hata;
        }
    }
    if (::rename(gecici.c_str(), hedef.c_str()) != 0) {
        const int e = errno;
        if (e == EBUSY || e == ETXTBSY) return YerineKoymaSonucu::PaylasimIhlali;
        hata = "Dosya yerine konamadı (" + Neden(e) + "): " + hedef + ".";
        return YerineKoymaSonucu::Hata;
    }
    const int d = ::open(Klasor(hedef).c_str(), O_RDONLY | O_DIRECTORY | O_CLOEXEC);
    if (d >= 0) {
        ::fsync(d);  // yeni dizin girdisi de diske yazılsın
        ::close(d);
    }
    return YerineKoymaSonucu::Tamam;
}

}  // namespace

const AtomikYazmaIslemleri& PlatformAtomikIslemleri() {
    static const AtomikYazmaIslemleri is{
        &GeciciYaz,
        &YerineKoy,
        [](int ms) { std::this_thread::sleep_for(std::chrono::milliseconds(ms)); },
        [](const std::string& yol) { ::unlink(yol.c_str()); },
    };
    return is;
}

uint32_t SurecNo() { return static_cast<uint32_t>(::getpid()); }

// ---- oturum kilidi (flock) -------------------------------------------------------------------------------------------
struct OturumKilidi::Ic {
    int fd = -1;
    std::string yol;
};

OturumKilidi::OturumKilidi() : ic_(std::make_unique<Ic>()) {}
OturumKilidi::~OturumKilidi() { Birak(); }

bool OturumKilidi::Al(const std::string& yol) {
    Birak();
    const int fd = ::open(yol.c_str(), O_RDWR | O_CREAT | O_CLOEXEC, 0600);
    if (fd < 0) return false;
    if (::flock(fd, LOCK_EX | LOCK_NB) != 0) {
        ::close(fd);
        return false;
    }
    ic_->fd = fd;
    ic_->yol = yol;
    return true;
}

void OturumKilidi::Birak() {
    if (ic_->fd < 0) return;
    ::unlink(ic_->yol.c_str());
    ::close(ic_->fd);  // kilit kapanışla düşer
    ic_->fd = -1;
    ic_->yol.clear();
}

bool OturumKilidi::Tutuluyor() const { return ic_->fd >= 0; }

bool KilitTutuluyorMu(const std::string& yol) {
    const int fd = ::open(yol.c_str(), O_RDONLY | O_CLOEXEC);
    if (fd < 0) return false;
    const bool tutuluyor = ::flock(fd, LOCK_EX | LOCK_NB) != 0 && errno == EWOULDBLOCK;
    ::close(fd);  // aldıysak kapanışla bırakılır
    return tutuluyor;
}

// ---- proje okuma kilidi (POSIX'te işlem yok) -------------------------------------------------------------------------
struct ProjeOkumaKilidi::Ic {};
ProjeOkumaKilidi::ProjeOkumaKilidi() : ic_(std::make_unique<Ic>()) {}
ProjeOkumaKilidi::~ProjeOkumaKilidi() = default;
bool ProjeOkumaKilidi::Ac(const std::string& yol) {
    yol_ = yol;
    return true;
}
void ProjeOkumaKilidi::Birak() { yol_.clear(); }

}  // namespace op4
