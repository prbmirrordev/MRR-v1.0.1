# MRR Programlama Dili: Sıfırdan İleri Seviyeye Öğrenim Rehberi

MRR (Memory, Registers, Rings), siber güvenlik, sistem programlama ve yüksek performans gerektiren işlemler için tasarlanmış, güçlü ve esnek bir programlama dilidir. Rust'ın güvenliğini, Ruby'nin kolay okunabilirliğini, C#'ın nesne yönelimli yapısını ve C++'ın donanım seviyesi gücünü bir araya getirir.

Bu rehber, daha önce hiç programlama yapmamış biri bile anlayabilecek şekilde MRR dilini sıfırdan öğretmek için hazırlanmıştır.

---

## 1. Temel Kavramlar ve İlk Adımlar

### 1.1 "Merhaba Dünya!" (Print İşlemi)
Her dilin klasiği olan ekrana yazı yazdırma işlemi MRR'da çok basittir:

```mrr
print("Merhaba, MRR dünyası!")
println("Bu yazıdan sonra alt satıra geçilir.")
```
*   `print` : Verilen değeri ekrana yazar ama alt satıra geçmez.
*   `println` : Verilen değeri ekrana yazar ve ardından bir alt satıra (yeni satıra) geçer.

### 1.2 Yorum Satırları
Kodunuzun içine, bilgisayar tarafından okunmayan ve sadece insanların anlaması için notlar bırakabilirsiniz.

```mrr
// Bu tek satırlık bir yorumdur. Sadece bu satır koddan sayılmaz.
/// Bu ise dokümantasyon (açıklama) yorumudur.
```

---

## 2. Değişkenler ve Veri Tipleri

Değişkenler, verileri hafızada tuttuğumuz kutucuklardır. MRR'da veri tipleri güçlü bir şekilde kontrol edilir.

### 2.1 Değişken Tanımlama (`let` ve `mut`)
MRR'da varsayılan olarak bir değişken oluşturduğunuzda, değeri sonradan **değiştirilemez**. Bu, kodun güvenliğini artırır.

```mrr
// Sabit (değiştirilemez) değişken tanımlama:
let isim = "Ahmet"
let yas = 25

// isim = "Mehmet" // HATA! 'let' ile tanımlandığı için değiştirilemez.

// Değiştirilebilir (mutable) değişken tanımlama:
mut sayac = 0
sayac = sayac + 1 // BAŞARILI! 'mut' (mutable) olduğu için değişebilir.

// Alternatif atama sözdizimi (Hızlı atama):
@sonuc = 100 // Otomatik olarak mutable (değiştirilebilir) bir 'sonuc' değişkeni oluşturur.
```

*   `let` : Değeri sonradan değiştirilemeyecek değişkenler (sabitler) oluşturur.
*   `mut` : Değeri kodun ilerleyen kısımlarında değiştirilebilecek değişkenler oluşturur.
*   `@degisken_adi` : Hızlıca değiştirilebilir değişken tanımlamanın kısa yoludur.

### 2.2 Veri Tipleri
MRR, donanıma yakın bir dil olduğu için çok çeşitli sayı tiplerine sahiptir.

```mrr
let tam_sayi: i32 = 42       // i32: 32-bit işaretli tam sayı (standart tam sayı)
let ondalikli: f64 = 3.14    // f64: 64-bit ondalıklı sayı
let metin: str = "MRR Dili"  // str: Metin (String) tipi
let dogru_mu: bool = true    // bool: Mantıksal (true veya false)
let karakter: char = 'A'     // char: Tek bir karakter
let byte_dizisi: bytes = b"merhaba" // bytes: Bellek işlemleri için ham veriler
```

---

## 3. Operatörler (İşlemciler)

### 3.1 Matematiksel Operatörler
```mrr
let a = 10
let b = 3

println(a + b)  // Toplama: 13
println(a - b)  // Çıkarma: 7
println(a * b)  // Çarpma: 30
println(a / b)  // Bölme: 3.333...
println(a % b)  // Mod (Kalan): 1
println(a ** b) // Üs alma (10'un 3. kuvveti): 1000
```

### 3.2 Karşılaştırma Operatörleri
Bunlar her zaman `true` (doğru) veya `false` (yanlış) sonucu verir.
```mrr
a == b  // Eşit mi? (false)
a != b  // Eşit değil mi? (true)
a > b   // Büyük mü? (true)
a < b   // Küçük mü? (false)
a >= b  // Büyük veya eşit mi? (true)
a <= b  // Küçük veya eşit mi? (false)
```

### 3.3 Hızlı Atama Operatörleri
```mrr
mut x = 5
x += 2  // x = x + 2 ile aynıdır. Sonuç: 7
x *= 3  // x = x * 3 ile aynıdır. Sonuç: 21
```

---

## 4. Kontrol Yapıları (Karar Verme ve Döngüler)

Kodun akışını yönlendirmek için kullanılırlar. MRR, blokları belirtmek için satır sonlarına `:` (iki nokta) koymanızı ve alt satırları içeriye (indent) doğru girintili yazmanızı ister.

### 4.1 İf - Elif - Otherwise (Eğer - Değilse Eğer - Değilse)
```mrr
let puan = 75

if puan >= 90:
    println("Harika, AA aldın!")
elif puan >= 70:
    println("Güzel, BB aldın.")
otherwise:
    println("Maalesef kaldın.")
```
*   `if` : Eğer koşul doğruysa (true) altındaki bloğu çalıştırır.
*   `elif` : Önceki `if` yanlışsa, bu yeni koşula bakar. (Else-if kısaltması)
*   `otherwise` : Hiçbir koşul sağlanmadıysa çalışacak "varsayılan" bloktur. (Diğer dillerdeki `else` gibidir).

### 4.2 Döngüler (Sürekli Tekrarlayan İşlemler)

**For Döngüsü:** Belirli bir sayı veya liste üzerinde gezinmek için.
```mrr
// 1'den 5'e kadar (5 dahil değil) sayar
for i in 1..5:
    println("Sayı: #{i}")

// Liste içinde gezinme
let renkler = ["Kırmızı", "Mavi", "Yeşil"]
for renk in renkler:
    println("Renk: #{renk}")
```

**While Döngüsü (MRR Tarzı: `return.code`)**
MRR'da geleneksel `while` döngüsü yerine güvenlik odaklı `return.code` mantığı kullanılır. Bir blok tanımlanır ve en sonunda dönüp dönmeyeceğine karar verilir.

```mrr
mut sayac = 0

// "do:" bloğu başlatır. İçindeki kod çalışır.
do:
    println("Sayacın şu anki değeri: #{sayac}")
    sayac += 1
    
    // "return.code koşul" : Eğer koşul doğruysa (true) bloğun başına geri dön!
    return.code sayac < 3
```

**Loop Döngüsü:** Sonsuz döngüdür, içeriden `break` ile kırılana kadar döner.
```mrr
mut i = 0
loop:
    i += 1
    if i == 5:
        break // Döngüyü tamamen bitir.
    if i == 3:
        continue // Bu adımı atla, başa dön (3'ü ekrana yazmaz).
    println(i)
```

---

## 5. Veri Yapıları (Koleksiyonlar)

Birden fazla veriyi tek bir değişkende tutmamızı sağlarlar.

### 5.1 Listeler (Diziler)
Sıralı veri gruplarıdır. `[]` işaretleri ile tanımlanır.

```mrr
let sayilar = [10, 20, 30, 40]
println(sayilar[0]) // 10 (Bilgisayarlar saymaya 0'dan başlar!)

mut meyveler = ["Elma", "Armut"]
append(meyveler, "Muz") // Listeye yeni eleman ekler
```

### 5.2 Sözlükler (Dictionaries)
Verileri anahtar-değer (key-value) ikilileri şeklinde eşleştirerek tutar. `{}` işaretleri ile tanımlanır.

```mrr
let kullanici = {
    "isim": "Hasan",
    "yas": 30,
    "yetki": "Admin"
}

println(kullanici["isim"]) // Ekrana "Hasan" yazar.
```

---

## 6. Fonksiyonlar (Özelleştirilmiş Kod Blokları)

Kodunuzu modüler, tekrar kullanılabilir parçalara ayırmak için fonksiyonlar oluşturursunuz. MRR'da iki farklı fonksiyon tanımlama şekli vardır:

### 6.1 `Function.create` (Sistem Seviyesi/Detaylı Tanımlama)
Daha yetenekli ve sistemsel işlemler için kullanılır.

```mrr
// topla adında, a ve b adında iki parametre alan bir fonksiyon oluşturuyoruz.
Function.create "topla" (a, b):
    return a + b

let sonuc = topla(5, 10) // 15
```
*   `Function.create "isim" (parametreler):` : Yeni bir fonksiyon oluşturur.
*   `return` : Fonksiyonun ürettiği sonucu dışarıya, çağrıldığı yere geri gönderir.

### 6.2 `fn` (Kısa ve Standart Tanımlama)
Modern dillere (Rust, Python) benzeyen daha pratik tanımlama yöntemidir. Tipleri de belirtebilirsiniz.

```mrr
// a ve b parametreleri i32 (tam sayı) olmalı, sonuç da i32 dönmeli.
fn carp(a: i32, b: i32) -> i32:
    return a * b
```

---

## 7. Nesne Yönelimli ve Gelişmiş Yapılar

### 7.1 Yapılar (Structs)
Kendi özel veri tipinizi oluşturmanızı sağlar. Birbiriyle ilişkili verileri gruplar.

```mrr
// Bir 'Oyuncu' yapısı tanımlıyoruz.
struct Oyuncu:
    pub isim: str    // pub: Dışarıdan erişilebilir (public)
    pub can: i32
    priv seviye: i32 // priv: Sadece içeriden erişilebilir (private)

// Struct'ı kullanma (yeni bir oyuncu oluşturma)
let kahraman = Oyuncu(isim: "Ertuğrul", can: 100, seviye: 1)
```

### 7.2 Enumlar (Seçenekler)
Belirli ve sabit seçeneklerden birini ifade eden özel bir veri tipidir.

```mrr
enum Durum:
    BEKLEMEDE
    CALISIYOR
    DURDU

let anlik_durum = Durum::CALISIYOR
```

### 7.3 Try - Catch - Finally (Hata Yakalama)
Program çalışırken beklenmedik bir hata (örneğin dosya bulunamaması) oluştuğunda programın çökmesini engellemek için kullanılır.

```mrr
try:
    // Hata oluşabilecek, riskli kodu buraya yazın
    let dosya = readfile("olmayan_dosya.txt")
catch hata_mesaji:
    // Eğer try bloğunda hata olursa, program çökmez, burası çalışır
    println("Bir sorun oluştu: #{hata_mesaji}")
finally:
    // Hata olsa da olmasa da en son mutlaka çalışacak kod (örneğin açık dosyayı kapatmak)
    println("İşlem denemesi bitti.")
```

---

## 8. Siber Güvenlik ve Sistem Seviyesi Özellikler

MRR'ın diğer dillerden ayrıldığı en önemli kısımdır.

### 8.1 `add.code` (Dış Kütüphane / Modül Ekleme)
MRR, diğer dillerin (Python, C++) kütüphanelerini doğrudan projenize bağlayabilir.

```mrr
// Python'un güçlü kütüphanelerini MRR'da kullanın
add.code "os"
add.code "requests"
```

### 8.2 `exploit` ve `hook` Blokları
Siber güvenlik testleri, zafiyet analizi ve sistem çağrılarını yakalamak için tasarlanmış özel yapılardır.

```mrr
// Bellek analizi veya zafiyet testi için izole bir blok
exploit "MemoryLeakTest":
    // Burada yapılan işlemler ana sistemi bozmaz, sanal alanda (sandbox) test edilir.
    // ...
```

### 8.3 `unsafe` Bloğu
MRR normalde bellek güvenliğini korur ve tehlikeli işlemlere izin vermez. Ancak donanıma çok yakın seviyede, belleğe doğrudan müdahale etmeniz gerekiyorsa, sorumluluğu alarak `unsafe` bloğunu kullanabilirsiniz. C++ gücündedir.

```mrr
unsafe:
    // DİKKAT: Burada yapılan işlemler sistemi çökertebilir.
    // Doğrudan bellek adreslerine (pointer) erişim burada serbesttir.
```

---

## 9. Faydalı Yerleşik (Built-in) Fonksiyonlar

MRR, geliştirme sürecinizi hızlandıracak birçok hazır fonksiyonla gelir. Herhangi bir kütüphane eklemeden direkt kullanabilirsiniz.

### Metin (String) İşlemleri
*   `upper(metin)` : Metni BÜYÜK HARFE çevirir. (`upper("mrr")` -> `"MRR"`)
*   `lower(metin)` : Metni küçük harfe çevirir.
*   `replace(metin, eski, yeni)` : Metin içindeki kelimeleri değiştirir.
*   `split(metin, ayrac)` : Metni verilen ayıraca göre böler ve bir liste yapar. (`split("A,B,C", ",")` -> `["A", "B", "C"]`)
*   `join(ayrac, liste)` : Listeyi birleştirip tek bir metin yapar.
*   `contains(metin, aranacak)` : Metin içinde aranacak kelime var mı? (true/false döner)

### Liste İşlemleri
*   `len(liste)` : Listenin kaç elemanlı olduğunu söyler.
*   `append(liste, eleman)` : Listenin sonuna yeni eleman ekler.
*   `sort(liste)` : Listeyi küçükten büyüğe (veya alfabetik) sıralar.
*   `reverse(liste)` : Listeyi tersine çevirir.

### Sistem ve Dosya İşlemleri
*   `readfile("dosya.txt")` : Dosyanın içindeki yazıları okur.
*   `writefile("dosya.txt", "icerik")` : Dosyaya yeni yazı yazar.
*   `sleep(saniye)` : Programı belirtilen saniye kadar duraklatır (bekletir).
*   `random_int(min, max)` : Belirtilen aralıkta rastgele bir sayı üretir.
*   `time()` : O anki zamanın (bilgisayar saati) damgasını verir.

---

> [!TIP]
> **Kendi Terminalini Kullan!**
> Komut satırına (CMD veya PowerShell) sadece `mrr` yazarak MRR'ın kendi interaktif terminalini açabilir, kodları satır satır yazıp anında sonuçlarını görebilirsiniz. Deneme yapmak için harikadır!
