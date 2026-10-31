#!/usr/bin/env node
/* op4 — QuickJS ön yüklemesinin harmanlama (localeCompare) tablosu üreteci (MIMARI §9.2; kabul B2, B6). Sahibi: B.
   ICU'suz QuickJS'te String.prototype.localeCompare kod noktası karşılaştırmasıdır; docs/tablo_editoru.js sıralaması
   localeCompare(b, "tr", {numeric: true, sensitivity: "base"}) kullanır (eşdeğerlik derleminde node ile ayrıştı). Ön yükleme
   (op4/js/op4_onyukleme.js) bu tabloyla ICU'nun tr ve kök (en) harmanlamasını üç düzeyde (temel harf, aksan, büyük/küçük)
   karakter başına yeniden kurar. Tablo node'un ICU'sundan üretilir:
     node op4/testler/js/harman_uret.js          → op4_onyukleme.js içindeki HARMAN tablosunu günceller
   op4/testler/js/onyukleme.test.js tablonun güncel olduğunu ve öykünmenin ICU ile aynı sırayı verdiğini denetler. */
"use strict";
const fs = require("node:fs");
const path = require("node:path");

const ONYUKLEME = path.join(__dirname, "..", "..", "js", "op4_onyukleme.js");

/** Tablodaki karakterler: ASCII, Latin-1, Latin Genişletilmiş-A ve sık noktalama / simgeler. */
function karakterler() {
  const k = [0x09, 0x0a, 0x0d];
  for (let c = 0x20; c <= 0x7e; c++) k.push(c);
  for (let c = 0xa0; c <= 0x17f; c++) k.push(c);
  k.push(0x2013, 0x2014, 0x2018, 0x2019, 0x201c, 0x201d, 0x2022, 0x2026, 0x2030, 0x20ac, 0x2122, 0x2212, 0x2264, 0x2265, 0x221e,
    0x00d7, 0x2032, 0x2033, 0x0394, 0x03a3, 0x03b1, 0x03b2, 0x03b3, 0x03b4, 0x03bb, 0x03bc, 0x03c0, 0x03c3, 0x03c6);
  return Array.from(new Set(k)).sort((a, b) => a - b).map((c) => String.fromCharCode(c));
}

/**
 * Yerel ayar için karakter → [birincil, ikincil, üçüncül] sıra numaraları (ICU sırasından). Tümüyle yok sayılan karakter
 * (ICU'da "" ile eşit) birincil 0 alır.
 */
function tablo(yerel) {
  const tam = new Intl.Collator(yerel, { sensitivity: "variant" }), temel = new Intl.Collator(yerel, { sensitivity: "base" });
  const aksan = new Intl.Collator(yerel, { sensitivity: "accent" });
  const k = karakterler().filter((c) => tam.compare(c, "") !== 0);
  k.sort((a, b) => tam.compare(a, b) || (a < b ? -1 : a > b ? 1 : 0));
  const out = [];
  let p = 0, s = 0, t = 0, onceki = null;
  for (const c of k) {
    if (onceki === null || temel.compare(onceki, c) !== 0) { p++; s = 1; t = 1; }
    else if (aksan.compare(onceki, c) !== 0) { s++; t = 1; }
    else if (tam.compare(onceki, c) !== 0) t++;
    out.push([c.charCodeAt(0), p, s, t]);
    onceki = c;
  }
  return out;
}

/** Ön yüklemeye gömülen metin: "kod:birincil.ikincil.üçüncül" çiftleri (36 tabanlı), virgülle. */
function tabloMetni(yerel) {
  return tablo(yerel).map((x) => x[0].toString(36) + ":" + x[1].toString(36) + "." + x[2].toString(36) + "." + x[3].toString(36)).join(",");
}

function gomulu() {
  return "  const HARMAN = {\n    icu: \"" + process.versions.icu + "\",\n    tr: \"" + tabloMetni("tr") + "\",\n    kok: \"" +
    tabloMetni("en") + "\",\n  };\n";
}
/** Ön yüklemeye gömülü tablonun üretildiği ICU sürümü (yoksa null). */
function gomuluIcu(metin) {
  const m = /^\s*icu: "([^"]*)",$/m.exec(metin);
  return m ? m[1] : null;
}

const BAS = "  // HARMAN_TABLOSU_BAS (op4/testler/js/harman_uret.js üretir; elle değiştirmeyin)\n";
const SON = "  // HARMAN_TABLOSU_SON\n";

if (require.main === module) {
  const m = fs.readFileSync(ONYUKLEME, "utf8");
  const a = m.indexOf(BAS), b = m.indexOf(SON);
  if (a < 0 || b < a) throw new Error("op4_onyukleme.js içinde HARMAN_TABLOSU_BAS / _SON işaretleri yok");
  fs.writeFileSync(ONYUKLEME, m.slice(0, a + BAS.length) + gomulu() + m.slice(b));
  process.stderr.write("harman: tr " + tablo("tr").length + ", kök " + tablo("en").length + " karakter → " + path.relative(process.cwd(), ONYUKLEME) + "\n");
}

module.exports = { BAS: BAS, SON: SON, gomulu: gomulu, gomuluIcu: gomuluIcu, tablo: tablo, karakterler: karakterler };
