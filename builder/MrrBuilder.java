/*
 * ╔══════════════════════════════════════════════════════════════════╗
 * ║  MRR Builder — Java Build Tool v1.0.1                          ║
 * ║                                                                  ║
 * ║  MRR projelerini .mbuild formatında paketler.                  ║
 * ║  .mbuild = ZIP tabanlı self-contained çalıştırılabilir paket.  ║
 * ║                                                                  ║
 * ║  Kullanım:                                                      ║
 * ║    javac MrrBuilder.java && java MrrBuilder <dosya.mrr>        ║
 * ║                                                                  ║
 * ║  .mbuild içeriği:                                               ║
 * ║    manifest.json  — Paket metadata                              ║
 * ║    source/        — MRR kaynak dosyaları                        ║
 * ║    runtime/       — MRR interpreter                             ║
 * ║    entry.py       — Başlatıcı script                            ║
 * ╚══════════════════════════════════════════════════════════════════╝
 */

import java.io.*;
import java.nio.file.*;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.*;
import java.util.zip.*;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

public class MrrBuilder {

    private static final String VERSION = "1.0.1";
    private static final String CODENAME = "Resilient";

    // ─────────────────────────────────────────────────────
    // Ana Giriş Noktası
    // ─────────────────────────────────────────────────────

    public static void main(String[] args) {
        if (args.length < 1) {
            printUsage();
            System.exit(1);
        }

        String sourceFile = args[0];
        String format = "mb"; // Varsayılan: .mbuild
        String outputFile = null;

        // Argümanları ayrıştır
        for (int i = 1; i < args.length; i++) {
            switch (args[i]) {
                case "--format":
                case "-f":
                    if (i + 1 < args.length) {
                        format = args[++i];
                    }
                    break;
                case "--output":
                case "-o":
                    if (i + 1 < args.length) {
                        outputFile = args[++i];
                    }
                    break;
                case "--help":
                case "-h":
                    printUsage();
                    System.exit(0);
                    break;
            }
        }

        MrrBuilder builder = new MrrBuilder();
        
        try {
            if ("mb".equals(format)) {
                builder.buildMbuild(sourceFile, outputFile);
            } else if ("exe".equals(format)) {
                System.out.println("[BİLGİ] EXE build için C# MrrBuilder kullanın:");
                System.out.println("  dotnet run MrrBuilder.cs " + sourceFile + " --format exe");
                System.out.println("\n  Veya Python builder: mrr build " + sourceFile + " --format exe");
            } else {
                System.err.println("[HATA] Bilinmeyen format: " + format);
                System.exit(1);
            }
        } catch (Exception e) {
            System.err.println("[HATA] Build başarısız: " + e.getMessage());
            System.exit(1);
        }
    }

    // ─────────────────────────────────────────────────────
    // .mbuild Build
    // ─────────────────────────────────────────────────────

    public void buildMbuild(String sourceFile, String outputFile) throws IOException {
        Path sourcePath = Paths.get(sourceFile).toAbsolutePath();
        
        if (!Files.exists(sourcePath)) {
            throw new FileNotFoundException("Dosya bulunamadı: " + sourceFile);
        }

        String projectName = sourcePath.getFileName().toString().replace(".mrr", "");
        if (outputFile == null) {
            outputFile = projectName + ".mbuild";
        }

        printBanner("mb");
        System.out.println("  Kaynak:  " + sourcePath);
        System.out.println("  Çıktı:   " + outputFile);
        System.out.println("  Format:  .mbuild (self-contained)");
        System.out.println();

        Path outputPath = sourcePath.getParent().resolve(outputFile);
        Path tempDir = Files.createTempDirectory("mrr_build_");

        try {
            // 1. Manifest oluştur
            System.out.println("  [1/4] Manifest oluşturuluyor...");
            createManifest(tempDir, projectName, sourcePath);

            // 2. Kaynak dosyaları kopyala
            System.out.println("  [2/4] Kaynak dosyalar kopyalanıyor...");
            Path sourceDir = tempDir.resolve("source");
            Files.createDirectories(sourceDir);
            Files.copy(sourcePath, sourceDir.resolve(sourcePath.getFileName()));
            
            // Aynı dizindeki diğer .mrr dosyalarını da ekle
            try (DirectoryStream<Path> stream = Files.newDirectoryStream(sourcePath.getParent(), "*.mrr")) {
                for (Path mrrFile : stream) {
                    if (!mrrFile.equals(sourcePath)) {
                        Files.copy(mrrFile, sourceDir.resolve(mrrFile.getFileName()));
                    }
                }
            }

            // 3. Runtime kopyala
            System.out.println("  [3/4] MRR Runtime paketleniyor...");
            Path runtimeDir = tempDir.resolve("runtime");
            Files.createDirectories(runtimeDir);
            
            // MRR root dizinini bul (builder'ın bulunduğu dizinin üst dizini)
            Path mrrRoot = findMrrRoot(sourcePath);
            if (mrrRoot != null) {
                Path interpDir = mrrRoot.resolve("interpreter");
                if (Files.exists(interpDir)) {
                    copyDirectory(interpDir, runtimeDir.resolve("interpreter"));
                }
                Path stdlibDir = mrrRoot.resolve("stdlib");
                if (Files.exists(stdlibDir)) {
                    copyDirectory(stdlibDir, runtimeDir.resolve("stdlib"));
                }
            }

            // Entry point oluştur
            createEntryPoint(tempDir, sourcePath.getFileName().toString());

            // 4. ZIP olarak paketle
            System.out.println("  [4/4] .mbuild arşivi oluşturuluyor...");
            createZipArchive(tempDir, outputPath);

            long sizeKb = Files.size(outputPath) / 1024;
            System.out.println("\n  \033[32m✓ Build başarılı!\033[0m");
            System.out.println("    Dosya: " + outputPath);
            System.out.println("    Boyut: " + sizeKb + " KB");

        } finally {
            // Geçici dizini temizle
            deleteDirectory(tempDir);
        }
    }

    // ─────────────────────────────────────────────────────
    // Yardımcı Metodlar
    // ─────────────────────────────────────────────────────

    private void createManifest(Path dir, String projectName, Path sourcePath) throws IOException {
        String manifest = String.format(
            "{\n" +
            "  \"name\": \"%s\",\n" +
            "  \"version\": \"%s\",\n" +
            "  \"entry\": \"source/%s\",\n" +
            "  \"runtime\": \"mrr\",\n" +
            "  \"runtime_version\": \"%s\",\n" +
            "  \"build_date\": \"%s\",\n" +
            "  \"builder\": \"MrrBuilder.java\",\n" +
            "  \"platform\": \"%s\",\n" +
            "  \"format\": \"mbuild\",\n" +
            "  \"format_version\": \"1.0\"\n" +
            "}",
            projectName,
            VERSION,
            sourcePath.getFileName(),
            VERSION,
            LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME),
            System.getProperty("os.name")
        );
        Files.writeString(dir.resolve("manifest.json"), manifest);
    }

    private void createEntryPoint(Path dir, String sourceFileName) throws IOException {
        String entry = String.format(
            "#!/usr/bin/env python3\n" +
            "\"\"\"MRR .mbuild Entry Point — Auto-generated by MrrBuilder.java v%s\"\"\"\n" +
            "import sys, os\n" +
            "runtime_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'runtime')\n" +
            "sys.path.insert(0, runtime_dir)\n" +
            "source_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'source', '%s')\n" +
            "from interpreter.mrr_lexer import Lexer\n" +
            "from interpreter.mrr_parser import Parser\n" +
            "from interpreter.mrr_evaluator import Evaluator\n" +
            "from interpreter.mrr_ffi import FFIBridge, SandboxPolicy\n" +
            "with open(source_file, 'r', encoding='utf-8') as f:\n" +
            "    code = f.read()\n" +
            "lexer = Lexer(code, source_file)\n" +
            "tokens = lexer.tokenize()\n" +
            "parser = Parser(tokens)\n" +
            "ast = parser.parse()\n" +
            "ffi = FFIBridge(policy=SandboxPolicy())\n" +
            "evaluator = Evaluator()\n" +
            "evaluator.ffi_bridge = ffi\n" +
            "evaluator.execute(ast)\n",
            VERSION, sourceFileName
        );
        Files.writeString(dir.resolve("entry.py"), entry);
    }

    private Path findMrrRoot(Path fromPath) {
        Path current = fromPath.getParent();
        for (int i = 0; i < 5; i++) {
            if (current == null) break;
            if (Files.exists(current.resolve("interpreter")) &&
                Files.exists(current.resolve("stdlib"))) {
                return current;
            }
            current = current.getParent();
        }
        return null;
    }

    private void copyDirectory(Path source, Path target) throws IOException {
        Files.walkFileTree(source, new SimpleFileVisitor<Path>() {
            @Override
            public FileVisitResult preVisitDirectory(Path dir, BasicFileAttributes attrs) throws IOException {
                String dirName = dir.getFileName().toString();
                if (dirName.equals("__pycache__") || dirName.equals(".git")) {
                    return FileVisitResult.SKIP_SUBTREE;
                }
                Files.createDirectories(target.resolve(source.relativize(dir)));
                return FileVisitResult.CONTINUE;
            }

            @Override
            public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) throws IOException {
                String fileName = file.getFileName().toString();
                if (fileName.endsWith(".pyc") || fileName.endsWith(".pyo")) {
                    return FileVisitResult.CONTINUE;
                }
                Files.copy(file, target.resolve(source.relativize(file)),
                           StandardCopyOption.REPLACE_EXISTING);
                return FileVisitResult.CONTINUE;
            }
        });
    }

    private void createZipArchive(Path sourceDir, Path outputFile) throws IOException {
        try (ZipOutputStream zos = new ZipOutputStream(
                new BufferedOutputStream(new FileOutputStream(outputFile.toFile())))) {
            zos.setLevel(Deflater.BEST_COMPRESSION);
            
            Files.walkFileTree(sourceDir, new SimpleFileVisitor<Path>() {
                @Override
                public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) throws IOException {
                    String entryName = sourceDir.relativize(file).toString().replace("\\", "/");
                    zos.putNextEntry(new ZipEntry(entryName));
                    Files.copy(file, zos);
                    zos.closeEntry();
                    return FileVisitResult.CONTINUE;
                }
            });
        }
    }

    private void deleteDirectory(Path dir) {
        try {
            Files.walkFileTree(dir, new SimpleFileVisitor<Path>() {
                @Override
                public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) throws IOException {
                    Files.delete(file);
                    return FileVisitResult.CONTINUE;
                }

                @Override
                public FileVisitResult postVisitDirectory(Path d, IOException exc) throws IOException {
                    Files.delete(d);
                    return FileVisitResult.CONTINUE;
                }
            });
        } catch (IOException ignored) {}
    }

    // ─────────────────────────────────────────────────────
    // UI
    // ─────────────────────────────────────────────────────

    private void printBanner(String mode) {
        String modeStr = "mb".equals(mode) ? ".mbuild Mode" : "EXE Mode    ";
        System.out.println();
        System.out.println("╔══════════════════════════════════════════╗");
        System.out.println("║  MRR Builder v" + VERSION + " — " + modeStr + "   ║");
        System.out.println("╚══════════════════════════════════════════╝");
        System.out.println();
    }

    private static void printUsage() {
        System.out.println();
        System.out.println("╔══════════════════════════════════════════════╗");
        System.out.println("║  MRR Builder v" + VERSION + " (Java)                 ║");
        System.out.println("║  .mbuild Paket Oluşturma Aracı              ║");
        System.out.println("╚══════════════════════════════════════════════╝");
        System.out.println();
        System.out.println("  Kullanım:");
        System.out.println("    java MrrBuilder <dosya.mrr> [seçenekler]");
        System.out.println();
        System.out.println("  Seçenekler:");
        System.out.println("    --format, -f <mb|exe>   Build formatı (varsayılan: mb)");
        System.out.println("    --output, -o <dosya>    Çıktı dosya adı");
        System.out.println("    --help, -h              Bu yardım mesajı");
        System.out.println();
        System.out.println("  Örnekler:");
        System.out.println("    java MrrBuilder proje.mrr");
        System.out.println("    java MrrBuilder proje.mrr --format mb -o output.mbuild");
        System.out.println();
    }
}
