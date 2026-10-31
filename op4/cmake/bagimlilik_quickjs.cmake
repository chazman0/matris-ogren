# quickjs-ng v0.17.0 (MIT; 2026-09-18) — model çekirdeğinin JavaScript motoru (MIMARI §9.1). Hedef: op4::quickjs.
# Sahibi: B (model-cekirdegi). Yalnız dil motoru derlenir (quickjs-libc / std / os modülleri yok: çekirdek dosya, ağ ve
# süreç erişimi olmadan çalışır). Üçüncü taraf kaynağıdır: uyarı düzeyi kapalıdır (MSVC /W0, GCC/Clang -w), op4 hedeflerinin
# -Werror / /WX kuralı ona uygulanmaz. Bayraklar quickjs-ng'nin kendi CMakeLists.txt'iyle aynıdır (C11 + GNU uzantıları,
# MSVC'de /experimental:c11atomics, GCC/Clang'da -funsigned-char).
#
# Bu dosya ayrıca JsGom.cmake'i içerir ve CMakeLists.txt'in sonunda (cmake_language DEFER) op4_cekirdek_js hedefine
# QuickJS'i ve gömülü JS kaynaklarını bağlar; böylece B, A'nın CMakeLists.txt'ine dokunmadan kendi hedefini tamamlar.
# Çevrim dışı / yerel kopya: -DOP4_QUICKJS_DIZINI=<klasör>.
op4_bagimlilik_git(quickjs
  REPO https://github.com/quickjs-ng/quickjs.git
  ETIKET v0.17.0
  ISLEME 6d46d07d04041b40f4f49eaa7fdebe44c314c699)

add_library(op4_quickjs STATIC
  ${quickjs_SOURCE_DIR}/dtoa.c
  ${quickjs_SOURCE_DIR}/libregexp.c
  ${quickjs_SOURCE_DIR}/libunicode.c
  ${quickjs_SOURCE_DIR}/quickjs.c)
add_library(op4::quickjs ALIAS op4_quickjs)
target_include_directories(op4_quickjs SYSTEM PUBLIC "${quickjs_SOURCE_DIR}")
set_target_properties(op4_quickjs PROPERTIES C_STANDARD 11 C_STANDARD_REQUIRED ON C_EXTENSIONS ON
                                             C_VISIBILITY_PRESET hidden POSITION_INDEPENDENT_CODE ON)
target_compile_definitions(op4_quickjs PRIVATE QUICKJS_NG_BUILD _GNU_SOURCE)
if(WIN32)
  target_compile_definitions(op4_quickjs PRIVATE WIN32_LEAN_AND_MEAN _WIN32_WINNT=0x0601)
endif()
if(MSVC)
  target_compile_options(op4_quickjs PRIVATE /W0 /utf-8 /experimental:c11atomics /bigobj)
else()
  # Hata ayıklama derlemesinde de iyileştirilmiş: yorumlayıcı -O0'da 3–5 kat yavaştır (B7 bütçeleri; op4 kodu etkilenmez).
  target_compile_options(op4_quickjs PRIVATE -w -funsigned-char -O2)
endif()
# UBSan (linux-cekirdek-asan: -fsanitize=undefined -fno-sanitize-recover): Clang 17+ C'de -fsanitize=function'ı da açar ve
# QuickJS'in bilinçli işlev işaretçisi dönüşümlerini (js_realloc_rt → void *(*)(void *, …), cutils.h dbuf_claim) sınamayı
# düşüren hata sayar. Yalnız bu denetim, yalnız QuickJS'te kapatılır; ASan ve UBSan'ın geri kalanı açık kalır. GCC bu denetimi
# tanımaz (bayrak sınanır).
include(CheckCCompilerFlag)
check_c_compiler_flag(-fno-sanitize=function OP4_QUICKJS_FNO_SANITIZE_FUNCTION)
if(OP4_QUICKJS_FNO_SANITIZE_FUNCTION)
  target_compile_options(op4_quickjs PRIVATE -fno-sanitize=function)
endif()
if(NOT WIN32)
  target_link_libraries(op4_quickjs PUBLIC m)
endif()
find_package(Threads QUIET)
if(Threads_FOUND)
  target_link_libraries(op4_quickjs PUBLIC Threads::Threads)
endif()
target_link_libraries(op4_quickjs PUBLIC ${CMAKE_DL_LIBS})

include(JsGom)

# op4_cekirdek_js (CMakeLists.txt, A) bu dosyadan sonra tanımlanır: bağlama dizin sonunda yapılır.
function(_op4_cekirdek_js_bagla)
  if(NOT TARGET op4_cekirdek_js)
    message(FATAL_ERROR "bagimlilik_quickjs.cmake: op4_cekirdek_js hedefi yok (CMakeLists.txt yapısı değişti mi?)")
  endif()
  get_filename_component(_op4_depo "${CMAKE_SOURCE_DIR}/.." ABSOLUTE)
  # Yükleme sırası bağlayıcıdır (MIMARI §9.2): önce ön yükleme, sonra docs/ modülleri, en son op4 cephesi ve köprü.
  op4_js_gom(op4_cekirdek_js "${CMAKE_BINARY_DIR}/op4_js_gomulu.cpp" "${_op4_depo}"
    op4/js/op4_onyukleme.js
    docs/aks_sistemi.js
    docs/model_ops.js
    docs/bina_cizim.js
    docs/ifc_disari.js
    docs/tablo_editoru.js
    op4/js/op4_ops.js
    op4/js/op4_cekirdek.js
    op4/js/op4_kopru.js)
  target_link_libraries(op4_cekirdek_js PUBLIC op4::quickjs)
  target_compile_definitions(op4_cekirdek_js PRIVATE OP4_QUICKJS_SURUM="0.17.0")
endfunction()
cmake_language(DEFER CALL _op4_cekirdek_js_bagla)
