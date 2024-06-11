import time
import struct

from Crypto.Cipher import AES
from Crypto.Hash import SHA1

import config

SIGN_MAX_AGE = 2

CHECKSUM_LENGTH = 20
TS_LENGTH = 8
KEY = config.sign_key

class RSASign:
    @staticmethod
    def sign(message):
        sign = SHA1.new(message.encode('UTF-8')).digest() + struct.pack('<Q', int(time.time()))
        cipher = AES.new(KEY, AES.MODE_EAX, nonce=KEY)
        sign = cipher.encrypt(sign)

        return sign

    @staticmethod
    def verify(message, sign, message_ts):
        cipher = AES.new(KEY, AES.MODE_EAX, nonce=KEY)
        sign = cipher.decrypt(sign)
        
        checksum, ts = sign[:CHECKSUM_LENGTH], sign[-TS_LENGTH:]

        if SHA1.new(message.encode('UTF-8')).digest() != checksum:
            return False
        
        ts = struct.unpack('<Q', ts)[0]

        if message_ts not in range(ts, ts+SIGN_MAX_AGE+1):
            return False
        
        return True
