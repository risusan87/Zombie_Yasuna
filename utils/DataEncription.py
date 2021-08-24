from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto import Random

iv_def = 'jfbc72mfj5ldncgz'.encode()


def create_aes(password, iv):
    sha = SHA256.new()
    sha.update(password.encode())
    key = sha.digest()
    return AES.new(key, AES.MODE_CFB, iv)


def encrypt(data: bytes, password: str):
    iv = Random.new().read(AES.block_size)
    return iv + create_aes(password, iv).encrypt(data)


def decrypt(data: bytes, password: str):
    iv, cipher = data[:AES.block_size], data[AES.block_size:]
    return create_aes(password, iv).decrypt(cipher)