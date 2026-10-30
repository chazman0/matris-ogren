# nlohmann/json 3.12.0 (MIT; 2025-04) — yalnız başlık. Hedef: op4::json. Sahibi: A.
op4_bagimlilik_url(nlohmann_json
  URL https://github.com/nlohmann/json/releases/download/v3.12.0/json.tar.xz
  SHA256 42f6e95cad6ec532fd372391373363b62a14af6d771056dbfc86160e6dfff7aa)
add_library(op4_json INTERFACE)
add_library(op4::json ALIAS op4_json)
target_include_directories(op4_json SYSTEM INTERFACE "${nlohmann_json_SOURCE_DIR}/include")
