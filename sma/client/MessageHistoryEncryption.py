from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import json
from pathlib import Path
import os

"""
  MessageHistoryEncryption

  Creates private and public RSA keys and pems to be saved into user config
  file. Allows the loading of the configured RSA keys from disk into memory.
  Encrypts and decrypts texts using the RSA keys and AESGCM for message history.
"""
class MessageHistoryEncryption:
  """
    generate_pems()

    Generate the private and public RSA keys. Generate the PEMs for the RSA keys
    to be saved into the user's config.
  """
  @staticmethod
  def generate_pems(password):
    # Generate the private RSA key
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    # Generate the private RSA key PEM
    private_pem = private_key.private_bytes(
      encoding=serialization.Encoding.PEM,
      format=serialization.PrivateFormat.PKCS8,
      encryption_algorithm=serialization.BestAvailableEncryption(password.encode('utf-8'))
    )

    # Generate the public RSA key
    public_key = private_key.public_key()

    # Generate the public RSA key PEM
    public_pem = public_key.public_bytes(
      encoding=serialization.Encoding.PEM,
      format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    return private_pem, public_pem

  """
    load_public_key()

    Loads the public key from the user's config file.
  """
  @staticmethod
  def load_public_key(username):
    # Build the path to the config file
    root_dir = os.path.dirname(os.path.realpath(__file__))
    user_dir = Path(root_dir + '/{}'.format(username))
    user_config_path = Path(root_dir + '/{}/config.json'.format(username))

    # Validate username input; enforce child path of ./client/
    if not user_config_path.is_relative_to(root_dir):
      return None
  
    # Read the config file and load the public key
    config_fd = open(user_config_path, 'r')
    data = json.load(config_fd)
    config_fd.close()
    
    public_pem = data['public_pem']

    public_key = serialization.load_pem_public_key(public_pem.encode('utf-8'))

    return public_key
  
  """
    load_private_key()

    Loads the private key from the user's config file; password required.
  """
  @staticmethod
  def load_private_key(username, password):
    # Build the path to the config file
    root_dir = os.path.dirname(os.path.realpath(__file__))
    user_dir = Path(root_dir + '/{}'.format(username))
    user_config_path = Path(root_dir + '/{}/config.json'.format(username))

    # Validate username input; enforce child path of ./client/
    if not user_config_path.is_relative_to(root_dir):
      return None
  
    # Read the config file and load the private key with the password
    config_fd = open(user_config_path, 'r')
    data = json.load(config_fd)
    config_fd.close()
    
    private_pem = data['private_pem']

    private_key = serialization.load_pem_private_key(
        private_pem.encode('utf-8'),
        password=password.encode('utf-8'),
    )

    return private_key

  """
    create_encrypted_history_record()

    Create a key and nonce and use it to encrypt a history message. Return the
    RSA-encrypted(key + nonce) + AESGCM-encrypted(message).
  """
  @staticmethod
  def create_encrypted_history_record(public_key, message):
    # Generate the key, nonce, and algorithm
    key = AESGCM.generate_key(bit_length=128)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)

    # Encrypt the message with AESGCM
    message_ciphertext = aesgcm.encrypt(nonce, message.encode('utf-8'), None)

    message_key = key + nonce

    # Encrypt the key and nonce with the RSA public key
    key_ciphertext = public_key.encrypt(
      message_key,
      padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
      )
    )

    return key_ciphertext + message_ciphertext

  """
    decrypt_history_record()

    Decrypt a history message using the private RSA key
  """
  @staticmethod
  def decrypt_history_record(private_key, record):
    key_ciphertext = record[:256] # Get the AESGCM key + nonce
    record_ciphertext = record[256:] # Get the AESGCM-encrypted(message)

    # Use the private RSA key to decrypt the AESGCM key + nonce
    message_key = private_key.decrypt(
      key_ciphertext,
      padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
      )
    )

    # Destructure the AESGCM key + nonce
    key = message_key[:16]
    aesgcm = AESGCM(key)
    nonce = message_key[16:28]

    # Decrypt the AESGCM-encrypted(message)
    record_plaintext = aesgcm.decrypt(nonce, record_ciphertext, None).decode('utf-8')

    return record_plaintext
