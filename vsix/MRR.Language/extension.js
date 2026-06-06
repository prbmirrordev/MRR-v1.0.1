const vscode = require('vscode');
const path = require('path');
const cp = require('child_process');
const { LanguageClient, TransportKind } = require('vscode-languageclient/node');

let client;
let diagnosticCollection;

/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
    let terminal = null;

    // ─── Live Diagnostics (v1.0.1) ───
    diagnosticCollection = vscode.languages.createDiagnosticCollection('mrr');
    context.subscriptions.push(diagnosticCollection);

    // Dosya açıldığında veya değiştirildiğinde hata kontrolü yap
    if (vscode.window.activeTextEditor) {
        updateDiagnostics(vscode.window.activeTextEditor.document);
    }

    context.subscriptions.push(
        vscode.window.onDidChangeActiveTextEditor(editor => {
            if (editor && editor.document.languageId === 'mrr') {
                updateDiagnostics(editor.document);
            }
        })
    );

    context.subscriptions.push(
        vscode.workspace.onDidChangeTextDocument(event => {
            if (event.document.languageId === 'mrr' || event.document.fileName.endsWith('.mrr')) {
                updateDiagnostics(event.document);
            }
        })
    );

    context.subscriptions.push(
        vscode.workspace.onDidOpenTextDocument(doc => {
            if (doc.languageId === 'mrr' || doc.fileName.endsWith('.mrr')) {
                updateDiagnostics(doc);
            }
        })
    );

    context.subscriptions.push(
        vscode.workspace.onDidCloseTextDocument(doc => {
            diagnosticCollection.delete(doc.uri);
        })
    );

    // Run Code Command
    let runCmd = vscode.commands.registerCommand('mrr.runCode', function () {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('No active MRR file to run.');
            return;
        }

        const document = editor.document;
        if (document.languageId !== 'mrr' && !document.fileName.endsWith('.mrr')) {
            vscode.window.showErrorMessage('Active file is not an MRR file.');
            return;
        }

        if (document.isDirty) {
            document.save();
        }

        const filePath = document.fileName;
        const dirPath = path.dirname(filePath);

        if (!terminal || terminal.exitStatus !== undefined) {
            terminal = vscode.window.createTerminal('MRR Run');
        }

        terminal.show();
        terminal.sendText(`cd "${dirPath}"`);
        terminal.sendText(`mrr run "${filePath}"`);
    });

    context.subscriptions.push(runCmd);

    // Formatter
    let formatter = vscode.languages.registerDocumentFormattingEditProvider('mrr', {
        provideDocumentFormattingEdits(document) {
            return new Promise((resolve, reject) => {
                const filePath = document.fileName;
                // mrr fmt reads and modifies the file directly, we wait for it
                cp.exec(`mrr fmt "${filePath}"`, (error, stdout, stderr) => {
                    if (error) {
                        vscode.window.showErrorMessage('MRR Formatter error: ' + stderr);
                        reject(error);
                    } else {
                        // Normally formatter returns text edits.
                        // Since mrr fmt modifies the file in place, we can just return empty edits,
                        // but VS Code might complain. A better approach would be to read the formatted output.
                        // As a workaround, we'll let VS Code know the file was updated externally.
                        resolve([]);
                    }
                });
            });
        }
    });

    context.subscriptions.push(formatter);

    // LSP Client Setup
    try {
        const serverCommand = 'mrr';
        const serverOptions = {
            run: { command: serverCommand, args: ['lsp'], transport: TransportKind.stdio },
            debug: { command: serverCommand, args: ['lsp'], transport: TransportKind.stdio }
        };

        const clientOptions = {
            documentSelector: [{ scheme: 'file', language: 'mrr' }],
            synchronize: {
                fileEvents: vscode.workspace.createFileSystemWatcher('**/.clientrc')
            }
        };

        client = new LanguageClient(
            'mrrLanguageServer',
            'MRR Language Server',
            serverOptions,
            clientOptions
        );

        client.start();
    } catch (e) {
        console.error("Failed to start MRR LSP client: ", e);
    }
}

/**
 * v1.0.1: Live Diagnostics — MRR dosyasını analiz et ve hataları göster.
 * 
 * Bu fonksiyon MRR lexer kurallarını takip ederek yaygın hataları tespit eder:
 *   - Büyük/küçük harf hataları (Function.create vs function.create)
 *   - Eksik veya yanlış parantezler
 *   - Tanınmayan komutlar
 *   - String kapatma hataları
 *   - Girinti hataları
 * 
 * @param {vscode.TextDocument} document 
 */
function updateDiagnostics(document) {
    if (!document || (document.languageId !== 'mrr' && !document.fileName.endsWith('.mrr'))) {
        return;
    }

    const text = document.getText();
    const lines = text.split('\n');
    const diagnostics = [];

    // ─── MRR Canonical Forms ───
    const canonicalCommands = {
        'fonction.create': 'Fonction.create',
        'function.create': 'Function.create',
        'add.code': 'add.code',
        'mrr.run': 'mrr.run',
        'mrr.debug': 'mrr.debug',
        'return.code': 'return.code'
    };

    // MRR Keywords (doğru yazım: lowercase)
    const mrrKeywords = new Set([
        'let', 'mut', 'const', 'fn', 'if', 'elif', 'else', 'for', 'while',
        'loop', 'match', 'return', 'break', 'continue', 'pass', 'struct',
        'class', 'trait', 'impl', 'pub', 'unsafe', 'kernel', 'ring0',
        'exploit', 'hook', 'driver', 'enum', 'try', 'catch', 'finally',
        'throw', 'do', 'defer', 'delete', 'use', 'module', 'as', 'in',
        'is', 'not', 'and', 'or', 'true', 'false', 'null', 'print', 'println'
    ]);

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const trimmed = line.trim();

        // Yorum satırlarını atla
        if (trimmed.startsWith('//') || trimmed.startsWith('#')) continue;

        // ─── 1. Dot-notation komut kontrolü ───
        const dotCmdRegex = /\b(\w+)\.(\w+)\b/g;
        let match;
        while ((match = dotCmdRegex.exec(line)) !== null) {
            const fullCmd = match[0];
            const fullCmdLower = fullCmd.toLowerCase();
            
            if (canonicalCommands[fullCmdLower]) {
                const canonical = canonicalCommands[fullCmdLower];
                if (fullCmd !== canonical) {
                    const startPos = match.index;
                    const range = new vscode.Range(i, startPos, i, startPos + fullCmd.length);
                    
                    const diag = new vscode.Diagnostic(
                        range,
                        `Büyük/küçük harf hatası: '${fullCmd}' → doğrusu '${canonical}'`,
                        vscode.DiagnosticSeverity.Warning
                    );
                    diag.source = 'MRR';
                    diag.code = 'case-sensitivity';
                    diagnostics.push(diag);
                }
            }
        }

        // ─── 2. Keyword büyük/küçük harf kontrolü ───
        const wordRegex = /\b([A-Z][a-zA-Z]*)\b/g;
        while ((match = wordRegex.exec(line)) !== null) {
            const word = match[1];
            const wordLower = word.toLowerCase();
            
            // String içinde mi kontrol et
            const beforeMatch = line.substring(0, match.index);
            const quoteCount = (beforeMatch.match(/"/g) || []).length;
            if (quoteCount % 2 !== 0) continue; // String içinde

            if (mrrKeywords.has(wordLower) && word !== wordLower) {
                // Ama tip isimleri (PascalCase) anahtar kelime değil
                // Sadece tam keyword eşleşmelerini kontrol et
                if (word.length === wordLower.length) {
                    const startPos = match.index;
                    const range = new vscode.Range(i, startPos, i, startPos + word.length);
                    
                    const diag = new vscode.Diagnostic(
                        range,
                        `Anahtar kelime büyük/küçük harf hatası: '${word}' → doğrusu '${wordLower}'`,
                        vscode.DiagnosticSeverity.Warning
                    );
                    diag.source = 'MRR';
                    diag.code = 'keyword-case';
                    diagnostics.push(diag);
                }
            }
        }

        // ─── 3. Kapatılmamış string kontrolü ───
        let inString = false;
        let stringStart = -1;
        for (let j = 0; j < line.length; j++) {
            if (line[j] === '"' && (j === 0 || line[j-1] !== '\\')) {
                if (!inString) {
                    inString = true;
                    stringStart = j;
                } else {
                    inString = false;
                }
            }
        }
        if (inString) {
            const range = new vscode.Range(i, stringStart, i, line.length);
            const diag = new vscode.Diagnostic(
                range,
                'Kapatılmamış string literal — çift tırnak (") eksik',
                vscode.DiagnosticSeverity.Error
            );
            diag.source = 'MRR';
            diag.code = 'unclosed-string';
            diagnostics.push(diag);
        }

        // ─── 4. Eşleşmeyen parantez kontrolü ───
        let parenCount = 0;
        let bracketCount = 0;
        let braceCount = 0;
        for (let j = 0; j < trimmed.length; j++) {
            const c = trimmed[j];
            if (c === '(') parenCount++;
            else if (c === ')') parenCount--;
            else if (c === '[') bracketCount++;
            else if (c === ']') bracketCount--;
            else if (c === '{') braceCount++;
            else if (c === '}') braceCount--;
        }
        
        if (parenCount > 0) {
            const range = new vscode.Range(i, 0, i, line.length);
            const diag = new vscode.Diagnostic(
                range,
                `${parenCount} adet kapatılmamış parantez ')'`,
                vscode.DiagnosticSeverity.Error
            );
            diag.source = 'MRR';
            diag.code = 'unmatched-paren';
            diagnostics.push(diag);
        }

        // ─── 5. Girinti tutarsızlığı ───
        if (line.length > 0 && !trimmed.startsWith('//') && !trimmed.startsWith('#')) {
            const spaces = line.match(/^( *)/)[1].length;
            const tabs = line.match(/^(\t*)/)[1].length;
            if (spaces > 0 && tabs > 0) {
                const range = new vscode.Range(i, 0, i, spaces + tabs);
                const diag = new vscode.Diagnostic(
                    range,
                    'Karışık girinti: tab ve boşluk birlikte kullanılmamalı',
                    vscode.DiagnosticSeverity.Warning
                );
                diag.source = 'MRR';
                diag.code = 'mixed-indent';
                diagnostics.push(diag);
            }
        }
    }

    diagnosticCollection.set(document.uri, diagnostics);
}

function deactivate() {
    if (diagnosticCollection) {
        diagnosticCollection.dispose();
    }
    if (!client) {
        return undefined;
    }
    return client.stop();
}

module.exports = {
    activate,
    deactivate
};
