class NonPrintableEncoder:
    """
    Utility class to encode and decode hidden byte data within a string using non-printable UTF-8 characters.
    """

    HEADER = '\u2400\u2401\u2402\u2403'  # Unique header consisting of 4 non-printable UTF-8 characters

    @staticmethod
    def encode(data, text):
        """
        Encodes byte data and embeds it within a string, preserving the original text.

        Args:
            data (bytes): The byte data to encode.
            text (str): The text to embed the encoded data into.

        Returns:
            str: The string with the encoded data embedded.
        """
        encoded_body = ''.join(chr(byte) for byte in data)
        return f"{text}{NonPrintableEncoder.HEADER}{encoded_body}"

    @staticmethod
    def decode(encoded_string):
        """
        Extracts and decodes the hidden byte data from a string.

        Args:
            encoded_string (str): The string containing the hidden encoded data.

        Returns:
            bytes: The decoded byte data.

        Raises:
            ValueError: If the encoded string is in an incorrect format.
        """
        encoded_body_start = encoded_string.find(NonPrintableEncoder.HEADER)
        if encoded_body_start == -1:
            raise ValueError("Encoded string does not contain the expected header. Data may be corrupted or not encoded.")

        encoded_body_start += len(NonPrintableEncoder.HEADER)
        encoded_body = encoded_string[encoded_body_start:]
        return encoded_body.encode('utf-8')
