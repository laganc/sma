from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.x509.oid import NameOID
from cryptography import x509
import datetime

"""
  SelfSignedCertificate

  Generate a certificate that is self-signed with a private key.
"""
class SelfSignedCertificate:
  def __init__(self, hostname, passphrase, key=None):
    if key is None:
      # Create a new private key
      self.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

      # Create certificate.
      subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, hostname)
      ])
      self.cert = x509.CertificateBuilder().subject_name(
        subject
        ).issuer_name(
          issuer
          ).public_key(
            self.key.public_key()
            ).serial_number(
              x509.random_serial_number()
              ).not_valid_before(
                datetime.datetime.utcnow()
              ).not_valid_after(
                datetime.datetime.utcnow() + datetime.timedelta(days=10)
              ).sign(
                self.key, hashes.SHA256()
              )

      # Write the certificate and private key to disk.
      self.write('certificate.crt', 'key.pem', passphrase)

    else:
      # TODO: Load established certificate.
      pass

  """
    write()

    Write the certificate and private key PEM to disk.
  """
  def write(self, cert_fn, key_fn, passphrase):
    certfile = open(cert_fn, 'wb')
    certfile.write(self.cert.public_bytes(serialization.Encoding.PEM))
    keyfile = open(key_fn, 'wb')
    keyfile.write(self.key.private_bytes(
      encoding=serialization.Encoding.PEM,
      format=serialization.PrivateFormat.TraditionalOpenSSL,
      encryption_algorithm=serialization.BestAvailableEncryption(passphrase)
      ))
    keyfile.close()
    certfile.close()
