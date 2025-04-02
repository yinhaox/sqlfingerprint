class SQLFingerprintError(Exception):
    """Base exception for fingerprint errors"""


class SQLParseError(SQLFingerprintError):
    """SQL parsing related errors"""
