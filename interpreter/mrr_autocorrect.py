from typing import List
from interpreter.mrr_lexer import LexerError


def _normalize_indentation(lines: List[str]) -> List[str]:
    normalized = []
    for line in lines:
        if line.strip() == "":
            normalized.append(line.replace("\t", "    "))
            continue
        leading = len(line) - len(line.lstrip(" \t"))
        prefix = line[:leading].replace("\t", "    ")
        normalized.append(prefix + line[leading:])
    return normalized


def _close_unterminated_quote(line: str, quote: str) -> str:
    if quote in line and line.rstrip("\n").count(quote) % 2 == 1:
        if line.endswith("\n"):
            return line.rstrip("\n") + quote + "\n"
        return line + quote
    if quote not in line:
        if line.endswith("\n"):
            return line.rstrip("\n") + quote + "\n"
        return line + quote
    return line


def _remove_unexpected_character(lines: List[str], error: LexerError) -> List[str]:
    line_idx = max(0, min(len(lines) - 1, error.location.line - 1))
    line = lines[line_idx]
    col = max(0, error.location.column - 1)
    if col >= len(line):
        if line.endswith("\n"):
            line = line[:-1] + " " + "\n"
        else:
            line = line + " "
    else:
        line = line[:col] + " " + line[col + 1:]
    lines[line_idx] = line
    return lines


def autocorrect_source(source: str, errors: List[LexerError]) -> str:
    if not errors:
        return source

    lines = source.splitlines(True)
    if not lines:
        lines = [""]

    sorted_errors = sorted(
        errors,
        key=lambda e: (e.location.line, e.location.column),
        reverse=True
    )

    corrected_any = False
    for error in sorted_errors:
        message = str(error)
        if "Tutarsız girinti" in message:
            lines = _normalize_indentation(lines)
            corrected_any = True
            continue
        if "Sonlandırılmamış string literali" in message:
            line_idx = max(0, min(len(lines) - 1, error.location.line - 1))
            lines[line_idx] = _close_unterminated_quote(lines[line_idx], '"')
            corrected_any = True
            continue
        if "Sonlandırılmamış karakter literali" in message:
            line_idx = max(0, min(len(lines) - 1, error.location.line - 1))
            lines[line_idx] = _close_unterminated_quote(lines[line_idx], "'")
            corrected_any = True
            continue
        if "Beklenmeyen karakter" in message or "Beklenmeyen lexer hatası" in message:
            lines = _remove_unexpected_character(lines, error)
            corrected_any = True
            continue

        # Fallback: remove a single character at reported location.
        lines = _remove_unexpected_character(lines, error)
        corrected_any = True

    return "".join(lines) if corrected_any else source
