#!/usr/bin/env python3

import json
from socket import socket, AF_INET, SOCK_STREAM
import ssl
import sys

import ClientServerConnection
import LoginMenu

"""
  connect()

  Try to connect to the configured server. If connection is unsuccessful, exit.
"""
def connect(server_address):
  # Connect to the server
  try:
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.load_verify_locations('certificate.crt')
    pre_sock = socket(AF_INET, SOCK_STREAM)
    sock = ctx.wrap_socket(pre_sock, server_hostname=server_address[0])
    sock.connect(server_address)

    return ClientServerConnection.ClientServerConnection(sock)

  # Failed to connect to server
  except:
    sys.stderr.write('Unable to connect to the server\n')
    return None

def main():
  # Open config file
  with open("./client/config.json") as config_file:
    config = json.load(config_file)

  # Connect to the server
  client_socket = connect((config['server']['ip'], config['server']['port']))

  # Launch login menu
  LoginMenu.LoginMenu(client_socket)

if __name__ == "__main__":
  try:
    main()
  except KeyboardInterrupt:
    sys.exit(0)
