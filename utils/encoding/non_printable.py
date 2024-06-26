﻿import cbor2

UTF8_MASK = 0xE0000
HEADER = "\U000e0042\U000e0042\U000e0011\U000e0011"  # Unique header consisting of 4 non-printable UTF-8 characters


class NonPrintableEncoder:
    """
    Utility class to encode and decode hidden byte data within a string using non-printable UTF-8 characters.
    """

    @staticmethod
    def encode_dict(text: str, data: dict) -> str:
        """
        Encodes dict data and embeds it within a string, preserving the original text.

        Args:
            text (str): The text to embed the encoded data into.
            data (dict): The dict data to encode.

        Returns:
            str: The string with the encoded data embedded.
        """
        return NonPrintableEncoder.encode(text, cbor2.dumps(data))

    @staticmethod
    def decode_dict(encoded_string: str) -> tuple[str, dict]:
        """
        Extracts and decodes the hidden byte data from a string.

        Args:
            encoded_string (str): The string containing the hidden encoded data.

        Returns:
            bytes: The decoded byte data.

        Raises:
            ValueError: If the encoded string is in an incorrect format.
        """
        try:
            text, dict_bytes = NonPrintableEncoder.decode(encoded_string)
            dict_data = cbor2.loads(dict_bytes)
        except (ValueError, cbor2.CBORDecodeError):
            text, dict_data = encoded_string, None
        # TODO need get error catch

        return text, dict_data

    
    @staticmethod
    def encode(text: str, data: bytes) -> str:
        """
        Encodes byte data and embeds it within a string, preserving the original text.

        Args:
            data (bytes): The byte data to encode.
            text (str): The text to embed the encoded data into.

        Returns:
            str: The string with the encoded data embedded.
        """
        encoded_string = "".join(chr(UTF8_MASK + byte) for byte in data)
        return f"{text}{HEADER}{encoded_string}"

    @staticmethod
    def decode(encoded_string: str) -> tuple[str, bytes]:
        """
        Extracts and decodes the hidden byte data from a string.

        Args:
            encoded_string (str): The string containing the hidden encoded data.

        Returns:
            bytes: The decoded byte data.

        Raises:
            ValueError: If the encoded string is in an incorrect format.
        """
        encoded_body_start = encoded_string.find(HEADER)
        if encoded_body_start == -1:
            raise ValueError(
                "Encoded string does not contain the expected header. Data may be corrupted or not encoded."
            )

        encoded_body_start += len(HEADER)
        encoded_body = encoded_string[encoded_body_start:]
        byte_string = bytes((ord(char) - UTF8_MASK) for char in encoded_body)
        return encoded_string[:encoded_body_start-len(HEADER)], byte_string
