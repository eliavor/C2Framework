"""
Part 2 — Data Parser & Crypto
Currently: plain text only, no encryption.
The encode/decode interface is intentionally kept stable so encryption
can be layered back in here later without touching anything else.
"""


class DataParserCrypto:
    def encode(self, message: str) -> bytes:
        return message.encode()

    def decode(self, data: bytes) -> str:
        return data.decode().strip()
