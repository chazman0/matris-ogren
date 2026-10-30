# doctest 2.5.3 (MIT; 2026-07) — C++ birim sınama çatısı, yalnız başlık. Hedef: op4::doctest. Sahibi: A.
if(OP4_TESTLER)
  op4_bagimlilik_git(doctest
    REPO https://github.com/doctest/doctest.git
    ETIKET v2.5.3
    ISLEME 2d0a9359a60c51affe2a9bebb1be1dca47868151)
  add_library(op4_doctest INTERFACE)
  add_library(op4::doctest ALIAS op4_doctest)
  target_include_directories(op4_doctest SYSTEM INTERFACE "${doctest_SOURCE_DIR}")
endif()
