# op4 — gölgelendiriciler derlemede (MIMARI §6.1, D12; F1 iş 1.1, kabul A4). Sahibi: A.
#
# op4_golgelendiriciler(<hedef>) tek kaynak op4/golgelendiriciler/op4.hlsl'den iki şey üretir (<yapı>/uretilen/):
#   golgelendirici_kaynak.inc   HLSL metni, NUL ile biten bayt dizisi olarak (kaynak/golgelendirici.h, kGolgelendirici:
#                               gömülü bayt kodu yoksa grafik.cpp'nin çalışma anı D3DCompile yedeği)
#   golgelendirici_gomulu.cpp   Windows SDK fxc.exe ile her giriş noktasının SM 5.1 bayt kodu (vs_* → vs_5_1, ps_* →
#                               ps_5_1; giriş noktaları HLSL'den kendiliğinden bulunur) ve ad → bayt tablosu
#                               (kaynak/grafik/golgelendirici_bayt.cpp, GomuluGolgelendirici — sözleşme S25)
# fxc bulunamazsa (MinGW sözdizimi denetimi) tablo boş üretilir ve program çalışma anında derler (uyarı verilir).
# OP4_FXC ile fxc.exe yolu elle verilebilir. FXC hataları derlemeyi durdurur (hatalar derlemede yakalanır).

function(_op4_fxc_bul)
  if(OP4_FXC)
    return()
  endif()
  set(_ipuclari)
  set(_pf86 "ProgramFiles(x86)")
  foreach(_kok IN ITEMS "$ENV{${_pf86}}/Windows Kits/10/bin" "$ENV{ProgramFiles}/Windows Kits/10/bin")
    if(CMAKE_VS_WINDOWS_TARGET_PLATFORM_VERSION)
      list(APPEND _ipuclari "${_kok}/${CMAKE_VS_WINDOWS_TARGET_PLATFORM_VERSION}/x64")
    endif()
    file(GLOB _surumler LIST_DIRECTORIES true "${_kok}/10.*")
    list(SORT _surumler COMPARE NATURAL ORDER DESCENDING)
    foreach(_s IN LISTS _surumler)
      list(APPEND _ipuclari "${_s}/x64")
    endforeach()
    list(APPEND _ipuclari "${_kok}/x64")
  endforeach()
  if(DEFINED ENV{WindowsSdkVerBinPath})
    list(PREPEND _ipuclari "$ENV{WindowsSdkVerBinPath}/x64")
  endif()
  find_program(OP4_FXC NAMES fxc fxc.exe HINTS ${_ipuclari} NO_DEFAULT_PATH)
  if(NOT OP4_FXC)
    find_program(OP4_FXC NAMES fxc fxc.exe)
  endif()
endfunction()

function(op4_golgelendiriciler hedef)
  set(_hlsl "${CMAKE_CURRENT_SOURCE_DIR}/golgelendiriciler/op4.hlsl")
  set(_cikti "${CMAKE_CURRENT_BINARY_DIR}/uretilen")
  file(MAKE_DIRECTORY "${_cikti}/golgelendirici")
  set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${_hlsl}")

  # (1) HLSL metni → bayt dizisi (MSVC'nin 16 KB dize sabiti sınırı yok).
  file(READ "${_hlsl}" _hex HEX)
  # Karakter sabitleri ('\xNN'): char işaretli olsa da daraltma (narrowing) hatası vermez. 16 bayt / satır.
  string(REGEX REPLACE "([0-9a-f][0-9a-f])" "'\\\\x\\1'," _bayt "${_hex}")
  set(_bayt16 "('\\\\x[0-9a-f][0-9a-f]',)")
  string(REPEAT "${_bayt16}" 16 _desen)
  string(REGEX REPLACE "(${_desen})" "\\1\n" _bayt "${_bayt}")
  file(WRITE "${_cikti}/golgelendirici_kaynak.inc.yeni"
       "// Üretilen dosya (cmake/Golgelendiriciler.cmake): op4/golgelendiriciler/op4.hlsl, NUL ile biten bayt dizisi.\n${_bayt}'\\0'\n")
  file(COPY_FILE "${_cikti}/golgelendirici_kaynak.inc.yeni" "${_cikti}/golgelendirici_kaynak.inc" ONLY_IF_DIFFERENT)

  # (2) Giriş noktaları: "<tür> vs_ad(" / "<tür> ps_ad(".
  file(READ "${_hlsl}" _metin)
  string(REGEX MATCHALL "[ \t\r\n](vs|ps)_[A-Za-z0-9_]+[ \t]*\\(" _eslesmeler "${_metin}")
  set(_girisler)
  foreach(_e IN LISTS _eslesmeler)
    string(REGEX REPLACE "^[ \t\r\n]+" "" _e "${_e}")
    string(REGEX REPLACE "[ \t]*\\($" "" _e "${_e}")
    list(APPEND _girisler "${_e}")
  endforeach()
  list(REMOVE_DUPLICATES _girisler)
  list(LENGTH _girisler _n)

  set(_basliklar)
  set(_icerme "")
  set(_tablo "")
  set(_derlenen 0)
  if(WIN32)
    _op4_fxc_bul()
  endif()
  if(WIN32 AND OP4_FXC)
    foreach(_g IN LISTS _girisler)
      string(SUBSTRING "${_g}" 0 2 _tur)
      set(_h "${_cikti}/golgelendirici/${_g}.h")
      add_custom_command(
        OUTPUT "${_h}"
        COMMAND "${OP4_FXC}" /nologo /T ${_tur}_5_1 /E ${_g} /O3 /Qstrip_debug /Qstrip_priv /Qstrip_reflect
                /Vn op4_bayt_${_g} /Fh "${_h}" "${_hlsl}"
        DEPENDS "${_hlsl}"
        COMMENT "FXC ${_tur}_5_1 ${_g} (op4.hlsl)"
        VERBATIM)
      list(APPEND _basliklar "${_h}")
      string(APPEND _icerme "#include \"golgelendirici/${_g}.h\"\n")
      string(APPEND _tablo "    {\"${_g}\", op4_bayt_${_g}, sizeof(op4_bayt_${_g})},\n")
      math(EXPR _derlenen "${_derlenen} + 1")
    endforeach()
    message(STATUS "op4 gölgelendiricileri: ${_n} giriş noktası FXC ile SM 5.1'e derlenecek (${OP4_FXC})")
  else()
    string(APPEND _tablo "    {nullptr, nullptr, 0},\n")
    if(WIN32)
      message(WARNING "op4: fxc.exe (Windows SDK) bulunamadı; gölgelendiriciler çalışma anında derlenecek (OP4_FXC ile yol verin)")
    endif()
  endif()
  file(WRITE "${_cikti}/golgelendirici_gomulu.cpp.yeni"
"// Üretilen dosya (cmake/Golgelendiriciler.cmake): op4/golgelendiriciler/op4.hlsl → FXC SM 5.1 bayt kodu (sözleşme S25).
#include <cstddef>
#include <cstdint>
using BYTE = unsigned char;  // fxc /Fh çıktısı \"const BYTE ad[]\" yazar
${_icerme}
namespace op4::golgelendirici_gomulu {
struct Girdi {
    const char* ad;
    const void* veri;
    size_t boyut;
};
extern const Girdi kGirdiler[];
extern const size_t kGirdiSayisi;
const Girdi kGirdiler[] = {
${_tablo}};
const size_t kGirdiSayisi = ${_derlenen};
}  // namespace op4::golgelendirici_gomulu
")
  file(COPY_FILE "${_cikti}/golgelendirici_gomulu.cpp.yeni" "${_cikti}/golgelendirici_gomulu.cpp" ONLY_IF_DIFFERENT)
  target_sources(${hedef} PRIVATE ${_basliklar} "${_cikti}/golgelendirici_gomulu.cpp")
  target_include_directories(${hedef} PRIVATE "${_cikti}")
endfunction()
