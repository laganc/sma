import base64
import io
from pathlib import Path
from PIL import Image, ImageTk
from queue import Queue
from re import match, DOTALL
import os
import tkinter
import tkinter.messagebox

import MessageHistoryEncryption

"""
  Reader

  Reads the history between the logged in user and a recipient. The user's
  password is required to view the history.
"""
class Reader:
  def __init__(self, root, username, recipient, password):
    self.username = username
    self.root = root
    self.recipient = recipient

    # Authenticate the user with their password (to access their configured private key)
    try:
      self.private_key = MessageHistoryEncryption.MessageHistoryEncryption().load_private_key(username, password)
    except:
      self.__show_error()
      return

    # View history, if available
    self.history = self.__open_history()
    if self.history is None:
      self.__show_error()
    else:
      self.conversation_picture_history = Queue() # To avoid garbage collection
      self.__show_history()

  """
    open_history()

    Opens the .his (history) file for reading.
  """
  def __open_history(self):
    # Build the path to the .his file
    root_dir = os.path.dirname(os.path.realpath(__file__))
    history_path = Path(root_dir + '/{}/{}.his'.format(self.username, self.recipient))

    # Validate username and recipient input; enforce child path of ./client/
    if not history_path.is_relative_to(root_dir):
      return None

    # Open the file
    try:
      fd = open(history_path, 'r')
    except:
      return None
    else:
      history = fd.read()
      fd.close()
      return self.__decode_history(history) # Decrypt and decode the messages in the history

  """
    decode_history()

    Decodes the .his (history) file content to strings and decrypts it.
  """
  def __decode_history(self, history):
    decoded_history = Queue()

    # Decode and decrypt history recrods
    for record in [r for r in history.split('\n') if r]:
      # Decode the history record
      decoded_record = base64.b64decode(record.encode('utf-8'))

      # Decrypt the record
      record = MessageHistoryEncryption.MessageHistoryEncryption().decrypt_history_record(self.private_key, decoded_record)

      # Fetch the metadata and message from the record and enqueue it to load into GUI
      record_match = match('^(?P<sender>.*?)\n(?P<type>.*?)\n(?P<message>.*)$', record, flags=DOTALL)

      decoded_history.put_nowait((
        record_match['sender'],
        record_match['type'],
        record_match['message'],
      ))

    return decoded_history

  """
    show_history()

    Displays the history in the GUI.
  """
  def __show_history(self):
    # Display an error if no history to show
    if self.history is None or self.history.empty() is True:
      self.__show_error()
      return

    history_window = tkinter.Toplevel(self.root)

    # Style chat window
    history_window.title('{} - message history with {}'.format(self.username, self.recipient))
    tkinter.Label(history_window, text='Message history with: {}'.format(self.recipient)).pack(fill=tkinter.X)

    # Create a Text widget and display the plaintext history
    conversation = tkinter.Text(history_window)
    conversation.pack()

    # Load message history into the GUI window
    self.__load_messages(conversation)

    # Create a button to delete the history
    delete_button = tkinter.Button(history_window, text='Delete History', command=lambda: self.__delete_history(history_window)).pack()

  """
    load_messages()

    Loads the decoded messages in the history into the GUI window.
  """
  def __load_messages(self, conversation):
    while self.history.empty() is False:
      # Get new messages to load into the history window
      sender, message_type, message = self.history.get_nowait()

      # Simply print text messages
      if message_type == 'text':
        conversation.insert(tkinter.END, '{}: {}\n'.format(sender, message))

      # Convert images back to image format and display them
      elif message_type == 'image':
        conversation.insert(tkinter.END, '{}:\n'.format(sender))

        # Convert image from string to bytes
        image_data = base64.b64decode(message.encode('utf-8'))

        # Open the image from memory to avoid saving to disk
        image = Image.open(io.BytesIO(image_data))
        img = ImageTk.PhotoImage(image)

        # Prevent image from being garbage-collected; persist in chat window
        self.conversation_picture_history.put(img) 

        # Create image on the GUI
        conversation.image_create(tkinter.END, image=img)
        conversation.insert(tkinter.END, '\n')

  """
    show_error()

    Displays an error if something goes wrong during history viewing:
      - failed authentication
      - no history available
  """
  def __show_error(self):
    tkinter.messagebox.showinfo('Error', 'History unavailable!')

  """
    delete_history()

    Deletes the currently opened .his (history) file.
  """
  def __delete_history(self, history_window):
    # Build the path to the history file
    root_dir = os.path.dirname(os.path.realpath(__file__))
    history_path = Path(root_dir + '/{}/{}.his'.format(self.username, self.recipient))

    # Validate username and recipient input; enforce child path of ./client/
    if not history_path.is_relative_to(root_dir):
      return None

    # Delete the file if it exists
    if os.path.exists(history_path): os.remove(history_path)

    tkinter.messagebox.showinfo('Success', 'History with {} has been deleted!'.format(self.recipient))

    history_window.destroy()

"""
  Writer

  Writes records into the history. Encodes the records into strings and encrypts
  it.
"""
class Writer:
  def __init__(self, username, recipient):
    self.username = username
    self.recipient = recipient

    # Load the public key from the user's config file
    self.public_key = MessageHistoryEncryption.MessageHistoryEncryption().load_public_key(username)

  """
    open_history()

    Opens the .his (history) file for appending.
  """
  def __open_history(self):
    # Build the path to the history file
    root_dir = os.path.dirname(os.path.realpath(__file__))
    history_dir = Path(root_dir + '/{}'.format(self.username))
    history_path = Path(root_dir + '/{}/{}.his'.format(self.username, self.recipient))

    # Validate username and recipient input; enforce child path of ./client/
    if not history_path.is_relative_to(root_dir):
      return None

    # Create the history directory for self.username if it doesn't exist
    try:
      os.makedirs(history_dir)
    except FileExistsError:
      pass

    # Create a new history file or open an existing one
    return open(history_path, 'a')

  """
    save_to_history()

    Saves new encoded and encrypted records into the .his (history) file.
  """
  def save_to_history(self, sender, message_type, message):
    # Build the metadata + message for the record
    plaintext = '{}\n{}\n{}'.format(sender, message_type, message)

    # Encrypt the record
    history_bytes = MessageHistoryEncryption.MessageHistoryEncryption().create_encrypted_history_record(self.public_key, plaintext)

    # Encode the record from bytes to string
    record = base64.b64encode(history_bytes).decode('utf-8')

    # Write the record to disk (delimit with newlines)
    history_fd = self.__open_history()
    history_fd.write(record + '\n')
    history_fd.close()
