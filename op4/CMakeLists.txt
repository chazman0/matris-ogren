# op4 — Opus Fortis yapısal modelleme / analiz programı (Windows, yerel C++20 + DirectX 12 + Dear ImGui + gömülü CPython).
#
# Derleme (Windows, Visual Studio 2022+ / MSVC x64):
#   cmake -S op4 -B op4-yapi -A x64
#   cmake --build op4-yapi --config Release --parallel
#   cmake --install op4-yapi --config Release --prefix paket        # op4.exe + kimlik/
#   python op4/araclar/python_hazirla.py --paket paket                # gömülü Python + numpy/sympy + motor/*.py
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

if(NOT WIN32)
  message(FATAL_ERROR "op4 yalnız Windows için derlenir (MSVC x64; sözdizimi denetimi için MinGW-w64).")
endif()

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
if(MSVC)
  # Statik C/C++ çalışma zamanı: op4.exe, Visual C++ yeniden dağıtılabilir paketi gerektirmez.
  set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")
endif()

# ---------------------------------------------------------------------------------------------- Dear ImGui (docking)
set(OP4_IMGUI_ETIKET "v1.92.9b-docking")
set(OP4_IMGUI_ISLEME "b48d1afbe8ee8b238e2961dc363a949dd7304e23")
set(OP4_IMGUI_DIZINI "" CACHE PATH "Hazır Dear ImGui (docking dalı) kaynak klasörü; boşsa ${OP4_IMGUI_ETIKET} indirilir")
if(OP4_IMGUI_DIZINI)
  set(imgui_SOURCE_DIR "${OP4_IMGUI_DIZINI}")
else()
  include(FetchContent)
  FetchContent_Declare(imgui
    GIT_REPOSITORY https://github.com/ocornut/imgui.git
    GIT_TAG ${OP4_IMGUI_ETIKET}
    GIT_SHALLOW TRUE)
  FetchContent_MakeAvailable(imgui)
  # Etiket değiştirilmiş mi? İşleme özetini doğrula (tedarik zinciri güvencesi).
  find_package(Git QUIET)
  if(GIT_FOUND)
    execute_process(COMMAND "${GIT_EXECUTABLE}" -C "${imgui_SOURCE_DIR}" rev-parse HEAD
                    OUTPUT_VARIABLE _imgui_isleme OUTPUT_STRIP_TRAILING_WHITESPACE RESULT_VARIABLE _sonuc)
    if(_sonuc EQUAL 0 AND NOT _imgui_isleme STREQUAL OP4_IMGUI_ISLEME)
      message(FATAL_ERROR "Dear ImGui ${OP4_IMGUI_ETIKET} beklenen işleme değil: ${_imgui_isleme} != ${OP4_IMGUI_ISLEME}")
    endif()
  endif()
endif()

add_library(imgui STATIC
  ${imgui_SOURCE_DIR}/imgui.cpp
  ${imgui_SOURCE_DIR}/imgui_draw.cpp
  ${imgui_SOURCE_DIR}/imgui_tables.cpp
  ${imgui_SOURCE_DIR}/imgui_widgets.cpp
  ${imgui_SOURCE_DIR}/backends/imgui_impl_win32.cpp
  ${imgui_SOURCE_DIR}/backends/imgui_impl_dx12.cpp)
target_include_directories(imgui PUBLIC ${imgui_SOURCE_DIR} ${imgui_SOURCE_DIR}/backends)
target_compile_definitions(imgui PUBLIC IMGUI_DISABLE_OBSOLETE_FUNCTIONS IMGUI_DISABLE_DEMO_WINDOWS UNICODE _UNICODE)
target_link_libraries(imgui PUBLIC d3d12 dxgi d3dcompiler dwmapi)
if(MSVC)
  target_compile_options(imgui PRIVATE /utf-8 /W3)
endif()

# ---------------------------------------------------------------------------------------------- op4.exe
set(OP4_SIMGE "${CMAKE_CURRENT_SOURCE_DIR}/kimlik/op4.ico")
if(NOT EXISTS "${OP4_SIMGE}")
  set(OP4_SIMGE "${CMAKE_CURRENT_SOURCE_DIR}/kimlik/op4_simge_placeholder.ico")
endif()
set(OP4_BILDIRIM "${CMAKE_CURRENT_SOURCE_DIR}/kaynak/op4.manifest")
configure_file(kaynak/op4.rc.in "${CMAKE_CURRENT_BINARY_DIR}/op4.rc" @ONLY)

add_executable(op4 WIN32
  kaynak/ana.cpp
  kaynak/acilis.cpp
  kaynak/arayuz.cpp
  kaynak/geometri.cpp
  kaynak/grafik.cpp
  kaynak/gunluk.cpp
  kaynak/motor.cpp
  kaynak/proje.cpp
  kaynak/resim.cpp
  "${CMAKE_CURRENT_BINARY_DIR}/op4.rc")
target_compile_definitions(op4 PRIVATE UNICODE _UNICODE NOMINMAX WIN32_LEAN_AND_MEAN _CRT_SECURE_NO_WARNINGS
                                       OP4_SURUM="${PROJECT_VERSION}")
target_link_libraries(op4 PRIVATE imgui windowscodecs ole32 shell32 shlwapi uuid msimg32 dwmapi)
if(MSVC)
  target_compile_options(op4 PRIVATE /utf-8 /W4 /permissive- /Zc:__cplusplus /MP)
  # Bildirim (manifest) kaynak dosyasında gömülü; bağlayıcının kendi bildirimini üretmesini kapat.
  target_link_options(op4 PRIVATE /MANIFEST:NO)
elseif(MINGW)
  target_compile_options(op4 PRIVATE -Wall -Wextra -Wno-unused-parameter -Wno-missing-field-initializers)
  target_link_options(op4 PRIVATE -municode -static)
endif()

install(TARGETS op4 RUNTIME DESTINATION .)
install(DIRECTORY kimlik/ DESTINATION kimlik FILES_MATCHING PATTERN "*.png" PATTERN "*.ico")
