#!/usr/bin/env python3

from re import match, split, DOTALL
from select import select
from socket import socket, AF_INET, SHUT_RDWR, SO_REUSEADDR, SOCK_STREAM, SOL_SOCKET
import sqlite3
import ssl
import sys

from SelfSignedCertificate import *
from ServerClientConnection import *

SERVER_ADDRESS = ('localhost', 9000)
USERS_DATABASE = 'users.db'

socket_connections = {} # key: socket, value: Connection

"""
  create_users_database()

  Create a SQL database to store usernames and passwords.
"""
def create_users_database():
  conn = sqlite3.connect(USERS_DATABASE)
  cursor = conn.cursor()

  # Create the database if it does not exist
  cursor.execute('''
    CREATE TABLE IF NOT EXISTS users(
      username TEXT PRIMARY KEY NOT NULL,
      password_hash BLOB NOT NULL,
      salt BLOB NOT NULL
    )
  ''')

  conn.commit()
  conn.close()

"""
  initialize_server()

  Initialize the server's socket and database.
"""
def initialize_server():
  ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
  ctx.load_cert_chain('./certificate.crt', './key.pem')
  sock = socket(AF_INET, SOCK_STREAM)
  server_socket = ctx.wrap_socket(sock)
  server_socket.setblocking(0)
  server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
  server_socket.bind(SERVER_ADDRESS)
  server_socket.listen(5)

  create_users_database()

  return server_socket

'''
  initialize_certificate()

  Signs a certificate to be used for server authentication via TLS.
  Creates two files that contain the certificate and the private key.
  The files are currently just named 'certificate.crt' and 'key.pem'
  
  TODO:
  Modify SelfSignedCertificate to load previously established certificates
  that are shared with the clients.
'''
def initialize_certificate():
  cert = SelfSignedCertificate(SERVER_ADDRESS[0], b'passphrase')

"""
  run_server()

  Event loop for the server. Accept connections and data from clients.
"""
def run_server(server_socket):
  print('Listening for events')

  inputs = [server_socket]
  
  while True:
    readable, _, _ = select(inputs, [], [])

    # Check if there is any data coming from clients
    for ready_socket in readable:
      # Accept connections from new clients
      if ready_socket == server_socket:
        connection = Connection(server_socket, USERS_DATABASE)

        client_socket = connection.get_client_socket()
        socket_connections[client_socket] = connection
        inputs.append(client_socket)

      # Receive data from connected clients
      else:
        connection = socket_connections[ready_socket]
        is_socket_disconnected = connection.process_data()
        if is_socket_disconnected == 1 and ready_socket in inputs: inputs.remove(ready_socket)
        
def main():
  initialize_certificate()
  server_socket = initialize_server()
  run_server(server_socket)
  sys.exit(0)

if __name__ == "__main__":
  try:
    main()
  except KeyboardInterrupt:
    sys.exit(0)
