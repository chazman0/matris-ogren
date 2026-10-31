# FreeType 2.13.3 (FTL; 2024-08-12) — yalnız Windows: Dear ImGui yazı atlasının glif işleyicisi (imgui_freetype; hafif
# oto-ipucu, MIMARI §25.1). Hedef: op4::freetype (statik C kitaplığı). Sahibi: A (sürüm), C (kullanım: arayuz/yazi.cpp).
# Linux çekirdek derlemesi FreeType'a gerek duymaz.
#
# Kaynak ağacı add_subdirectory ile eklenmez (Bagimliliklar.cmake kuralı): FreeType'ın belgelediği el ile derleme
# (docs/INSTALL.ANY) burada yapılır. Yalnız op4'ün kullandığı yazı tipi biçimleri derlenir: TrueType ve OpenType/CFF
# sürücüleri, sfnt (+ WOFF için gömülü zlib), PostScript yardımcıları, oto-ipucu, gri ve tek renk işleyiciler. Modül
# listesi FreeType'ın varsayılan freetype/config/ftmodule.h'ının yerine yapı klasörüne yazılır ve include yolunda önce
# gelir (docs/CUSTOMIZE). Üçüncü taraf kaynağıdır: uyarı düzeyi kapalıdır (MSVC /W0, GCC/Clang -w), op4 hedeflerinin
# /WX / -Werror kuralı ona uygulanmaz.
#
# Lisans: FTL (FreeType Project License; GPLv2 ile çift lisanslıdır, op4 FTL'yi seçer). Metin kurulu programda
# lisanslar\FreeType-FTL.txt; atıf satırı kurulum/lisanslar/UCUNCU_TARAF.txt'tedir. Çevrim dışı: -DOP4_FREETYPE_DIZINI.
if(WIN32)
  op4_bagimlilik_git(freetype
    REPO https://github.com/freetype/freetype.git
    ETIKET VER-2-13-3
    ISLEME 42608f77f20749dd6ddc9e0536788eaad70ea4b5)

  set(_op4_ft_uretilen "${CMAKE_CURRENT_BINARY_DIR}/op4_freetype")
  file(WRITE "${_op4_ft_uretilen}/freetype/config/ftmodule.h.yeni"
    "/* op4: derlenen FreeType modülleri (cmake/bagimlilik_freetype.cmake). */\n"
    "FT_USE_MODULE( FT_Module_Class, autofit_module_class )\n"
    "FT_USE_MODULE( FT_Driver_ClassRec, tt_driver_class )\n"
    "FT_USE_MODULE( FT_Driver_ClassRec, cff_driver_class )\n"
    "FT_USE_MODULE( FT_Module_Class, psaux_module_class )\n"
    "FT_USE_MODULE( FT_Module_Class, psnames_module_class )\n"
    "FT_USE_MODULE( FT_Module_Class, pshinter_module_class )\n"
    "FT_USE_MODULE( FT_Module_Class, sfnt_module_class )\n"
    "FT_USE_MODULE( FT_Renderer_Class, ft_smooth_renderer_class )\n"
    "FT_USE_MODULE( FT_Renderer_Class, ft_raster1_renderer_class )\n")
  configure_file("${_op4_ft_uretilen}/freetype/config/ftmodule.h.yeni"
                 "${_op4_ft_uretilen}/freetype/config/ftmodule.h" COPYONLY)

  add_library(op4_freetype STATIC
    ${freetype_SOURCE_DIR}/builds/windows/ftsystem.c
    ${freetype_SOURCE_DIR}/builds/windows/ftdebug.c
    ${freetype_SOURCE_DIR}/src/base/ftinit.c
    ${freetype_SOURCE_DIR}/src/base/ftbase.c
    ${freetype_SOURCE_DIR}/src/base/ftbbox.c
    ${freetype_SOURCE_DIR}/src/base/ftbitmap.c
    ${freetype_SOURCE_DIR}/src/base/ftglyph.c
    ${freetype_SOURCE_DIR}/src/base/ftmm.c
    ${freetype_SOURCE_DIR}/src/base/ftsynth.c
    ${freetype_SOURCE_DIR}/src/autofit/autofit.c
    ${freetype_SOURCE_DIR}/src/truetype/truetype.c
    ${freetype_SOURCE_DIR}/src/cff/cff.c
    ${freetype_SOURCE_DIR}/src/sfnt/sfnt.c
    ${freetype_SOURCE_DIR}/src/psaux/psaux.c
    ${freetype_SOURCE_DIR}/src/pshinter/pshinter.c
    ${freetype_SOURCE_DIR}/src/psnames/psnames.c
    ${freetype_SOURCE_DIR}/src/smooth/smooth.c
    ${freetype_SOURCE_DIR}/src/raster/raster.c
    ${freetype_SOURCE_DIR}/src/gzip/ftgzip.c)
  add_library(op4::freetype ALIAS op4_freetype)
  set_target_properties(op4_freetype PROPERTIES LINKER_LANGUAGE C)
  target_include_directories(op4_freetype BEFORE PRIVATE "${_op4_ft_uretilen}")  # op4 modül listesi önce
  target_include_directories(op4_freetype SYSTEM PUBLIC "${freetype_SOURCE_DIR}/include")
  target_compile_definitions(op4_freetype PRIVATE FT2_BUILD_LIBRARY)
  if(MSVC)
    target_compile_definitions(op4_freetype PRIVATE _CRT_SECURE_NO_WARNINGS _CRT_NONSTDC_NO_WARNINGS)
    target_compile_options(op4_freetype PRIVATE /W0 /utf-8)
  else()
    target_compile_options(op4_freetype PRIVATE -w)
  endif()

  install(FILES "${freetype_SOURCE_DIR}/docs/FTL.TXT" DESTINATION lisanslar RENAME FreeType-FTL.txt)
endif()
