# miniz 3.0.2 (MIT; 2023-01-15) — .op4 proje dosyası ZIP okuma / yazma ve onizleme.png PNG kodlayıcısı (MIMARI §13.1,
# §19). Hedef: op4::miniz (statik C kitaplığı). Sahibi: D (dosya-cozum).
#
# Kaynak ağacı add_subdirectory ile eklenmez (Bagimliliklar.cmake kuralı): dört .c dosyası burada derlenir; miniz'in kendi
# CMake'inin ürettiği miniz_export.h (GenerateExportHeader) yapı klasörüne yazılır (statik kitaplıkta dışa aktarım işareti
# boştur). Yalnız bellek içi işlemler kullanılır: MINIZ_NO_STDIO (dosya G/Ç'si platform/dosya_sistemi.h'tedir; Türkçe
# karakterli yollar orada çözülür) ve MINIZ_NO_ZLIB_COMPATIBLE_NAMES (zlib adlarıyla çakışma olmasın).
#
# op4_cekirdek'e bağlantı: kaynak/cekirdek/proje_*.cpp miniz kullanır. Hedef bu dosya içerildiğinde henüz tanımlı
# olmadığından bağlantı, op4/ klasörünün işlenmesi bitince ertelenmiş çağrıyla kurulur (CMakeLists.txt'ye dokunmadan;
# MIMARI §24.3 "yeni bağımlılık kendi dosyasında").
op4_bagimlilik_git(miniz
  REPO https://github.com/richgel999/miniz.git
  ETIKET 3.0.2
  ISLEME 293d4db1b7d0ffee9756d035b9ac6f7431ef8492)

set(_op4_miniz_uretilen "${CMAKE_CURRENT_BINARY_DIR}/op4_miniz")
file(WRITE "${_op4_miniz_uretilen}/miniz_export.h.yeni"
  "/* op4: miniz statik kitaplık olarak derlenir (cmake/bagimlilik_miniz.cmake). */\n"
  "#ifndef MINIZ_EXPORT\n#define MINIZ_EXPORT\n#endif\n")
configure_file("${_op4_miniz_uretilen}/miniz_export.h.yeni" "${_op4_miniz_uretilen}/miniz_export.h" COPYONLY)

add_library(op4_miniz STATIC
  ${miniz_SOURCE_DIR}/miniz.c
  ${miniz_SOURCE_DIR}/miniz_tdef.c
  ${miniz_SOURCE_DIR}/miniz_tinfl.c
  ${miniz_SOURCE_DIR}/miniz_zip.c)
add_library(op4::miniz ALIAS op4_miniz)
set_target_properties(op4_miniz PROPERTIES LINKER_LANGUAGE C POSITION_INDEPENDENT_CODE ON)
target_include_directories(op4_miniz SYSTEM PUBLIC "${miniz_SOURCE_DIR}" "${_op4_miniz_uretilen}")
target_compile_definitions(op4_miniz PUBLIC MINIZ_NO_STDIO MINIZ_NO_ZLIB_COMPATIBLE_NAMES)
if(MSVC)
  target_compile_options(op4_miniz PRIVATE /W0 /utf-8)
else()
  target_compile_options(op4_miniz PRIVATE -w)
endif()

# Ertelenmiş bağlantı: op4/CMakeLists.txt sonunda (Windows dışı derlemede erken return() sonrasında da) çalışır.
function(_op4_miniz_bagla)
  if(TARGET op4_cekirdek)
    target_link_libraries(op4_cekirdek PUBLIC op4::miniz)
  else()
    message(WARNING "op4_cekirdek hedefi yok: miniz bağlanamadı (cmake/bagimlilik_miniz.cmake)")
  endif()
endfunction()
cmake_language(DEFER DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}" CALL _op4_miniz_bagla)
