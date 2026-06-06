
<div align="center">

# 🌐 MRR Programlama Dili: Tersine Mühendislik, Malware geliştirme, exploit geliştirme, payload geliştirme, reverse shell açma konusunda 1. seviye
**yeni güncelleme ile beraber ağ üzerinden module paylaşımı payload geliştirme reversel shell açma gibi birden fazla işlem eklendi**

![Build Status](https://img.shields.io/badge/build-passing-red)
![Version](https://img.shields.io/badge/version-1.0.1-orange)
![License](https://img.shields.io/badge/license-MIT-purple)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-lightgreen)

</div>


# MRR Programlama Dili Rehberi

Bu belge, MRR dilinin tüm temel yapılarını sıfırdan en detaylı şekilde açıklar. Word belgesine yapıştırıp kullanabilir, örnek kod bloklarını kutu içine alarak sunabilirsiniz.

---

## 1. Giriş: MRR Nedir?

MRR, güvenlik ve sistem programlamasına odaklı, modern sözdizimiyle tasarlanmış bir programlama dilidir. Amacı, düşük seviyeli kontrolü kolaylaştırırken aynı zamanda günlük görevleri hızlıca çözebilmektir. MRR, bellek yönetimini, dahili güvenlik kontrollerini ve exploit/shellcode yeteneklerini aynı dil içinde sunar.

- Hedef kitle: güvenlik araştırmacıları, exploit geliştiricileri, kernel/driver yazarları ve sistem programcıları
- Temel avantaj: yüksek seviyeli bir yazım rahatlığı ile sistem seviyesinde ifadeler
- Çalışma modu: `mrr` komutu ile doğrudan çalıştırma; Python arka planda olabilir ama kullanıcı için tek komut yeterlidir

```mrr
println("MRR diline hoş geldiniz!")
```

Bu kod, ekran çıktısı veren en basit MRR örneğidir.

---

## 2. Programlamanın Temelleri

Programlama, bir bilgisayarın yapmasını istediğiniz işlemleri bir dizi komut olarak tanımlamaktır. MRR’de bu komutlar; değişken tanımlama, karar alma, döngü yapıları, fonksiyon çağrıları ve bellek işlemleri şeklinde ifade edilir.

### 2.1. Değişkenler ve Atama

MRR’de değişkenler `let`, `mut` veya `const` ile tanımlanır. `let` varsayılan olarak değiştirilemez, `mut` değiştirilebilir değerler için kullanılır.

```mrr
let x: i32 = 10
mut count: u64 = 0
const greeting: str = "Merhaba"
```

- `let`: değişken bildirimi.
- `x`: değişken adı.
- `: i32`: değişkenin tipi, burada 32-bit işaretli tam sayı.
- `= 10`: başlangıç değeri.
- `mut`: bu değişkenin sonradan güncellenebileceğini belirtir.
- `u64`: 64-bit işaretsiz tam sayı.
- `const`: bu değer sonradan değiştirilemez.
- `str`: string (metin) tipi.

### 2.2. Veri Tipleri

MRR’nin temel tipleri:

- `i32`, `i64`: işaretli tam sayılar
- `u32`, `u64`: işaretsiz tam sayılar
- `f32`, `f64`: kayan nokta
- `bool`: `true` / `false`
- `str`: metin
- `ptr<T>`: işaretçi
- `byte`: bayt

```mrr
let id: u64 = 12345
let pi: f64 = 3.1415
let aktif: bool = true
let text: str = "MRR"
```

### 2.3. Yorumlar

Tek satır yorum için `//`, Python stili için `#` ve blok yorum için `/* ... */` kullanılabilir.

```mrr
// Bu tek satırlık yorumdur
# Bu da Python tarzı yorumdur
/* 
   Bu da blok yorumdur
*/
```

---

## 3. MRR’nin Temel Mimarisine Genel Bakış

MRR, iki ana bileşen etrafında kuruludur:

1. **Söz Dizimi**: `interpreter/mrr_lexer.py` ve `interpreter/mrr_parser.py`
2. **Çalışma Zamanı**: `interpreter/mrr_evaluator.py`

Bu mimari size iki avantaj sağlar:

- Hatalı kodu hızlıca yakalamak
- Dinamik olarak kod çalıştırmak

MRR’nin dili, tip sistemi ve `unsafe`/`kernel`/`exploit` bloklarıyla birlikte karmaşık güvenlik senaryolarını destekler.

---

## 4. Kurulum ve `mrr` Komut Satırı

MRR dilini kullanmak için hedef, `mrr` komutunun doğrudan çalışmasıdır. Yani:

- `python.exe mrr ...` değil
- `mrr` yazıldığında çalışacak

Bunun için sistem PATH’ine `mrr.bat` veya `mrr` kabuk betiği ekleyebilirsiniz.

```text
mrr run hello.mrr
mrr repl
mrr compile myproject.mrr
```

### 4.1. Doğrudan `mrr` çalıştırma

Windows için bir `mrr.bat` dosyası şu şekilde olabilir:

```bat
@echo off
python "%~dp0\interpreter\main.py" %*
```

Unix için benzer bir `mrr` kabuk betiği:

```sh
#!/usr/bin/env sh
python3 "$(dirname "$0")/interpreter/main.py" "$@"
```

Bunlar PATH’e eklenince artık `mrr` tek komut olarak çalışır.

---

## 5. İlk MRR Programı ve Temel Giriş/Çıkış

Aşağıdaki örnek, en temel MRR programıdır. `println` fonksiyonu metni ekrana yazdırır.

```mrr
println("MRR diline hoş geldiniz!")
```

Bu kod, ekrana bir mesaj yazdırır ve alt satıra geçer.

#### Kullanıcı girdisi alma

```mrr
let raw_input = input("Adınızı girin: ")
let safe_input = sanitize(raw_input)
printf("Merhaba #{safe_input}!")
```

- `input(...)`: Kullanıcıdan metin girişi alır.
- `sanitize(...)`: Gelen veriyi temizleyip güvenli hale getirir.
- `#{...}` ifadesi string interpolasyonudur.

---

## 6. Değişkenler, Tipler ve Dönüşümler

### 6.1. Basit değerler

```mrr
let sayi: i32 = 42
let ondalik: f64 = 2.718
let metin: str = "Merhaba"
let dogru: bool = true
```

### 6.2. Tip dönüşümü

```mrr
let x: i32 = integer("Sayı girin: ")
let y: f64 = float(3)
let s: str = str(123)
```

- `integer(...)`: Stringi tam sayıya dönüştürür.
- `float(...)`: Değerin kayan nokta karşılığını oluşturur.
- `str(...)`: Her şeyi metne çevirir.

---

## 7. Kontrol Akışları

MRR’de kullanılan temel kontrol yapıları şöyledir.

### 7.1. `if` / `otherwise`

```mrr
let score: i32 = 75

if score >= 90:
    println("A+")
elif score >= 80:
    println("A")
otherwise:
    println("B veya altı")
```

- `>=`: büyüktür veya eşittir.
- `elif`: alternatif koşul.
- `otherwise`: hiçbir koşul sağlanmadığında çalışan blok.

### 7.2. `for` döngüsü

```mrr
for i in range(5):
    println(i)
```

- `range(5)`: 0’dan 4’e kadar değer üretir.
- `i`: döngü değişkenidir.

### 7.3. `while` döngüsü

```mrr
mut counter: i32 = 0
while counter < 5:
    println(counter)
    counter = counter + 1
```

- `mut`: değişkenin değiştirilebilir olduğunu gösterir.
- `while`: koşul doğru olduğu sürece döngüyü tekrarlar.

### 7.4. `loop`

```mrr
loop:
    let command = input("> ")
    if command == "exit":
        break
    println("Komut: #{command}")
```

- `loop:`: sonsuz döngü başlatır.
- `break`: döngüyü sonlandırır.

---

## 8. Fonksiyonlar ve Modüler Programlama

MRR’de fonksiyonlar hem `fonction.create` hem de `fn` ile tanımlanabilir.

### 8.1. Basit Fonksiyon

```mrr
fonction.create topla(a: i32, b: i32) -> i32:
    return a + b

let toplam = topla(5, 7)
println(toplam)
```

- `fonction.create`: fonksiyon bildirimi.
- `-> i32`: dönüş tipi.
- `return`: fonksiyon sonucunu döndürür.

### 8.2. `mut` parametre ve varsayılan değer

```mrr
fonction.create arttir(mut x: i32, amount: i32 = 1) -> i32:
    x = x + amount
    return x
```

- `mut x`: parametrenin değiştirilebilir olduğunu gösterir.
- `amount: i32 = 1`: varsayılan değer `1` olarak atanır.

### 8.3. Lambda / anonim fonksiyon

```mrr
let kare = |x: i32| => x * x
println(kare(4))
```

- `|x: i32| => x * x`: tek satırlık anonim fonksiyon.

### 8.4. Pipe operatörü

```mrr
let result = 5 |> square |> to_string
```

- `|>`: bir değeri bir fonksiyona geçirir.

### 8.5. Modül ve `use`

```mrr
module myapp
use std.io
use std.mem::{alloc, free}
```

- `module`: kodun modülünü tanımlar.
- `use`: başka bir modülü veya isimleri içe aktarır.

---

## 9. Bellek Yönetimi: `unsafe` ve `alloc`

MRR’de doğrudan bellek kullanımı için `unsafe` blokları vardır.

### 9.1. `unsafe` bloku

```mrr
unsafe:
    let p: ptr<i32> = alloc(8)
    p.write(1337)
    let value = p.read()
    println(value)
    free(p)
```

- `unsafe:`: bu bloğun güvenli olmayan işlemler içerdiğini belirtir.
- `ptr<i32>`: `i32` tipinde işaretçi.
- `alloc(8)`: 8 baytlık bellek ayırır.
- `write(...)`: bellek içerisine yazar.
- `read()`: bellekten okur.
- `free(...)`: belleği serbest bırakır.

### 9.2. `drop` kullanımı

```mrr
unsafe:
    let p: ptr<i32> = alloc(8)
    drop(p)
```

- `drop(p)`: aynı `free` gibi belleği temizler.

### 9.3. `volatile` ön eki

```mrr
unsafe:
    volatile p.write(0x55)
```

- `volatile`: bellek yazmasının optimize edilmesini engeller.
- Donanım ve paylaşılan bellek erişimlerinde kullanışlıdır.

---

## 10. Shellcode ve Inline Assembly

MRR’in en güçlü yönlerinden biri, shellcode ve inline assembly desteğidir.

### 10.1. `shellcode` blokları

```mrr
let sc = shellcode x86_64 {
    db "Hello", 0x20, 0x57, 0x6F, 0x72, 0x6C, 0x64, 0x00
}
println(sc.len())
```

- `shellcode x86_64 { ... }`: x86_64 için shellcode bloğu.
- `db`: ham bayt tanımı yapar.
- `sc.len()`: oluşturulan shellcode’un uzunluğunu döner.

### 10.2. `asm` bloğu

```mrr
unsafe:
    asm { "mov rax, rbx" }
```

- `asm { ... }`: inline assembly ifadesi.
- Bu kod, register düzeyinde işlem yapar.

---

## 11. FFI / Harici Kütüphane Entegrasyonu

MRR, harici kütüphaneleri doğrudan çağırmaya izin verir.

### 11.1. `add.code`

```mrr
add.code "user32.dll" as user32
let result = user32.MessageBoxA(0, "Merhaba", "MRR", 0)
```

- `add.code`: dış kütüphaneyi yükler.
- `as user32`: bu kütüphaneye `user32` adı verilir.
- `MessageBoxA(...)`: kütüphane fonksiyonunu çağırır.

### 11.2. `use` modül kullanımı

```mrr
use std.io
use std.mem::{alloc, free}
```

- `use`: başka bir modülden isimleri içe aktarır.

### 11.3. Güvenlik kontrolü

FFI çağrıları genellikle `unsafe` bloklarında daha güvenlidir. Bu, MRR’nin harici kod yüklemeyi kontrollü şekilde desteklediğini gösterir.

---

## 12. Güvenlik Özellikleri

MRR, kendine özgü güvenlik özellikleri içerir.

### 12.1. `secure` tipi

```mrr
secure let secret: str = "parola"
```

- `secure`: değişkenin hassas veri içerdiğini belirtir.

### 12.2. `sanitize()`

```mrr
let raw_input = input("Giriş: ")
let safe_input = sanitize(raw_input)
println(safe_input)
```

- `sanitize(...)`: kullanıcı verisini temizler.

### 12.3. `temporal`

```mrr
temporal mut balance: i32 = 100
balance = 200
balance = 300
balance.rollback(2)
printf(balance)
```

- `temporal`: değişken geçmişini tutar.
- `rollback(2)`: son iki değişikliği geri alır.

### 12.4. `shared`

```mrr
shared<"node1"> let shared_value = 42
```

- `shared<"node1">`: değerin belirli bir hedefle paylaşılabileceğini gösterir.

---

## 13. String Interpolasyonu

```mrr
let username: str = "Ahmet"
println("Hoş geldin, #{username}!")
```

- `#{username}`: string içine dinamik bir değer yerleştirir.

---

## 14. Struct Tanımlama

```mrr
struct Point:
    x: i32
    y: i32

let p = Point(10, 20)
println(p.x)
```

- `struct Point:`: yapı tanımı.
- `x: i32`, `y: i32`: alan tipleri.
- `Point(10, 20)`: örnek oluşturma.

---

## 15. `match` Yapısı

```mrr
let value = 2

match value:
    1 => println("Bir")
    2 => println("İki")
    _ => println("Diğer")
```

- `match`: desen eşleştirme yapısı.
- `_`: varsayılan durum.

---

## 16. `try/catch/finally`

```mrr
try:
    let x = 10 / 0
    println(x)
catch err:
    println("Hata: #{err}")
finally:
    println("Her durumda çalışır")
```

- `try`: hata potansiyeli olan kod bloğu.
- `catch err`: hatayı yakalama bloğu.
- `finally`: her durumda çalıştırılır.

---

## 17. `defer`

```mrr
defer:
    println("Fonksiyon sonunda çalıştı")
```

- `defer`: blok çıkmadan hemen önce çalıştırılacak kodu kaydeder.

---

## 18. Komple Bir Örnek

```mrr
module bank_app
use std.io

temporal mut balance: i32 = 100

fonction.create deposit(amount: i32):
    balance = balance + amount

fonction.create withdraw(amount: i32):
    if amount > balance:
        println("Yetersiz bakiye")
    otherwise:
        balance = balance - amount

fonction.create main():
    println("Bankacılık uygulamasına hoş geldiniz")
    deposit(50)
    withdraw(30)
    println("Bakiye: #{balance}")

main()
```

- `module bank_app`: modül tanımı.
- `temporal mut balance`: geçmiş saklayan sayaç.
- `deposit(...)` ve `withdraw(...)`: fonksiyonlar.
- `main()`: uygulamayı başlatır.

---

## 19. `mrr` Komutunun Doğrudan Çalışması

Word belgesinde bu kısmı açıkça yazın: `mrr` komutu doğrudan çalışmalıdır.

```text
mrr run example.mrr
mrr repl
mrr compile example.mrr
```

- `run`: MRR dosyasını çalıştırır.
- `repl`: etkileşimli kabuk açar.
- `compile`: derleyici modu varsa kaynak kodu derler.

---

## 20. Pratik Örnekler ve Kullanım Senaryoları

MRR, aşağıdaki alanlarda özellikle güçlüdür:

- Shellcode üretimi: `shellcode_gen.mrr`
- Bellek tarama: `memory_scan.mrr`
- Kernel/driver prototipleri: `kernel_driver.mrr`
- Ağ testleri: `network_test.mrr`
- Güvenlik tarayıcı: `vuln_scanner.mrr`

### 20.1. Shellcode üretimi

```mrr
let sc = shellcode x86_64 {
    db "Hello", 0x00
}
println("Shellcode length: #{sc.len()}")
```

### 20.2. Bellek okuma/yazma

```mrr
unsafe:
    let data: ptr<byte> = alloc(16)
    data.write(0x41)
    println(data.read())
    free(data)
```

### 20.3. Basit exploit modülü

```mrr
exploit MyExploit:
    fn check() -> bool:
        return true

    fn payload():
        println("Exploit payload çalıştı")
```

---

## 21. MRR’nin Çalışma Modeli

MRR, interpretasyon esnasında AST oluşturur ve değerlendirme yapar. Bu sayede:

- Hata mesajları anlamlıdır
- Otomatik düzeltme ve sözdizimi uyarıları yapılabilir
- REPL deneyimi geliştirilebilir

### 21.1. Otomatik hata düzeltme

MRR derleyicisi, basit sözdizimi hatalarında düzeltme önerisi üretebilir. Bu özellik, geliştirme deneyimini hızlandırır.

---

## 22. Word Belgesine Yapıştırma İpuçları

Kod bloklarını Word’e yapıştırdıktan sonra:

- Kod bloğunu seçin
- Kenarlık ekleyin (`Borders > Outside Borders`)
- Arka planı açık gri veya açık mavi yapın
- Yazı tipini `Consolas` veya `Courier New` yapın

Bu sayede kodlar Word’de kutu içinde görünür.

---

## 23. Ek Kaynaklar ve İleri Okuma

MRR dilini daha iyi kullanmak için:

- `examples/` klasöründeki dosyaları inceleyin
- `docs/language_spec.md` dosyasını okuyun
- `interpreter/` altında `lexer`, `parser`, `evaluator` yapısını takip edin

Bu belge, MRR’nin ne yaptığını, hangi özellikleri sunduğunu ve nasıl kullanılacağını anlatan kapsamlı bir başlangıç kaynağıdır.


# KERNEL SEVİYEDEKİ DOSYALAR VE YAZILIM SİSTEM DOSYALARININ ŞEMASI

```mrr
├───.venv
│   ├───Include
│   ├───Lib
│   │   └───site-packages
│   │       ├───pip
│   │       │   ├───_internal
│   │       │   │   ├───cli
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───commands
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───distributions
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───index
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───locations
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───metadata
│   │       │   │   │   ├───importlib
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───models
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───network
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───operations
│   │       │   │   │   ├───build
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   ├───install
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───req
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───resolution
│   │       │   │   │   ├───legacy
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   ├───resolvelib
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───utils
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───vcs
│   │       │   │   │   └───__pycache__
│   │       │   │   └───__pycache__
│   │       │   ├───_vendor
│   │       │   │   ├───cachecontrol
│   │       │   │   │   ├───caches
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───certifi
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───distlib
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───distro
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───idna
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───msgpack
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───packaging
│   │       │   │   │   ├───licenses
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───pkg_resources
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───platformdirs
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───pygments
│   │       │   │   │   ├───filters
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   ├───formatters
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   ├───lexers
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   ├───styles
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───pyproject_hooks
│   │       │   │   │   ├───_in_process
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───requests
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───resolvelib
│   │       │   │   │   ├───resolvers
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───rich
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───tomli
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───tomli_w
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───truststore
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───urllib3
│   │       │   │   │   ├───contrib
│   │       │   │   │   │   ├───emscripten
│   │       │   │   │   │   │   └───__pycache__
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   ├───http2
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   ├───util
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   └───__pycache__
│   │       │   │   └───__pycache__
│   │       │   └───__pycache__
│   │       └───pip-26.1.2.dist-info
│   │           └───licenses
│   │               └───src
│   │                   └───pip
│   │                       └───_vendor
│   │                           ├───cachecontrol
│   │                           ├───certifi
│   │                           ├───distlib
│   │                           ├───distro
│   │                           ├───idna
│   │                           ├───msgpack
│   │                           ├───packaging
│   │                           ├───pkg_resources
│   │                           ├───platformdirs
│   │                           ├───pygments
│   │                           ├───pyproject_hooks
│   │                           ├───requests
│   │                           ├───resolvelib
│   │                           ├───rich
│   │                           ├───tomli
│   │                           ├───tomli_w
│   │                           ├───truststore
│   │                           └───urllib3
│   └───Scripts
├───assets
├───bin
├───builder
├───compiler
│   ├───include
│   │   └───mrr
│   │       ├───codegen
│   │       ├───driver
│   │       ├───ir
│   │       ├───lexer
│   │       ├───parser
│   │       └───sema
│   ├───pipeline
│   │   └───__pycache__
│   ├───src
│   │   ├───codegen
│   │   ├───driver
│   │   ├───ir
│   │   ├───lexer
│   │   ├───parser
│   │   └───sema
│   └───tests
├───debugger
│   ├───include
│   │   └───mrr
│   │       ├───core
│   │       └───dap
│   └───src
│       ├───bridge
│       ├───core
│       └───dap
├───docs
├───examples
├───interpreter
│   ├───bridges
│   ├───lsp
│   └───__pycache__
├───library
├───loader
├───optimizer
├───runtime
│   └───src
│       ├───crypto
│       ├───kernel
│       ├───memory
│       └───net
├───stdlib
│   ├───core
│   ├───exploit
│   ├───io
│   ├───mem
│   ├───memory
│   ├───network
│   └───ring1
└───vsix
    └───MRR.Language
        ├───assets
        ├───Grammars
        └───Snippets
```

# TAM DOSYA YAPISI VE AÇIKLAMALARI

```mrr
mrr/
├── README.md                    (Ana dokümantasyon - MRR dili rehberi)
├── KURULUM.md                   (Kurulum talimatları)
├── ogren.md                     (Öğrenme rehberi)
├── new_update.md                (Yeni güncellemeler)
│
├── install.ps1                  (PowerShell kurulum scripti)
├── kalinstall.sh                (Linux kurulum scripti)
├── mainİnstall.bat              (Windows kurulum batı)
├── ing.sh                        (Bash kurulum scripti)
├── ing.bat                       (Batch kurulum scripti)
│
├── .gitignore                   (Git ignore kuralları)
├── .gitattribute                (Git özellikleri)
│
├── scratch.mrr                  (MRR deneme dosyası)
├── scratch.py                   (Python deneme dosyası)
│
├── bin/                         (Yürütülebilir dosyalar)
│   ├── mrr.bat                  (MRR Windows çalıştırıcısı)
│   └── mrrinstall.bat           (MRR Windows kurulucu)
│
├── assets/                      (Proje varlıkları)
│   └── mrr.ico                  (MRR simgesi)
│
├── compiler/                    (MRR Derleyici - C++)
│   ├── CMakeLists.txt           (CMake yapılandırması)
│   ├── include/mrr/             (Başlık dosyaları)
│   │   ├── lexer/               (Sözcüksel çözümleyici)
│   │   ├── parser/              (Sözdizimsel çözümleyici)
│   │   ├── ir/                  (Ara Temsil)
│   │   ├── sema/                (Semantik analiz)
│   │   ├── codegen/             (Kod üretimi)
│   │   └── driver/              (CLI ve sürücü)
│   ├── src/                     (Kaynak dosyaları)
│   │   ├── lexer/               (Tokenizer)
│   │   ├── parser/              (AST inşaatçısı)
│   │   ├── ir/                  (IR oluşturma)
│   │   ├── sema/                (Tür kontrol ve sembol tablosu)
│   │   ├── codegen/             (x86_64 kod üretimi)
│   │   └── driver/              (Ana sürücü ve CLI)
│   ├── pipeline/                (Yapı hattı)
│   │   ├── build_pipeline.py    (Python yapı hattı)
│   │   ├── llvm_codegen.py      (LLVM kod üretimi)
│   │   ├── obfuscator.py        (Kod karıştırıcı)
│   │   └── signer.py            (Dijital imzalama)
│   └── tests/                   (Derleyici testleri)
│
├── debugger/                    (MRR Hata Ayıklayıcı)
│   ├── CMakeLists.txt           (CMake yapılandırması)
│   ├── dap_server.py            (Debug Adapter Protocol sunucusu)
│   ├── include/mrr/             (Başlık dosyaları)
│   │   ├── dap/                 (DAP protokolü)
│   │   └── core/                (Hata ayıklama çekirdeği)
│   └── src/                     (Kaynak dosyaları)
│       ├── main.cpp             (Ana hata ayıklayıcı giriş)
│       ├── dap/                 (DAP sunucusu uygulaması)
│       ├── core/                (Çekirdek hata ayıklama mantığı)
│       └── bridge/              (Kernel bağlantı köprüsü)
│
├── interpreter/                 (MRR Yorumlayıcı - Python)
│   ├── main.py                  (Ana giriş noktası)
│   ├── __init__.py              (Modül başlatma)
│   ├── mrr_lexer.py             (Token üreticisi)
│   ├── mrr_parser.py            (AST inşaatçısı)
│   ├── mrr_evaluator.py         (AST değerlendirici)
│   ├── mrr_builder.py           (Yapı yardımcısı)
│   ├── mrr_formatter.py         (Kod biçimlendiricisi)
│   ├── mrr_analyzer.py          (Statik analizci)
│   ├── mrr_autocorrect.py       (Otomatik düzeltme)
│   ├── mrr_ffi.py               (FFI bağlantısı)
│   ├── mrr_gui.py               (GUI arayüzü)
│   ├── mrr_repl.py              (Etkileşimli REPL)
│   ├── mrr_pkg.py               (Paket yönetimi)
│   ├── mrr_locale.py            (Lokalizasyon)
│   ├── lsp/                     (Language Server Protocol)
│   │   ├── __init__.py
│   │   ├── protocol.py          (LSP protokolü)
│   │   └── server.py            (LSP sunucusu)
│   └── bridges/                 (Harici sistem köprüleri)
│       ├── __init__.py
│       ├── mrr_memory_bridge.py (Bellek bağlantı köprüsü)
│       └── mrr_portswinger_bridge.py (Portswinger köprüsü)
│
├── runtime/                     (MRR Çalışma Zamanı)
│   ├── CMakeLists.txt           (CMake yapılandırması)
│   └── src/                     (Çalışma zamanı kaynakları)
│       ├── crypto/              (Şifreleme)
│       ├── kernel/              (Kernel API'si)
│       ├── memory/              (Bellek yönetimi)
│       └── net/                 (Ağ tabakası)
│
├── library/                     (Yerleşik Kütüphaneler)
│   ├── crypto.c/h               (Kriptografi)
│   ├── datetime.c/h             (Tarih/Saat)
│   ├── hex.c/h                  (Hex kodlama)
│   ├── json.c/h                 (JSON ayrıştırıcı)
│   ├── maths.c/h                (Matematik işlemleri)
│   ├── network.c/h              (Ağ işlemleri)
│   ├── os.c/h                   (İşletim sistemi API)
│   ├── random.c/h               (Rastgele sayı üretimi)
│   ├── requests.c/h             (HTTP istekleri)
│   ├── response.c/h             (HTTP yanıtları)
│   ├── sys.c/h                  (Sistem çağrıları)
│   ├── xor.c/h                  (XOR şifreleme)
│   ├── memory_reader.cpp/h      (Bellek okuyucu)
│   ├── portswinger.cpp/h        (Port yönlendirme)
│   ├── portswinger_raw.cpp/h    (Ham port yönlendirme)
│   ├── portswinger.dll          (Derlenmiş DLL)
│   ├── memory_reader.dll        (Derlenmiş DLL)
│   ├── generator.py             (Jeneratör)
│   └── ring-1.mrr               (Ring-1 kütüphanesi)
│
├── stdlib/                      (Standart Kütüphane)
│   ├── core/
│   │   └── core.mrr             (Çekirdek işlevler)
│   ├── io/
│   │   └── io.mrr               (Giriş/Çıkış)
│   ├── mem/
│   │   └── mem.mrr              (Bellek işlemleri)
│   ├── memory/
│   │   └── memory.mrr           (Gelişmiş bellek)
│   ├── network/
│   │   └── portswinger.mrr      (Ağ yardımcıları)
│   ├── exploit/
│   │   └── exploit.mrr          (Exploit kütüphanesi)
│   └── ring1/
│       └── ring1.mrr            (Ring-1 işlevler)
│
├── docs/                        (Belgeler)
│   └── language_spec.md         (Dil belirtimi)
│
├── examples/                    (Örnek MRR Programları)
│   ├── hello.mrr                (Merhaba Dünya)
│   ├── test_integer.mrr         (Tam sayı testi)
│   ├── test_ua.mrr              (User-Agent testi)
│   ├── ffi_test.mrr             (FFI testi)
│   ├── gui_test.mrr             (GUI testi)
│   ├── file_regex.mrr           (Dosya regex)
│   ├── hesap_makinesi.mrr       (Hesap makinesi)
│   ├── http_client.mrr          (HTTP istemcisi)
│   ├── network_test.mrr         (Ağ testi)
│   ├── memory_scan.mrr          (Bellek taraması)
│   ├── memory_scanner.mrr       (Bellek tarayıcı)
│   ├── shellcode_gen.mrr        (Shellcode üreticisi)
│   ├── kernel_driver.mrr        (Kernel sürücü)
│   ├── vuln_scanner.mrr         (Güvenlik açığı tarayıcısı)
│   ├── vuln_scanner_nmap.mrr    (Nmap tabanlı tarayıcı)
│   ├── scratch_mem.mrr          (Bellek çalışması)
│   └── input.txt                (Test girişi)
│
├── builder/                     (Yapılandırıcı Araçları)
│   ├── MrrBuilder.cs            (C# yapılandırıcı)
│   └── MrrBuilder.java          (Java yapılandırıcı)
│
├── optimizer/                   (Kod Optimize Edicisi)
│   └── MrrOptimizer.java        (Java optimizeri)
│
├── loader/                      (Modül Yükleyicisi)
│   ├── loader.py                (Python yükleyici)
│   └── config.yaml              (Yapılandırma dosyası)
│
└── vsix/                        (VS Code Eklentisi)
    └── MRR.Language/
        ├── package.json         (Eklenti manifest)
        ├── extension.js         (Eklenti giriş noktası)
        ├── language-configuration.json (Dil yapılandırması)
        ├── Grammars/            (Sözdizimi vurgulama)
        │   └── mrr.tmLanguage.json
        ├── Snippets/            (Kod parçacıkları)
        │   └── mrr.json
        ├── assets/              (Görsel varlıklar)
        │   └── mrr.ico
        └── mrr-language-support-0.1.0.vsix (Paketlenmiş eklenti)

```
