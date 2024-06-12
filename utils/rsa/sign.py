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
        sign = SHA1.new(message.encode('UTF-8')).digest() + struct.pack('<L', tupper_id) + struct.pack('<Q', int(time.time()))
        cipher = AES.new(KEY, AES.MODE_EAX, nonce=KEY)
        sign = cipher.encrypt(sign)

        return sign

    @staticmethod
    def verify(message, sign, message_ts, message_tupper_id):
        if len(sign) != SIGN_LENGTH:
            return False

        cipher = AES.new(KEY, AES.MODE_EAX, nonce=KEY)
        sign = cipher.decrypt(sign)
        
        sign, ts = sign[:CHECKSUM_LENGTH+TUPPER_ID_LENGTH], sign[-TS_LENGTH:]
        checksum, tupper_id = sign[:CHECKSUM_LENGTH], sign[-TUPPER_ID_LENGTH:]

        tupper_id = struct.unpack('<L', tupper_id)[0]
        
        if tupper_id != message_tupper_id:
            return False
        
        if SHA1.new(message.encode('UTF-8')).digest() != checksum:
            return False
        
        ts = struct.unpack('<Q', ts)[0]

        if message_ts not in range(ts, ts+SIGN_MAX_AGE+1):
            return False
        
        return True
