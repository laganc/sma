import json
import os
from pathlib import Path
import shutil

import MessageHistoryEncryption

"""
  create_user_config()

  Create the user's config.json file and user directory if they don't exist.
"""
def create_user_config(username, password):
  # Build the path to the user's config file
  root_dir = os.path.dirname(os.path.realpath(__file__))
  user_dir = Path(root_dir + '/{}'.format(username))
  user_config_path = Path(root_dir + '/{}/config.json'.format(username))

  # Validate username input; enforce child path of ./client/
  if not user_config_path.is_relative_to(root_dir):
    return None

  # Create the user directory for username if it doesn't exist
  try:
    os.makedirs(user_dir)
  except FileExistsError:
    pass

  # Create a new config file if it doesn't exist
  if os.path.exists(user_config_path):
    return None

  # Generate the private and pubic RSA keys' PEMs to write to the config file
  private_pem, public_pem = MessageHistoryEncryption.MessageHistoryEncryption().generate_pems(password)

  data = {}
  data['private_pem'] = private_pem.decode('utf-8')
  data['public_pem'] = public_pem.decode('utf-8')

  # Write the config file
  config_fd = open(user_config_path, 'w')
  json.dump(data, config_fd, indent=2)
  config_fd.close()

"""
  delete_user_config()

  Attempt to delete the user's saved data (config and history).
"""
def delete_user_config(username):
  # Build the path to the user's config file
  root_dir = os.path.dirname(os.path.realpath(__file__))
  user_dir = Path(root_dir + '/{}'.format(username))

  # Validate username input; enforce child path of ./client/
  if not user_dir.is_relative_to(root_dir):
    return None

  # Delete the user directory if it exists
  if os.path.exists(user_dir):
    try:
      shutil.rmtree(user_dir)
    except:
      pass
