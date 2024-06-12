import time
import struct

from Crypto.Cipher import AES
from Crypto.Hash import SHA1

import config

SIGN_MAX_AGE = 2

CHECKSUM_LENGTH = 20
TUPPER_ID_LENGTH = 4
TS_LENGTH = 8
SIGN_LENGTH = CHECKSUM_LENGTH + TUPPER_ID_LENGTH + TS_LENGTH
KEY = config.sign_key


class RSASign:
    @staticmethod
    def sign(message, tupper_id):
        sign = SHA1.new(message.encode("UTF-8")).digest() + struct.pack(
            "<LQ", tupper_id, int(time.time())
        )
        cipher = AES.new(KEY, AES.MODE_EAX, nonce=KEY)
        sign = cipher.encrypt(sign)

        return sign

    @staticmethod
    def verify(message, sign, message_ts, message_tupper_id):
        if len(sign) != SIGN_LENGTH:
            return False

        cipher = AES.new(KEY, AES.MODE_EAX, nonce=KEY)
        sign = cipher.decrypt(sign)

        checksum, sign = sign[:CHECKSUM_LENGTH], sign[CHECKSUM_LENGTH:]
        tupper_id, ts = struct.unpack("<LQ", sign)

        if tupper_id != message_tupper_id:
            return False

        if message_ts not in range(ts, ts + SIGN_MAX_AGE + 1):
            return False

        if SHA1.new(message.encode("UTF-8")).digest() != checksum:
            return False

        return True
