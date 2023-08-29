import base64

from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives import serialization

rsa_private_key = '''
-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDHdsyxT66pDG4p73yope7jxA92
c0AT4qIJ/xtbBcHkFPK77upnsfDTJiVEuQDH+MiMeb+XhCLNKZGp0yaUU6GlxZdp
+nLW8b7Kmijr3iepaDhcbVTsYBWchaWUXauj9Lrhz58/6AE/NF0aMolxIGpsi+ST
2hSHPu3GSXMdhPCkWQIDAQAB
-----END PUBLIC KEY-----
'''


class EMTradeEncrypt:

    def __init__(self):
        self._pub_key: rsa.RSAPublicKey = serialization.load_pem_public_key(rsa_private_key.encode('utf-8'))

    def encrypt(self, content: str) -> str:
        encrypt_text = self._pub_key.encrypt(content.encode(), padding.PKCS1v15())
        return base64.b64encode(encrypt_text).decode('utf-8')
