import re
from datetime import datetime
from typing import List, Optional


class TempMailUtils:
    OTP_PATTERNS = [
        r"code[:\s]*([A-Z0-9]{4,8})",
        r"verification[:\s]*([A-Z0-9]{4,8})",
        r"OTP[:\s]*([A-Z0-9]{4,8})",
        r"pin[:\s]*(\d{4,8})",
        r"\b\d{4,8}\b",
    ]

    @staticmethod
    def extract_otp(text: str) -> Optional[str]:
        if not text:
            return None

        text_lower = text.lower()

        for pattern in TempMailUtils.OTP_PATTERNS:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                otp = matches[0] if isinstance(matches[0], str) else matches[0][0]
                return otp.strip()

        return None

    @staticmethod
    def extract_all_codes(text: str) -> List[str]:
        if not text:
            return []

        codes = []
        for pattern in TempMailUtils.OTP_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            codes.extend(matches)

        seen = set()
        unique_codes = []
        for code in codes:
            code_str = str(code).strip()
            if code_str not in seen and len(code_str) >= 4:
                seen.add(code_str)
                unique_codes.append(code_str)

        return unique_codes

    @staticmethod
    def format_datetime(iso_datetime: str) -> str:
        try:
            dt = datetime.fromisoformat(iso_datetime.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return iso_datetime

    @staticmethod
    def clean_html(html: str) -> str:
        clean_text = re.sub(r"<[^>]+>", "", html)
        clean_text = re.sub(r"\s+", " ", clean_text)
        return clean_text.strip()

    @staticmethod
    def truncate_text(text: str, max_length: int = 100) -> str:
        if len(text) <= max_length:
            return text
        return text[: max_length - 3] + "..."

    @staticmethod
    def is_verification_email(subject: str, content: str) -> bool:
        verification_keywords = [
            "verification",
            "verify",
            "confirm",
            "otp",
            "code",
            "authentication",
            "signin",
            "sign in",
            "login",
            "verifikasi",
            "konfirmasi",
            "kode",
        ]

        text_to_check = f"{subject} {content}".lower()

        return any(keyword in text_to_check for keyword in verification_keywords)
