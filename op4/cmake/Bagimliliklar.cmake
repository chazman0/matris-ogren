# op4 — üçüncü taraf bağımlılıkları (MIMARI §2.2.8, §19). Her bağımlılık sabit sürüm + işleme özeti ya da SHA256 ile
# alınır; sürüm en az iki hafta önce yayımlanmış olmalıdır. Çevrim dışı / yerel kopya: -DOP4_<AD>_DIZINI=<klasör>.
#
# Her bağımlılık kendi dosyasındadır (cmake/bagimlilik_<ad>.cmake) ve SAHİBİ o dosyayı yazan pakettir (MIMARI
# "F1 paket sözleşmeleri"): json, doctest, imgui → A; quickjs → B; miniz → D. Yeni bağımlılık = yeni dosya; bu dosya
# değişmez (hepsi aşağıda sırayla içerilir).
include(FetchContent)
if(POLICY CMP0135)
  cmake_policy(SET CMP0135 NEW)  # URL indirmelerinde zaman damgası çıkarım anı
endif()

# op4_bagimlilik_git(<ad> REPO <url> ETIKET <etiket> ISLEME <40 hex>)
#   <ad>_SOURCE_DIR değişkenini kurar. OP4_<AD>_DIZINI verilmişse indirmez. İndirilen etiketin işleme özeti doğrulanır.
#   Kaynak ağacı add_subdirectory ile EKLENMEZ: hedefi bağımlılık dosyası kendisi tanımlar (seçenek / hedef kirliliği yok).
function(op4_bagimlilik_git ad)
  cmake_parse_arguments(A "" "REPO;ETIKET;ISLEME" "" ${ARGN})
  string(TOUPPER "${ad}" AD)
  set(OP4_${AD}_DIZINI "" CACHE PATH "Hazır ${ad} kaynak klasörü; boşsa ${A_ETIKET} indirilir")
  if(OP4_${AD}_DIZINI)
    set(${ad}_SOURCE_DIR "${OP4_${AD}_DIZINI}" PARENT_SCOPE)
    return()
  endif()
  FetchContent_Declare(${ad} GIT_REPOSITORY "${A_REPO}" GIT_TAG "${A_ETIKET}" GIT_SHALLOW TRUE SOURCE_SUBDIR op4_yok)
  FetchContent_MakeAvailable(${ad})
  find_package(Git QUIET)
  if(GIT_FOUND)
    execute_process(COMMAND "${GIT_EXECUTABLE}" -C "${${ad}_SOURCE_DIR}" rev-parse HEAD
                    OUTPUT_VARIABLE _isleme OUTPUT_STRIP_TRAILING_WHITESPACE RESULT_VARIABLE _sonuc)
    if(_sonuc EQUAL 0 AND NOT _isleme STREQUAL A_ISLEME)
      message(FATAL_ERROR "${ad} ${A_ETIKET} beklenen işleme değil: ${_isleme} != ${A_ISLEME}")
    endif()
  endif()
  set(${ad}_SOURCE_DIR "${${ad}_SOURCE_DIR}" PARENT_SCOPE)
endfunction()

# op4_bagimlilik_url(<ad> URL <url> SHA256 <64 hex>)
function(op4_bagimlilik_url ad)
  cmake_parse_arguments(A "" "URL;SHA256" "" ${ARGN})
  string(TOUPPER "${ad}" AD)
  set(OP4_${AD}_DIZINI "" CACHE PATH "Hazır ${ad} kaynak klasörü; boşsa ${A_URL} indirilir")
  if(OP4_${AD}_DIZINI)
    set(${ad}_SOURCE_DIR "${OP4_${AD}_DIZINI}" PARENT_SCOPE)
    return()
  endif()
  FetchContent_Declare(${ad} URL "${A_URL}" URL_HASH "SHA256=${A_SHA256}" SOURCE_SUBDIR op4_yok)
  FetchContent_MakeAvailable(${ad})
  set(${ad}_SOURCE_DIR "${${ad}_SOURCE_DIR}" PARENT_SCOPE)
endfunction()

file(GLOB _op4_bagimliliklar "${CMAKE_CURRENT_LIST_DIR}/bagimlilik_*.cmake")
list(SORT _op4_bagimliliklar)
foreach(_d IN LISTS _op4_bagimliliklar)
  include("${_d}")
endforeach()
