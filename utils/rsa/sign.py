import time
import struct

from Crypto.Cipher import AES
from Crypto.Hash import SHA1

import config
from utils.encoding.non_printable import NonPrintableEncoder

CHECKSUM_LENGTH = 20
TS_LENGTH = 8
SIGN_LENGTH = CHECKSUM_LENGTH + TS_LENGTH
TS_DIFF = 3
KEY = config.sign_key

class RSASign:
    @staticmethod
    def sign(message):
        sign = SHA1.new(message.encode('UTF-8')).digest() + struct.pack('<Q', int(time.time()))
        cipher = AES.new(KEY, AES.MODE_EAX, nonce=KEY)
        sign = cipher.encrypt(sign)
        sign = NonPrintableEncoder.encode_raw(sign)

        return message + sign

    @staticmethod
    def verify(message, message_ts): 
        if len(message) <= SIGN_LENGTH:
            return False
        
        message, sign = message[:-SIGN_LENGTH], message[-SIGN_LENGTH:]
        sign = NonPrintableEncoder.decode_raw(sign)
        cipher = AES.new(KEY, AES.MODE_EAX, nonce=KEY)
        sign = cipher.decrypt(sign)
        
        checksum, ts = sign[:-TS_LENGTH], sign[-TS_LENGTH:]

        if SHA1.new(message.encode('UTF-8')).digest() != checksum:
            return False
        
        ts = struct.unpack('<Q', ts)[0]

        if message_ts not in range(ts, ts+TS_DIFF+1):
            return False
        
        return True
