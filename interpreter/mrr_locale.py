import os
from typing import Dict

LANG = os.getenv("MRR_LANG", "").strip().lower()
if LANG in ("en", "english"):
    LANG = "en"
else:
    LANG = "tr"

MESSAGES: Dict[str, Dict[str, str]] = {
    "auto_correct_prompt": {
        "tr": "Token hatası oluştu. Hataları otomatik düzeltmek ister misiniz? (E/H): ",
        "en": "A token error occurred. Attempt auto-correction? (Y/N): "
    },
    "auto_correcting": {
        "tr": "Hatalar otomatik olarak düzeltiliyor...",
        "en": "Auto-correcting errors..."
    },
    "auto_corrected": {
        "tr": "Hata düzeltildi, kod tekrar işleniyor.",
        "en": "Errors corrected, reprocessing code."
    },
    "auto_correct_failed": {
        "tr": "Otomatik düzeltme yetersiz kaldı, lütfen kodu elle kontrol edin.",
        "en": "Auto-correction could not resolve all errors. Please check the source manually."
    },
    "error_header_lexer": {
        "tr": "LEXER HATALARI:",
        "en": "LEXER ERRORS:"
    },
    "error_header_parser": {
        "tr": "PARSER HATALARI:",
        "en": "PARSER ERRORS:"
    },
    "lexer_error": {
        "tr": "Lexer hatası:",
        "en": "Lexer error:"
    },
    "parser_error": {
        "tr": "Parser hatası:",
        "en": "Parser error:"
    },
    "unexpected_error": {
        "tr": "Beklenmeyen hata:",
        "en": "Unexpected error:"
    }
}

YES_CHOICES = {
    "tr": ("e", "evet", "y", "yes"),
    "en": ("y", "yes")
}

NO_CHOICES = {
    "tr": ("h", "hayır", "hayir", "n", "no"),
    "en": ("n", "no")
}


def translate(key: str) -> str:
    return MESSAGES.get(key, {}).get(LANG, key)


def is_yes(answer: str) -> bool:
    return answer.strip().lower() in YES_CHOICES[LANG]


def is_no(answer: str) -> bool:
    return answer.strip().lower() in NO_CHOICES[LANG]


def ask_yes_no(key: str) -> bool:
    prompt = translate(key)
    while True:
        answer = input(prompt)
        if is_yes(answer):
            return True
        if is_no(answer):
            return False
        print(translate("unexpected_error"), answer)
