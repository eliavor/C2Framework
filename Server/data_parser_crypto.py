"""
Part 2 — Data Parser & Crypto
Currently: plain JSON only, no encryption.
The encode/decode interface is intentionally kept stable so encryption
can be layered back in here later without touching anything else.
"""

import json


class DataParserCrypto:
    def encode(self, message: dict) -> bytes:
        return json.dumps(message, separators=(",", ":")).encode()

    def decode(self, data: bytes) -> dict:
        return json.loads(data.decode())
