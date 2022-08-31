import base64
import io
from PIL import Image, ImageTk
from queue import Queue
import tkinter
import tkinter.filedialog

from GCMEncryption import *
import MessageHistory

"""
  Chat

  A wrapper to group messages in the same conversations (i.e., to the same
  recipient) powered by event-driven GUI.
"""
class Chat:
  def __init__(self, client_socket, root, recipient):
    self.client_socket = client_socket
    self.root = root
    self.username = client_socket.get_username()
    self.recipient = recipient
    self.message_queue = Queue() # (username, type, message)
    self.conversation_picture_history = Queue()
    self.history = MessageHistory.Writer(self.username, self.recipient)
    self.shared_keys = Queue()
    self.outgoing_public_keys = Queue()
    self.incoming_public_keys = Queue()

  """
    chat()

    Open a chat window. Accept input to send as messages and update the window
    with incoming messages. Save messags to message history.
  """
  def chat(self):
    chat_window = tkinter.Toplevel(self.root)

    # Style chat window
    chat_window.title('{} - chatting with {}'.format(self.username, self.recipient))
    tkinter.Label(chat_window, text='Chatting with: {}'.format(self.recipient)).pack(fill=tkinter.X)

    """
      encrypted_send()

      Initiate Diffie-Hellman with the recipient by sending them a public key.
    """
    def encrypted_send(message_type, payload):
      # Send the recipient own publc key
      keys = DH_Keys()
      public_key = gen_serialized_key(keys.get_public_key()).decode('utf-8')

      headers = 'event: outgoing\nusername: {}\nto: {}\ntype: dh_init\n\n'.format(self.username, self.recipient)
      self.client_socket.send(headers + public_key)

      # Listen for the recipient's public key in response
      chat_window.after(1, get_shared_key, keys.get_priv_key(), message_type, payload)

    """
      send_dh_fin_keys()

      Callback to send public keys to complete Diffie-Hellman whenever a public
      key is ready to be sent
    """
    def send_dh_fin_keys():
      try:
        public_key = self.outgoing_public_keys.get_nowait()
        headers = 'event: outgoing\nusername: {}\nto: {}\ntype: dh_fin\n\n'.format(self.username, self.recipient)
        self.client_socket.send(headers + public_key)
        chat_window.after(1, send_dh_fin_keys)
      except:
        chat_window.after(1, send_dh_fin_keys)

    """
      get_shared_key()

      Callback to use the recipient's public key to generate the shared key. The
      shared key is then used to encrypt and send the message.
    """
    def get_shared_key(private_key, message_type, payload):
      try:
        # Generate the shared key using the recipient's public key
        recipient_public_key = self.incoming_public_keys.get_nowait()
        shared_key = gen_shared_key(private_key, recipient_public_key)

        # Encrypt the message with the shared key and send it
        cipher = encrypt_message(payload, shared_key)
        decoded_cipher = base64.b64encode(cipher).decode('utf-8')
        headers = 'event: outgoing\nusername: {}\nto: {}\ntype: {}\n\n'.format(self.username, self.recipient, message_type)
        self.client_socket.send(headers + decoded_cipher)

      # Wait until recipient's public key has been sent
      except:
        chat_window.after(1, get_shared_key, private_key, message_type, payload)

    # Callback to get input from user to send to recipient
    def get_input(_):
      payload = input_text.get()
      message_entry.delete(0, tkinter.END) # Clear input field
      self.message_buffer = payload # Save message in buffer to encrypt later

      # Begin Diffie-Hellman and ultimately send encrypted message
      encrypted_send('text', payload)

      # Display the message in the chat window
      self.load_message(self.username, 'text', payload)

    # Callback to select an image to send to the recipient
    # Only GIFs are supported
    def get_image():
      image_path = tkinter.filedialog.askopenfilename(initialdir='~', title='Select image', filetypes=(('gif files','*.gif'),))
      if image_path:
        fd = open(image_path, 'rb')
        payload = base64.b64encode(fd.read()).decode('utf-8')
        fd.close()
        self.message_buffer = payload # Save image in buffer to encrypt later
        self.message_type_buffer = 'image'

        # Begin Diffie-Hellman and ultimately send encrypted message
        encrypted_send('image', payload)

        # Display the image in the chat window
        self.load_message(self.username, 'image', payload)

    # Callback to update the chat window with messages periodically
    def display_conversation():
      while not self.message_queue.empty():
        try:
          # Get new messages to load into the chat window
          sender, message_type, message = self.message_queue.get_nowait()

          # Simply print text messages
          if message_type == 'text':
            conversation.insert(tkinter.END, '{}: {}\n'.format(sender, message))
            self.history.save_to_history(sender, message_type, message) # Save to history

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

            self.history.save_to_history(sender, message_type, message) # Save to history

          # Server message
          else:
            conversation.insert(tkinter.END, '{}\n'.format(message))

          if not message_type == 'server': self.save_history(sender, message_type, message)
            
        except:
          continue

      chat_window.after(1, display_conversation) # Update the GUI window

    # Create a Text widget to display the messages
    conversation = tkinter.Text(chat_window)
    conversation.pack()

    # Request input from the user
    label = tkinter.Label(chat_window, text='Message').pack()
    input_text = tkinter.StringVar()
    message_entry = tkinter.Entry(chat_window, textvariable=input_text)
    message_entry.pack()
    message_entry.bind('<Return>', get_input)

    # Request image from the user
    image_entry = tkinter.Button(chat_window, text='Send Image', command=get_image)
    image_entry.pack()

    # Update the screen with messages
    display_conversation()

    # Send out public keys to complete Diffie-Hellman when they're available
    send_dh_fin_keys()

  """
    load_message()

    If the message is not encrypted, simply queue the message so it gets loaded
    into the GUI chat window in order of receipt.

    If the message is encrypted, retrieve the queued shared_key and use it to
    decrypt the message before loading it into the GUI chat window.
  """
  def load_message(self, sender, message_type, message, encryption = False):
    # No decryption necessary
    if encryption is False:
      self.message_queue.put_nowait((sender, message_type, message))

    # Decrypt
    else:
      shared_key = self.shared_keys.get()
      encoded_cipher = base64.b64decode(message.encode('utf-8'))
      decrypted_message = decrypt_message(encoded_cipher, shared_key)
      self.message_queue.put_nowait((sender, message_type, decrypted_message))

  """
    handle_dh_init()

    Recipient has sent self their public key to initiate Diffie-Hellman. Use 
    the recipient's public key to generate the shared key to decrypt the
    recipient's encrpyted message, which will come next. Send the recipient
    self's public key so that they can complete Diffie-Hellman and can generate
    the shared key to encrypt the message with.
  """
  def handle_dh_init(self, public_key):
    # Create a shared key using the recipient's public key and enqueue it to use
    # to decode the incoming encrypted message
    keys = DH_Keys()
    shared_key = gen_shared_key(keys.get_priv_key(), gen_deserialized_key(public_key))
    self.shared_keys.put_nowait(shared_key)

    # Send own public key to recipient in `send_dh_fin_keys()`
    serialized_self_public_key = gen_serialized_key(keys.get_public_key()).decode('utf-8')
    self.outgoing_public_keys.put(serialized_self_public_key)

  """
    handle_dh_fin()

    Recipient has responded to self's Diffie-Hellman request with a public key.
    Use the recipient's public key to generate a shared key in `get_shared_key()`.
  """
  def handle_dh_fin(self, public_key):
    self.incoming_public_keys.put_nowait(gen_deserialized_key(public_key))
