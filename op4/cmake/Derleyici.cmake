# op4 — derleyici uyarı ayarları (MIMARI §19 kodlama kuralları). Sahibi: A.
#   MSVC : /W4 /permissive- /utf-8 /Zc:__cplusplus /MP   (+ /WX: OP4_UYARI_HATA)
#   Clang/GCC: -Wall -Wextra -Wpedantic                  (+ -Werror: OP4_UYARI_HATA)
# F1 iş 1.1: OP4_UYARI_HATA varsayılanı ON yapılır (A); o zamana dek Linux işi ve sözleşme testi ON ile derler.
option(OP4_UYARI_HATA "Uyarılar hata sayılır (/WX, -Werror)" OFF)

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
