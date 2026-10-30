// op4 platform — alt süreç + iki anonim boru, POSIX (sözleşme S14; F1 iş 1.2). Uygulayan: A (derleme-motor).
//
// pipe2(O_CLOEXEC) + posix_spawn. Çocuğun boru uçları fd 3 (istek, okur) ve 4 (yanıt, yazar) olarak verilir; "{istek}" /
// "{yanit}" yer tutucuları "3" / "4" olur. Diğer bütün tanımlayıcılar O_CLOEXEC ile kapanır. stdout + stderr ciktiDosyasi'na
// eklenir (yoksa /dev/null), stdin /dev/null'dur. Bellek sınırı POSIX'te yok sayılır (op4.exe yalnız Windows'tadır; bu
// uygulama Linux sınamaları — `python3 -m op4_sunucu` — içindir).
//
// İş parçacığı kuralı: Oku ayrı bir okuyucu iş parçacığından, Yaz ve YazmayiKapat tek bir yazıcı iş parçacığından
// çağrılabilir; Calisiyor / Bekle / Sonlandir her iş parçacığından güvenlidir. Yıkıcıdan önce okuyucu bitmiş olmalıdır.
#include <fcntl.h>
#include <signal.h>
#include <spawn.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <unistd.h>

#include <cerrno>
#include <chrono>
#include <cstring>
#include <mutex>
#include <string_view>
#include <thread>

#include "platform/surec.h"

extern char** environ;

namespace op4 {
namespace {

constexpr int kCocukIstekFd = 3;
constexpr int kCocukYanitFd = 4;

std::string HataMetni(const char* ne, int e) { return std::string(ne) + ": " + std::strerror(e); }

void Kapat(int& fd) {
    if (fd >= 0) ::close(fd);
    fd = -1;
}

std::string YerTut(std::string s) {
    for (const auto& [ad, deger] : {std::pair<const char*, const char*>{"{istek}", "3"}, {"{yanit}", "4"}}) {
        for (size_t i = s.find(ad); i != std::string::npos; i = s.find(ad, i + std::strlen(deger))) s.replace(i, std::strlen(ad), deger);
    }
    return s;
}

class PosixSurec final : public Surec {
public:
    PosixSurec() {
        // Kapanmış boruya yazmak süreci SIGPIPE ile öldürmesin (Yaz false döner).
        static std::once_flag bir;
        std::call_once(bir, [] { ::signal(SIGPIPE, SIG_IGN); });
    }
    ~PosixSurec() override {
        if (pid_ > 0) {
            Sonlandir();
            int kod = 0;
            Bekle(5000, kod);
        }
        Kapat(yaz_);
        Kapat(oku_);
    }

    bool Baslat(const SurecAyari& a, std::string& hata) override {
        if (pid_ > 0) {
            hata = "süreç zaten başlatıldı";
            return false;
        }
        if (a.program.empty()) {
            hata = "program yolu boş";
            return false;
        }
        if (a.program.find('/') != std::string::npos && ::access(a.program.c_str(), X_OK) != 0) {
            hata = "program bulunamadı ya da çalıştırılamıyor: " + a.program + " (" + std::strerror(errno) + ")";
            return false;
        }
        int istek[2] = {-1, -1}, yanit[2] = {-1, -1};
        if (::pipe2(istek, O_CLOEXEC) != 0) {
            hata = HataMetni("pipe2 (istek)", errno);
            return false;
        }
        if (::pipe2(yanit, O_CLOEXEC) != 0) {
            hata = HataMetni("pipe2 (yanıt)", errno);
            ::close(istek[0]);
            ::close(istek[1]);
            return false;
        }
        // Çocuk uçlarını 3/4'e dup2 edebilmek için önce yüksek numaralara taşı (aynı numaraya dup2 CLOEXEC'i silmez).
        int cocukIstek = ::fcntl(istek[0], F_DUPFD_CLOEXEC, 10);
        int cocukYanit = ::fcntl(yanit[1], F_DUPFD_CLOEXEC, 10);
        ::close(istek[0]);
        ::close(yanit[1]);
        yaz_ = istek[1];
        oku_ = yanit[0];

        posix_spawn_file_actions_t fa;
        posix_spawn_file_actions_init(&fa);
        posix_spawn_file_actions_addopen(&fa, 0, "/dev/null", O_RDONLY, 0);
        if (a.ciktiDosyasi.empty())
            posix_spawn_file_actions_addopen(&fa, 1, "/dev/null", O_WRONLY, 0);
        else
            posix_spawn_file_actions_addopen(&fa, 1, a.ciktiDosyasi.c_str(), O_WRONLY | O_CREAT | O_APPEND, 0644);
        posix_spawn_file_actions_adddup2(&fa, 1, 2);
        posix_spawn_file_actions_adddup2(&fa, cocukIstek, kCocukIstekFd);
        posix_spawn_file_actions_adddup2(&fa, cocukYanit, kCocukYanitFd);
#if defined(__GLIBC__) || defined(__APPLE__)
        if (!a.calismaDizini.empty()) posix_spawn_file_actions_addchdir_np(&fa, a.calismaDizini.c_str());
#endif
        // argv
        std::vector<std::string> args;
        args.push_back(a.program);
        for (const std::string& s : a.argumanlar) args.push_back(YerTut(s));
        std::vector<char*> argv;
        for (std::string& s : args) argv.push_back(s.data());
        argv.push_back(nullptr);
        // ortam: üst süreçten + değişiklikler
        std::vector<std::string> ortam;
        for (char** e = environ; e && *e; ++e) {
            const std::string_view s(*e);
            const std::string_view ad = s.substr(0, s.find('='));
            bool degisti = false;
            for (const auto& [k, v] : a.ortam) degisti = degisti || k == ad;
            if (!degisti) ortam.emplace_back(s);
        }
        for (const auto& [k, v] : a.ortam) ortam.push_back(k + "=" + v);
        std::vector<char*> envp;
        for (std::string& s : ortam) envp.push_back(s.data());
        envp.push_back(nullptr);

        pid_t pid = -1;
        const bool yolVar = a.program.find('/') != std::string::npos;
        const int r = yolVar ? ::posix_spawn(&pid, a.program.c_str(), &fa, nullptr, argv.data(), envp.data())
                             : ::posix_spawnp(&pid, a.program.c_str(), &fa, nullptr, argv.data(), envp.data());
        posix_spawn_file_actions_destroy(&fa);
        ::close(cocukIstek);
        ::close(cocukYanit);
        if (r != 0) {
            hata = HataMetni(("süreç başlatılamadı (" + a.program + ")").c_str(), r);
            Kapat(yaz_);
            Kapat(oku_);
            return false;
        }
        std::lock_guard<std::mutex> k(kilit_);
        pid_ = pid;
        bitti_ = false;
        return true;
    }

    bool Yaz(const void* veri, size_t boyut) override {
        const char* p = static_cast<const char*>(veri);
        while (boyut > 0) {
            if (yaz_ < 0) return false;
            const ssize_t n = ::write(yaz_, p, boyut);
            if (n < 0) {
                if (errno == EINTR) continue;
                return false;
            }
            p += n;
            boyut -= static_cast<size_t>(n);
        }
        return true;
    }

    long long Oku(void* tampon, size_t boyut) override {
        for (;;) {
            if (oku_ < 0) return -1;
            const ssize_t n = ::read(oku_, tampon, boyut);
            if (n < 0 && errno == EINTR) continue;
            return n;
        }
    }

    void YazmayiKapat() override { Kapat(yaz_); }

    bool Calisiyor() const override {
        std::lock_guard<std::mutex> k(kilit_);
        return Yokla();
    }

    bool Bekle(uint32_t ms, int& cikisKodu) override {
        const auto bitis = std::chrono::steady_clock::now() + std::chrono::milliseconds(ms);
        for (;;) {
            {
                std::lock_guard<std::mutex> k(kilit_);
                if (pid_ <= 0) {
                    cikisKodu = -1;
                    return true;
                }
                if (!Yokla()) {
                    cikisKodu = kod_;
                    return true;
                }
            }
            if (std::chrono::steady_clock::now() >= bitis) return false;
            std::this_thread::sleep_for(std::chrono::milliseconds(2));
        }
    }

    void Sonlandir() override {
        std::lock_guard<std::mutex> k(kilit_);
        if (pid_ > 0 && Yokla()) ::kill(pid_, SIGKILL);
    }

    long long Kimlik() const override { return pid_; }

private:
    // kilit_ tutulurken: süreç hâlâ çalışıyor mu (bittiyse çıkış kodunu bir kez toplar).
    bool Yokla() const {
        if (pid_ <= 0 || bitti_) return false;
        int st = 0;
        const pid_t r = ::waitpid(pid_, &st, WNOHANG);
        if (r == 0) return true;
        bitti_ = true;
        if (r == pid_) kod_ = WIFEXITED(st) ? WEXITSTATUS(st) : (WIFSIGNALED(st) ? 128 + WTERMSIG(st) : -1);
        else kod_ = -1;
        return false;
    }

    mutable std::mutex kilit_;
    pid_t pid_ = -1;
    mutable bool bitti_ = false;
    mutable int kod_ = 0;
    int yaz_ = -1;
    int oku_ = -1;
};

}  // namespace

std::unique_ptr<Surec> SurecOlustur() { return std::make_unique<PosixSurec>(); }

}  // namespace op4
