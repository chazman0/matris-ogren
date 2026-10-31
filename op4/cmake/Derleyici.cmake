# op4 — derleyici uyarı ve denetleyici ayarları (MIMARI §19 kodlama kuralları; F1 iş 1.1, kabul A1, A2, A5). Sahibi: A.
#   MSVC     : /W4 /permissive- /utf-8 /Zc:__cplusplus /MP   + /WX (OP4_UYARI_HATA, varsayılan AÇIK)
#   Clang/GCC: -Wall -Wextra -Wpedantic                      + -Werror (OP4_UYARI_HATA)
#   OP4_ASAN : AddressSanitizer + UndefinedBehaviorSanitizer (Clang/GCC; ön ayar linux-cekirdek-asan). UBSan bulguları
#              sınamayı düşürür (-fno-sanitize-recover).
# Üçüncü taraf hedefleri (imgui, quickjs …) bu işlevi kullanmaz; kendi uyarı düzeylerinde derlenir.
option(OP4_UYARI_HATA "Uyarılar hata sayılır (/WX, -Werror)" ON)
option(OP4_ASAN "AddressSanitizer + UndefinedBehaviorSanitizer (Clang/GCC)" OFF)

if(OP4_ASAN)
  if(MSVC)
    message(FATAL_ERROR "OP4_ASAN yalnız Clang/GCC ile (linux-cekirdek-asan ön ayarı)")
  endif()
  set(OP4_ASAN_BAYRAKLARI -fsanitize=address,undefined -fno-omit-frame-pointer -fno-sanitize-recover=undefined)
  add_compile_options(${OP4_ASAN_BAYRAKLARI})
  add_link_options(-fsanitize=address,undefined)
  message(STATUS "op4: AddressSanitizer + UndefinedBehaviorSanitizer açık")
endif()

function(op4_uyarilar hedef)
  if(MSVC)
    target_compile_options(${hedef} PRIVATE /utf-8 /W4 /permissive- /Zc:__cplusplus /MP)
    if(OP4_UYARI_HATA)
      target_compile_options(${hedef} PRIVATE /WX)
    endif()
  else()
    target_compile_options(${hedef} PRIVATE -Wall -Wextra -Wpedantic)
    if(OP4_UYARI_HATA)
      target_compile_options(${hedef} PRIVATE -Werror)
    endif()
  endif()
endfunction()
