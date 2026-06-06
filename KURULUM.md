# ⚙️ MRR Programlama Dili: Kurulum ve Sistem Entegrasyon Rehberi

MRR dili, doğrudan işletim sisteminin çekirdeğine (Ring 0 ve ring -1 "Kernel Mode") ve ağ donanımlarına erişecek şekilde tasarlandığından, Windows sisteminize tam olarak entegre olması gerekir. 

Aşağıdaki adımları izleyerek MRR Derleyicisi, Yorumlayıcısı ve Pentagram İkon Seti ile birlikte tam teşekküllü geliştirme ortamını kurabilirsiniz.

---

## 💻 Sistem Gereksinimleri
- **İşletim Sistemi:** Windows 10 veya Windows 11 (64-bit)
- **Komut Satırı:** PowerShell 5.1 veya daha güncel bir sürüm
- **Geliştirme Ortamı:** Visual Studio Code ve Cursor (Önerilen)

---

## 🚀 Adım Adım Kurulum

### Adım 1: Dosyaları Hazırlama
Projeyi bilgisayarınıza indirdikten veya klonladıktan sonra (örn: `Masaüstü/mrr`), klasörün içindeki tüm yapıya dokunmadan komut satırınızı (PowerShell) bu klasörde yönetici olarak açın.

### Adım 2: Otomatik Kurulum Betiği (install.ps1)
MRR'ın Windows Registry (Kayıt Defteri) ayarlarını ve PATH yollarını otomatik yapılandırması için PowerShell scriptini çalıştırın:

```powershell
.\install.ps1
```
*(Not: Eğer yetki hatası alırsanız, önce `Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope CurrentUser` komutunu çalıştırarak script yürütme izni verin.)*

**Bu betik arka planda şunları yapar:**
1. **Çevresel Değişkenler (User PATH):** `bin` klasörünü ortam değişkenlerinize ekler. Böylece herhangi bir terminal ekranından sadece `mrr` komutuyla derleyiciye ulaşabilirsiniz.
2. **Uzantı Çalıştırma (PATHEXT):** Windows'un `.MRR` dosyalarını bir `.exe` veya `.bat` gibi doğrudan çalıştırılabilir komut olarak tanımasını sağlar.
3. **Pentagram İkonu:** Registry'ye müdahale ederek sisteminizdeki tüm `.mrr` uzantılı dosyalara `assets\mrr.ico` yolundaki Pentagram ikonunu giydirir.
4. **Explorer Reset:** İkonların anında gözükmesi için `explorer.exe` (Windows Gezgini) servisini yeniden başlatır. Görev çubuğunuz bir anlığına gidip gelecektir, bu normaldir.

### Adım 3: VS Code Eklentisi (Sözdizimi Vurgulama)
MRR kodlarını yazarken renkli sözdizimi, hata ayıklama ve kod tamamlama özelliklerinden yararlanmak için kendi özel VS Code eklentimizi kurmalısınız.

Klasördeki `vsix/` dizini içerisinde eklenti kaynak kodları mevcuttur. Eklentiyi VS Code'a tanıtmak için klasörü kopyalayabilir veya VS Code içerisinde çalıştırabilirsiniz:

1. VS Code'u açın.
2. `vsix` dizinini veya MRR çalışma alanınızı açın.
3. MRR uzantılı dosyalarda artık özel Syntax Highlighting (Sözdizimi Renklendirmesi) aktif olacaktır.

---

## 🎯 Kurulumu Doğrulama

Kurulumun başarılı olup olmadığını test etmek için yeni bir komut satırı (CMD veya PowerShell) açın. (Değişkenlerin güncellenmesi için terminali kapatıp açmanız önemlidir).

1. Masaüstünde veya herhangi bir yerde `test.mrr` adında bir dosya oluşturun. İkonunun otomatik olarak **Pentagram**'a dönüştüğünü teyit edin.
2. İçine şu kodu yazıp kaydedin:
   ```mrr
   print("MRR Sistemi Aktif!")
   ```
3. Komut satırında dosyanın bulunduğu dizine gidin ve şu komutu çalıştırın:
   ```bash
   mrr test.mrr
   ```

Ekranda `MRR Sistemi Aktif!` yazısını görüyorsanız, sisteminiz Ring 0 operasyonlarına ve donanım manipülasyonlarına hazırdır!

---

> [!WARNING]
> **Güvenlik Uyarısı:** MRR dili ile yazılmış kodlar işletim sisteminin alt katmanlarına inebilir, I/O bağlantı noktalarına (Ports) erişebilir ve bellek okuma (Memory Read) işlemi yapabilir. Güvenmediğiniz `.mrr` dosyalarını çalıştırırken bir Sanal Makine (Virtual Machine) kullanmanız şiddetle tavsiye edilir.
