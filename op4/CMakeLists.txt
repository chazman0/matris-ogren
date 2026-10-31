# op4 — Opus Fortis yapısal modelleme / analiz programı (Windows, yerel C++20 + DirectX 12 + Dear ImGui + CPython motoru).
#
# Hedefler (MIMARI §19, "F1 paket sözleşmeleri"):
#   op4_cekirdek           platformdan bağımsız çekirdek (kaynak/cekirdek, kaynak/platform) — Windows VE Linux
#   op4_cekirdek_js        model çekirdeği (kaynak/cekirdek_js; QuickJS-ng, F1 iş 1.3) — Windows VE Linux
#   op4_cekirdek_testleri  doctest birim sınamaları (testler/cekirdek/*.cpp) — ctest
#   op4.exe                Windows uygulaması (kaynak/*.cpp, kaynak/arayuz, kaynak/grafik, kaynak/dosya, kaynak/cozum);
#                          gölgelendiriciler derlemede FXC SM 5.1 ile gömülür (cmake/Golgelendiriciler.cmake)
#   op4motor.exe           hesap motoru süreç barındırıcısı (kaynak/motor_barindirici; Py_Main → op4_sunucu) — Windows
# Ön ayarlar (CMakePresets.json): win-surum, win-hata, linux-cekirdek, linux-cekirdek-asan.
# Kaynak listeleri KLASÖR DESENİYLE toplanır (CONFIGURE_DEPENDS): paketler yeni dosya eklemek için bu dosyaya dokunmaz.
# Dosya adı kuralı: *_win.cpp yalnız Windows'ta, *_posix.cpp yalnız Windows dışında derlenir.
#
# Derleme (Windows, Visual Studio 2022+ / MSVC x64):
#   cmake -S op4 -B op4-yapi -A x64                 (ya da: cmake --preset win-surum && cmake --build --preset win-surum)
#   cmake --build op4-yapi --config Release --parallel
#   ctest --test-dir op4-yapi -C Release --output-on-failure
#   cmake --install op4-yapi --config Release --prefix paket        # op4.exe + op4motor.exe + kimlik/ + veri/
#   python op4/araclar/python_hazirla.py --paket paket                # gömülü Python + numpy/sympy + motor/*.py
# Linux (yalnız çekirdek): cmake --preset linux-cekirdek-asan && cmake --build --preset linux-cekirdek-asan
#                          && ctest --preset linux-cekirdek-asan          (ön ayarsız: cmake -S op4 -B /tmp/op4-linux -G Ninja)
# Yerel sözdizimi denetimi (Linux, MinGW-w64): op4/araclar/mingw.cmake araç zinciri dosyasıyla.
cmake_minimum_required(VERSION 3.24)

# Sürüm X.Y.Z. Etiketsiz derlemede taban sürüm; CI'da "op4-vX.Y.Z" etiketinden -DOP4_SURUM=X.Y.Z ile verilir
# (op4.exe sürüm bilgisi, açılış ekranı ve op4-setup-<sürüm>.exe aynı değeri taşır). CI taban sürümü bu satırdan okur.
set(OP4_TABAN_SURUM "0.0.1")
set(OP4_SURUM "" CACHE STRING "op4 sürümü (X.Y.Z); boşsa taban sürüm")
if(OP4_SURUM STREQUAL "")
  set(_op4_surum "${OP4_TABAN_SURUM}")
else()
  set(_op4_surum "${OP4_SURUM}")
endif()
if(NOT _op4_surum MATCHES "^[0-9]+\\.[0-9]+\\.[0-9]+$")
  message(FATAL_ERROR "OP4_SURUM X.Y.Z biçiminde olmalı (ör. 0.1.0): '${_op4_surum}'")
endif()
project(op4 VERSION ${_op4_surum} LANGUAGES C CXX)
message(STATUS "op4 sürümü: ${PROJECT_VERSION}")

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
if(MSVC)
  # Statik C/C++ çalışma zamanı: op4.exe, Visual C++ yeniden dağıtılabilir paketi gerektirmez.
  set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")
endif()

option(OP4_TESTLER "C++ birim sınamaları (doctest, ctest)" ON)
option(OP4_HATA_AYIKLAMA "op4.exe: D3D12 hata ayıklama katmanı her zaman açık (win-hata ön ayarı)" OFF)
if(OP4_TESTLER)
  enable_testing()
endif()

list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")
include(Derleyici)
include(Bagimliliklar)
include(Golgelendiriciler)

# Platforma göre süzülmüş kaynak deseni: op4_kaynaklar(<değişken> <klasör>...)
function(op4_kaynaklar cikti)
  set(_liste)
  foreach(_k IN LISTS ARGN)
    file(GLOB _d CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/${_k}/*.cpp")
    list(APPEND _liste ${_d})
  endforeach()
  if(WIN32)
    list(FILTER _liste EXCLUDE REGEX "_posix\\.cpp$")
  else()
    list(FILTER _liste EXCLUDE REGEX "_win\\.cpp$")
  endif()
  list(SORT _liste)
  set(${cikti} ${_liste} PARENT_SCOPE)
endfunction()

# ---------------------------------------------------------------------------------------------- op4_cekirdek
op4_kaynaklar(OP4_CEKIRDEK_KAYNAKLARI kaynak/cekirdek kaynak/platform)
add_library(op4_cekirdek STATIC ${OP4_CEKIRDEK_KAYNAKLARI})
target_include_directories(op4_cekirdek PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}/kaynak")
target_link_libraries(op4_cekirdek PUBLIC op4::json)
target_compile_definitions(op4_cekirdek PUBLIC OP4_SURUM="${PROJECT_VERSION}")
if(WIN32)
  target_compile_definitions(op4_cekirdek PUBLIC UNICODE _UNICODE NOMINMAX WIN32_LEAN_AND_MEAN)
endif()
op4_uyarilar(op4_cekirdek)

# ---------------------------------------------------------------------------------------------- op4_cekirdek_js
# Model çekirdeğini (QuickJS) çalıştıran ikililer Windows'ta 4 MB ana yığınla bağlanır (varsayılan 1 MB); JS yığın sınırı
# 3 MB'dir (js_ortami.cpp). Linux'ta ana yığın ulimit'ten gelir (çoğunlukla 8 MB).
set(OP4_YIGIN 4194304)
function(op4_yigin hedef)
  if(MSVC)
    target_link_options(${hedef} PRIVATE /STACK:${OP4_YIGIN})
  elseif(MINGW)
    target_link_options(${hedef} PRIVATE -Wl,--stack,${OP4_YIGIN})
  endif()
endfunction()
op4_kaynaklar(OP4_CEKIRDEK_JS_KAYNAKLARI kaynak/cekirdek_js)
add_library(op4_cekirdek_js STATIC ${OP4_CEKIRDEK_JS_KAYNAKLARI})
target_link_libraries(op4_cekirdek_js PUBLIC op4_cekirdek)
op4_uyarilar(op4_cekirdek_js)

# ---------------------------------------------------------------------------------------------- sınamalar
if(OP4_TESTLER)
  file(GLOB OP4_TEST_KAYNAKLARI CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/testler/cekirdek/*.cpp")
  list(SORT OP4_TEST_KAYNAKLARI)
  add_executable(op4_cekirdek_testleri ${OP4_TEST_KAYNAKLARI})
  target_link_libraries(op4_cekirdek_testleri PRIVATE op4_cekirdek_js op4::doctest)
  op4_yigin(op4_cekirdek_testleri)
  # Sınamalar depo dosyalarını (op4/veri, op4/testler/ortak, docs/) bu yollardan okur.
  get_filename_component(_op4_depo "${CMAKE_CURRENT_SOURCE_DIR}/.." ABSOLUTE)
  target_compile_definitions(op4_cekirdek_testleri PRIVATE OP4_KAYNAK_DIZINI="${CMAKE_CURRENT_SOURCE_DIR}"
                                                           OP4_DEPO_DIZINI="${_op4_depo}")
  if(MSVC)
    target_compile_definitions(op4_cekirdek_testleri PRIVATE _CRT_SECURE_NO_WARNINGS)  # getenv (motor sınamaları)
  endif()
  find_package(Python3 COMPONENTS Interpreter QUIET)
  if(Python3_Interpreter_FOUND)
    # Motor sınamaları (motor_*.cpp) bu yorumlayıcıyla `-m op4_sunucu` süreçleri başlatır (C dizesi: ileri eğik çizgi).
    file(TO_CMAKE_PATH "${Python3_EXECUTABLE}" _op4_python)
    target_compile_definitions(op4_cekirdek_testleri PRIVATE OP4_PYTHON="${_op4_python}")
  endif()
  op4_uyarilar(op4_cekirdek_testleri)
  if(MINGW)
    target_link_options(op4_cekirdek_testleri PRIVATE -static)
  endif()
  add_test(NAME op4_cekirdek COMMAND op4_cekirdek_testleri)
  # Motor sınamaları (motor_*.cpp) `python -m op4_sunucu` süreçleri başlatır: süre sınırı geniş.
  set_tests_properties(op4_cekirdek PROPERTIES TIMEOUT 900)
endif()

# ---------------------------------------------------------------------------------------------- op4.exe (Windows)
if(NOT WIN32)
  message(STATUS "Windows dışı: yalnız op4_cekirdek, op4_cekirdek_js ve sınamaları derlenir.")
  return()
endif()

set(OP4_SIMGE "${CMAKE_CURRENT_SOURCE_DIR}/kimlik/op4.ico")
if(NOT EXISTS "${OP4_SIMGE}")
  set(OP4_SIMGE "${CMAKE_CURRENT_SOURCE_DIR}/kimlik/op4_simge_placeholder.ico")
endif()
set(OP4_BILDIRIM "${CMAKE_CURRENT_SOURCE_DIR}/kaynak/op4.manifest")
configure_file(kaynak/op4.rc.in "${CMAKE_CURRENT_BINARY_DIR}/op4.rc" @ONLY)

op4_kaynaklar(OP4_UYGULAMA_KAYNAKLARI kaynak kaynak/arayuz kaynak/grafik kaynak/dosya kaynak/cozum)
add_executable(op4 WIN32 ${OP4_UYGULAMA_KAYNAKLARI} "${CMAKE_CURRENT_BINARY_DIR}/op4.rc")
# Geliştirme derlemesi (op4-yapi/Release/op4.exe) veri kataloglarını kaynak ağacından bulur; kurulu program <uygulama>\veri.
target_compile_definitions(op4 PRIVATE _CRT_SECURE_NO_WARNINGS OP4_GELISTIRME_VERI="${CMAKE_CURRENT_SOURCE_DIR}/veri")
target_link_libraries(op4 PRIVATE op4_cekirdek_js imgui windowscodecs ole32 shell32 shlwapi uuid msimg32 dwmapi)
if(OP4_HATA_AYIKLAMA)
  target_compile_definitions(op4 PRIVATE OP4_HATA_AYIKLAMA)
endif()
# Gölgelendiriciler: golgelendiriciler/op4.hlsl → FXC SM 5.1 bayt kodu + çalışma anı yedeği metni (MIMARI §6.1, D12).
op4_golgelendiriciler(op4)
if(MSVC)
  op4_uyarilar(op4)  # /W4 /permissive- /utf-8 /Zc:__cplusplus /MP (+ /WX: OP4_UYARI_HATA)
  # Bildirim (manifest) kaynak dosyasında gömülü; bağlayıcının kendi bildirimini üretmesini kapat.
  target_link_options(op4 PRIVATE /MANIFEST:NO)
elseif(MINGW)
  target_compile_options(op4 PRIVATE -Wall -Wextra -Wno-unused-parameter -Wno-missing-field-initializers)
  target_link_options(op4 PRIVATE -municode -static)
endif()
op4_yigin(op4)

# ---------------------------------------------------------------------------------------------- op4motor.exe (Windows)
# Hesap motoru süreci (MIMARI §8.1): python\python3XX.dll'i yükler, Py_Main(-X utf8 -B -m op4_sunucu …). Konsol alt
# sistemi (op4.exe onu CREATE_NO_WINDOW ile başlatır; elle çalıştırınca iletiler görünür); statik CRT; bağımlılık yok.
configure_file(kaynak/motor_barindirici/op4motor.rc.in "${CMAKE_CURRENT_BINARY_DIR}/op4motor.rc" @ONLY)
add_executable(op4motor kaynak/motor_barindirici/op4motor.cpp "${CMAKE_CURRENT_BINARY_DIR}/op4motor.rc")
target_compile_definitions(op4motor PRIVATE UNICODE _UNICODE NOMINMAX WIN32_LEAN_AND_MEAN)
if(MSVC)
  op4_uyarilar(op4motor)
elseif(MINGW)
  target_compile_options(op4motor PRIVATE -Wall -Wextra)
  target_link_options(op4motor PRIVATE -municode -static)
endif()

install(TARGETS op4 op4motor RUNTIME DESTINATION .)
install(DIRECTORY kimlik/ DESTINATION kimlik FILES_MATCHING PATTERN "*.png" PATTERN "*.ico")
# Veri katalogları (komutlar.json, oznitelikler.json, sahne_kodlari.json, sablonlar/) kurulu programda <uygulama>\veri.
install(DIRECTORY veri/ DESTINATION veri FILES_MATCHING PATTERN "*.json")
