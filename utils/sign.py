import time
import struct

from Crypto.Cipher import AES
from Crypto.Hash import SHA1

import config

SIGN_MAX_AGE = 2

CHECKSUM_LENGTH = 20
TUPPER_ID_LENGTH = 4
CHAT_ID_LENGTH = 8
TS_LENGTH = 8
SIGN_LENGTH = CHECKSUM_LENGTH + TUPPER_ID_LENGTH + CHAT_ID_LENGTH + TS_LENGTH
KEY = config.sign_key


class Sign:
    @staticmethod
    def sign(message, tupper_id, chat_id):
        sign = SHA1.new(message.encode("UTF-8")).digest() + struct.pack(
            "<LQQ", tupper_id, chat_id, int(time.time())
        )
        cipher = AES.new(KEY, AES.MODE_EAX, nonce=KEY)
        sign = cipher.encrypt(sign)

        return sign

    @staticmethod
    def verify(message, sign, message_ts, message_tupper_id, message_chat_id):
        if len(sign) != SIGN_LENGTH:
            return False

        cipher = AES.new(KEY, AES.MODE_EAX, nonce=KEY)
        sign = cipher.decrypt(sign)

        checksum, sign = sign[:CHECKSUM_LENGTH], sign[CHECKSUM_LENGTH:]
        tupper_id, chat_id, ts = struct.unpack("<LQQ", sign)

        if tupper_id != message_tupper_id:
            return False
        
        if chat_id != message_chat_id:
            return False
        
        if message_ts not in range(ts, ts + SIGN_MAX_AGE + 1):
            return False

        if SHA1.new(message.encode("UTF-8")).digest() != checksum:
            return False

        return True
