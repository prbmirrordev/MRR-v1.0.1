/*
 * ╔══════════════════════════════════════════════════════════════════╗
 * ║  MRR Builder — C# EXE Build Tool v1.0.1                       ║
 * ║                                                                  ║
 * ║  MRR projelerini native Windows .exe dosyasına dönüştürür.     ║
 * ║  .mbuild paketini self-extracting executable olarak paketler.  ║
 * ║                                                                  ║
 * ║  Kullanım:                                                      ║
 * ║    dotnet run MrrBuilder.cs <dosya.mrr> --format exe            ║
 * ║    csc MrrBuilder.cs && MrrBuilder.exe <dosya.mrr>              ║
 * ╚══════════════════════════════════════════════════════════════════╝
 */

using System;
using System.IO;
using System.IO.Compression;
using System.Text;
using System.Diagnostics;
using System.Runtime.InteropServices;

namespace MRR.Builder
{
    /// <summary>
    /// MRR C# Builder — Native .exe oluşturma aracı.
    /// 
    /// İki mod destekler:
    ///   1. Self-Extracting EXE: .mbuild paketini EXE'ye gömülü olarak paketler
    ///   2. PyInstaller Wrapper: Python PyInstaller üzerinden EXE oluşturur
    /// </summary>
    class MrrBuilder
    {
        private const string VERSION = "1.0.1";
        private const string CODENAME = "Resilient";

        static void Main(string[] args)
        {
            if (args.Length < 1)
            {
                PrintUsage();
                return;
            }

            string sourceFile = args[0];
            string outputFile = null;
            string format = "exe";

            for (int i = 1; i < args.Length; i++)
            {
                switch (args[i])
                {
                    case "--output":
                    case "-o":
                        if (i + 1 < args.Length) outputFile = args[++i];
                        break;
                    case "--format":
                    case "-f":
                        if (i + 1 < args.Length) format = args[++i];
                        break;
                    case "--help":
                    case "-h":
                        PrintUsage();
                        return;
                }
            }

            var builder = new MrrBuilder();

            try
            {
                if (format == "exe")
                    builder.BuildExe(sourceFile, outputFile);
                else if (format == "mb")
                {
                    Console.WriteLine("[BİLGİ] .mbuild build için Java MrrBuilder kullanın:");
                    Console.WriteLine($"  java MrrBuilder {sourceFile} --format mb");
                }
            }
            catch (Exception ex)
            {
                Console.ForegroundColor = ConsoleColor.Red;
                Console.WriteLine($"[HATA] Build başarısız: {ex.Message}");
                Console.ResetColor();
                Environment.Exit(1);
            }
        }

        // ─────────────────────────────────────────────────────
        // EXE Build
        // ─────────────────────────────────────────────────────

        /// <summary>
        /// MRR dosyasını native .exe'ye dönüştürür.
        /// Strateji: 
        ///   1. MRR kaynağını ve runtime'ı bir .mbuild'e paketle
        ///   2. Self-extracting launcher oluştur
        ///   3. .mbuild'i EXE'ye gömülü kaynak olarak ekle
        /// </summary>
        void BuildExe(string sourceFile, string outputFile)
        {
            string fullPath = Path.GetFullPath(sourceFile);

            if (!File.Exists(fullPath))
                throw new FileNotFoundException($"Dosya bulunamadı: {sourceFile}");

            string projectName = Path.GetFileNameWithoutExtension(fullPath);
            outputFile ??= projectName + ".exe";

            PrintBanner();
            Console.WriteLine($"  Kaynak:  {fullPath}");
            Console.WriteLine($"  Çıktı:   {outputFile}");
            Console.WriteLine($"  Format:  .exe (native Windows)");
            Console.WriteLine();

            // 1. Önce .mbuild oluştur
            Console.WriteLine("  [1/3] MRR paketi hazırlanıyor...");
            string mbuildPath = Path.Combine(
                Path.GetDirectoryName(fullPath)!,
                projectName + ".mbuild"
            );

            CreateMbuild(fullPath, mbuildPath, projectName);

            // 2. Self-extracting launcher oluştur
            Console.WriteLine("  [2/3] EXE launcher oluşturuluyor...");
            string launcherSource = GenerateLauncherSource(projectName, fullPath);

            // 3. Compile
            Console.WriteLine("  [3/3] Derleniyor...");
            
            // Python/PyInstaller yaklaşımı kullan
            string wrapperPy = Path.Combine(
                Path.GetDirectoryName(fullPath)!,
                $"_mrr_exe_{projectName}.py"
            );
            File.WriteAllText(wrapperPy, launcherSource);

            bool success = RunPyInstaller(wrapperPy, projectName, Path.GetDirectoryName(fullPath)!);

            // Temizlik
            if (File.Exists(mbuildPath)) File.Delete(mbuildPath);
            if (File.Exists(wrapperPy)) File.Delete(wrapperPy);

            if (success)
            {
                string exePath = Path.Combine(Path.GetDirectoryName(fullPath)!, outputFile);
                if (File.Exists(exePath))
                {
                    var info = new FileInfo(exePath);
                    Console.ForegroundColor = ConsoleColor.Green;
                    Console.WriteLine($"\n  ✓ EXE build başarılı!");
                    Console.ResetColor();
                    Console.WriteLine($"    Dosya: {exePath}");
                    Console.WriteLine($"    Boyut: {info.Length / (1024.0 * 1024.0):F1} MB");
                }
            }
            else
            {
                Console.ForegroundColor = ConsoleColor.Yellow;
                Console.WriteLine("  ⚠ PyInstaller bulunamadı veya hata oluştu.");
                Console.WriteLine("  Yüklemek için: pip install pyinstaller");
                Console.ResetColor();
            }
        }

        void CreateMbuild(string sourceFile, string outputPath, string projectName)
        {
            if (File.Exists(outputPath)) File.Delete(outputPath);

            using var zip = ZipFile.Open(outputPath, ZipArchiveMode.Create);

            // Manifest
            string manifest = $@"{{
  ""name"": ""{projectName}"",
  ""version"": ""{VERSION}"",
  ""entry"": ""source/{Path.GetFileName(sourceFile)}"",
  ""runtime"": ""mrr"",
  ""runtime_version"": ""{VERSION}"",
  ""build_date"": ""{DateTime.Now:O}"",
  ""builder"": ""MrrBuilder.cs"",
  ""platform"": ""{RuntimeInformation.OSDescription}"",
  ""format"": ""mbuild"",
  ""format_version"": ""1.0""
}}";
            var manifestEntry = zip.CreateEntry("manifest.json");
            using (var writer = new StreamWriter(manifestEntry.Open()))
                writer.Write(manifest);

            // Source
            var sourceEntry = zip.CreateEntry($"source/{Path.GetFileName(sourceFile)}");
            using (var writer = new StreamWriter(sourceEntry.Open()))
                writer.Write(File.ReadAllText(sourceFile));
        }

        string GenerateLauncherSource(string projectName, string sourceFile)
        {
            string sourceCode = File.ReadAllText(sourceFile)
                .Replace("\\", "\\\\")
                .Replace("\"\"\"", "\\\"\\\"\\\"");

            return $@"#!/usr/bin/env python3
""""""MRR EXE — Auto-generated by MrrBuilder.cs v{VERSION}""""""
import sys, os

# MRR root'u bul
mrr_root = os.environ.get('MRR_ROOT', '')
if mrr_root:
    sys.path.insert(0, mrr_root)

# Gömülü kaynak
SOURCE = """"""{sourceCode}""""""

try:
    from interpreter.mrr_lexer import Lexer
    from interpreter.mrr_parser import Parser
    from interpreter.mrr_evaluator import Evaluator
    from interpreter.mrr_ffi import FFIBridge, SandboxPolicy

    lexer = Lexer(SOURCE, '{Path.GetFileName(sourceFile)}')
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    ffi = FFIBridge(policy=SandboxPolicy())
    evaluator = Evaluator()
    evaluator.ffi_bridge = ffi
    evaluator.execute(ast)
except ImportError:
    print('MRR runtime bulunamadı. MRR_ROOT ortam değişkenini ayarlayın.')
    sys.exit(1)
";
        }

        bool RunPyInstaller(string scriptPath, string projectName, string outputDir)
        {
            try
            {
                string iconPath = FindIcon();
                var psi = new ProcessStartInfo
                {
                    FileName = "python",
                    Arguments = $"-m PyInstaller --onefile --name {projectName} " +
                               $"--distpath \"{outputDir}\" " +
                               $"--specpath \"{outputDir}\" " +
                               $"--workpath \"{Path.Combine(outputDir, "build")}\" " +
                               (iconPath != null ? $"--icon=\"{iconPath}\" " : "") +
                               $"--clean \"{scriptPath}\"",
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    UseShellExecute = false,
                    CreateNoWindow = true
                };

                using var process = Process.Start(psi);
                process?.WaitForExit(120000); // 2 dakika timeout

                // Temizlik
                string buildDir = Path.Combine(outputDir, "build");
                if (Directory.Exists(buildDir)) Directory.Delete(buildDir, true);
                string specFile = Path.Combine(outputDir, $"{projectName}.spec");
                if (File.Exists(specFile)) File.Delete(specFile);

                return process?.ExitCode == 0;
            }
            catch
            {
                return false;
            }
        }

        string? FindIcon()
        {
            // Proje kökünde assets/mrr.ico ara
            string? dir = Path.GetDirectoryName(
                System.Reflection.Assembly.GetExecutingAssembly().Location);
            
            for (int i = 0; i < 4 && dir != null; i++)
            {
                string iconPath = Path.Combine(dir, "assets", "mrr.ico");
                if (File.Exists(iconPath)) return iconPath;
                dir = Path.GetDirectoryName(dir);
            }
            return null;
        }

        // ─────────────────────────────────────────────────────
        // UI
        // ─────────────────────────────────────────────────────

        void PrintBanner()
        {
            Console.WriteLine();
            Console.WriteLine("╔══════════════════════════════════════════╗");
            Console.WriteLine($"║  MRR Builder v{VERSION} — C# EXE Mode     ║");
            Console.WriteLine("╚══════════════════════════════════════════╝");
            Console.WriteLine();
        }

        static void PrintUsage()
        {
            Console.WriteLine();
            Console.WriteLine("╔══════════════════════════════════════════════╗");
            Console.WriteLine($"║  MRR Builder v{VERSION} (C#)                  ║");
            Console.WriteLine("║  Native EXE Oluşturma Aracı                 ║");
            Console.WriteLine("╚══════════════════════════════════════════════╝");
            Console.WriteLine();
            Console.WriteLine("  Kullanım:");
            Console.WriteLine("    MrrBuilder.exe <dosya.mrr> [seçenekler]");
            Console.WriteLine();
            Console.WriteLine("  Seçenekler:");
            Console.WriteLine("    --output, -o <dosya>   Çıktı dosya adı");
            Console.WriteLine("    --help, -h             Bu yardım mesajı");
            Console.WriteLine();
            Console.WriteLine("  Örnekler:");
            Console.WriteLine("    MrrBuilder.exe proje.mrr");
            Console.WriteLine("    MrrBuilder.exe proje.mrr -o output.exe");
            Console.WriteLine();
        }
    }
}
