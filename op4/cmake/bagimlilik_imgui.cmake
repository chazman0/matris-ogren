# Dear ImGui v1.92.9b-docking (MIT) — yalnız Windows (DX12 + Win32 arka uçları). Hedef: imgui. Sahibi: A (sürüm), C (kullanım).
# OP4_IMGUI_DIZINI ile yerel kopya verilebilir (MinGW denetimi).
if(WIN32)
  op4_bagimlilik_git(imgui
    REPO https://github.com/ocornut/imgui.git
    ETIKET v1.92.9b-docking
    ISLEME b48d1afbe8ee8b238e2961dc363a949dd7304e23)
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
endif()
