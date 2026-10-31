# op4 — JS kaynaklarının exe'ye gömülmesi (MIMARI §9.2 "Gömme"). Sahibi: B (model-cekirdegi).
#
# Yapılandırmada: op4_js_gom(<hedef> <çıktı.cpp> <kök> <göreli yol>...) derleme anında bir C++ kaynağı üretir ve hedefe
# ekler. Üretilen kaynak her dosyayı bayt dizisi olarak taşır (MSVC'nin 64 KB'lık dizgi sınırı yoktur) ve
# kaynak/cekirdek_js/js_gomulu.h'deki GomuluJsDosyalari()'yı tanımlar. Dosya adı (ör. "docs/model_ops.js") QuickJS'te
# kaynak adı olarak kullanılır: hata yığınlarında satır numarası kalır. JS dosyası değişince kaynak yeniden üretilir.
#
# Betik kipinde (cmake -P JsGom.cmake -DJSGOM_CIKTI=… -DJSGOM_KOK=… -DJSGOM_DOSYALAR=a|b|c) üretimi yapar.

if(CMAKE_SCRIPT_MODE_FILE AND DEFINED JSGOM_CIKTI)
  string(REPLACE "|" ";" _dosyalar "${JSGOM_DOSYALAR}")
  set(_govde "")
  set(_tablo "")
  set(_i 0)
  foreach(_d IN LISTS _dosyalar)
    file(READ "${JSGOM_KOK}/${_d}" _hex HEX)
    string(LENGTH "${_hex}" _n)
    math(EXPR _bayt "${_n} / 2")
    # 32 baytlık satırlar: önce satır sonları, sonra bayt ayırıcıları
    string(REGEX REPLACE "(................................................................)" "\\1\n" _hex "${_hex}")
    string(REGEX REPLACE "([0-9a-f][0-9a-f])" "0x\\1," _hex "${_hex}")
    string(APPEND _govde "alignas(8) const unsigned char kVeri${_i}[] = {\n${_hex}0x00};\n")
    string(APPEND _tablo "    {\"${_d}\", kVeri${_i}, ${_bayt}u},\n")
    math(EXPR _i "${_i} + 1")
  endforeach()
  set(_metin "// ÜRETİLDİ — elle değiştirmeyin (op4/cmake/JsGom.cmake). Gömülü JS kaynakları (MIMARI §9.2).
#include \"cekirdek_js/js_gomulu.h\"

namespace op4 {
namespace {
${_govde}
const GomuluJs kDosyalar[] = {
${_tablo}};
}  // namespace

const GomuluJs* GomuluJsDosyalari(size_t& sayi) {
    sayi = sizeof(kDosyalar) / sizeof(kDosyalar[0]);
    return kDosyalar;
}

}  // namespace op4
")
  file(WRITE "${JSGOM_CIKTI}.yeni" "${_metin}")
  file(COPY_FILE "${JSGOM_CIKTI}.yeni" "${JSGOM_CIKTI}" ONLY_IF_DIFFERENT)
  file(REMOVE "${JSGOM_CIKTI}.yeni")
  return()
endif()

set(_OP4_JSGOM_BETIK "${CMAKE_CURRENT_LIST_FILE}")

function(op4_js_gom hedef cikti kok)
  set(_bagimli)
  foreach(_d IN LISTS ARGN)
    if(NOT EXISTS "${kok}/${_d}")
      message(FATAL_ERROR "op4_js_gom: ${kok}/${_d} yok")
    endif()
    list(APPEND _bagimli "${kok}/${_d}")
  endforeach()
  string(REPLACE ";" "|" _liste "${ARGN}")
  add_custom_command(
    OUTPUT "${cikti}"
    COMMAND "${CMAKE_COMMAND}" "-DJSGOM_CIKTI=${cikti}" "-DJSGOM_KOK=${kok}" "-DJSGOM_DOSYALAR=${_liste}" -P "${_OP4_JSGOM_BETIK}"
    DEPENDS ${_bagimli} "${_OP4_JSGOM_BETIK}"
    COMMENT "op4: JS kaynakları gömülüyor (${cikti})"
    VERBATIM)
  target_sources(${hedef} PRIVATE "${cikti}")
endfunction()
