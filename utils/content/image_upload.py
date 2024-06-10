from urllib.parse import urlparse

import paramiko
from paramiko import SSHClient, SFTPClient

import config


class ImageStorage:
    def __init__(self):
        self.client = SSHClient()
        sftp_path = urlparse(config.values.get("secrets.sftp_path"))
        print(sftp_path)

        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        temp = sftp_path.netloc.split("@")
        self.path = sftp_path.path
        self.user = temp[0]
        self.host = temp[1].split(":")[0]
        self.port = int(temp[1].split(":")[1])
        self.https_path = config.values.get("secrets.sftp_path")

    def _connect(self):
        self.client.connect(hostname=self.host, port=self.port, username=self.user,
                            key_filename=config.values.get("secrets.ssh_key_path"))

    def upload_file(self, data: bytes, filename: str) -> str:
        self._connect()
        sftp: SFTPClient = self.client.open_sftp()
        sftp.chdir(self.path)
        with sftp.file(filename, "wb") as sftp_file:
            sftp_file.write(data)
        sftp.close()
        self.client.close()
        return f"{self.https_path}{filename}"


if __name__ == "__main__":
    iS = ImageStorage()
    with open("test.png", "rb") as png_test:
        iS.upload_file(png_test.read(), "pngtest.png")
