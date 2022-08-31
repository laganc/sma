from threading import Thread
import tkinter

import Chat
import ClientAuthentication
import ConfigHelper
import MessageHistory
from Chat import Chat

chats = {}
message_histories = {}

"""
  MainMenu

  Prompt the logged in user for messaging actions:
    - chat
    - view message history
    - delete account
    - exit
"""
class MainMenu:
  # Draw the GUI window
  def __init__(self, login_menu, client_socket):
    self.login_menu = login_menu
    self.client_socket = client_socket

    self.main_menu = tkinter.Toplevel(self.login_menu)

    self.username = self.client_socket.get_username()

    # Style chat menu window
    self.main_menu.geometry('300x150')
    self.main_menu.title('{} - main menu'.format(self.username))
    tkinter.Label(self.main_menu, text='Logged in as: {}'.format(self.username)).pack(fill=tkinter.X)

    # Spawn a new thread to listen for data pushes from the server
    listener = Thread(target=self.__listen, daemon=True)
    listener.start()

    chat_button = tkinter.Button(self.main_menu, text='Chat', command=self.__chat).pack()
    message_history_button = tkinter.Button(self.main_menu, text='Message History', command=self.__initialize_message_history).pack()
    delete_account_button = tkinter.Button(self.main_menu, text='Delete Account', command=self.__delete_account).pack()
    exit_button = tkinter.Button(self.main_menu, text='Exit', command=client_socket.disconnect).pack(side=tkinter.BOTTOM)

  """
    listen()

    Listen for incoming data from the server. Parse incoming data and dispatch the
    incoming user messages accordingly.
  """
  def __listen(self):
    while True:
      data = self.client_socket.receive()

      headers, payload = self.client_socket.parse_incoming(data)
      event = headers['event']

      # Message from recipient
      if event == 'incoming':
        recipient = headers['from']
        message_type = headers['type']

        if recipient not in chats: 
          chats[recipient] = Chat(self.client_socket, self.main_menu, recipient)

        # Received a public key to initiate Diffie-Hellman
        # Use to generate a shared key to eventually decrypt a message
        # Send own public key back
        if message_type == 'dh_init':
          chats[recipient].handle_dh_init(payload)

        # Received a public key to complete Diffie-Hellman from recipient
        # Use to generate a shared key to send encrypted message
        elif message_type == 'dh_fin':
          chats[recipient].handle_dh_fin(payload)

        # Received an encrypted message from recipient
        elif message_type in ['text', 'image']: 
          chats[recipient].load_message(recipient, message_type, payload, encryption = True)

      # Message from server reflecting the outgoing messaging back to client indicating an error
      elif event == 'outgoing' and headers['status'] == 'failure' and headers['type'] == 'server':
        recipient = headers['to']
        if recipient not in chats: chats[recipient] = Chat(self.client_socket, self.main_menu, recipient)
        chats[recipient].load_message(recipient, headers['type'], payload)

  """
    chat()

    Open a GUI window to allow user to initialize a new chat with a recipient.
  """
  def __chat(self):
    recipient_window = tkinter.Toplevel(self.main_menu)

    # Callback function to get the recipient's username and open the chat window
    def get_input(_):
      recipient = input_text.get()
      if recipient not in chats:
        # Start the chat with the recipient
        chats[recipient] = Chat(self.client_socket, self.main_menu, recipient)
      chats[recipient].chat()
      recipient_window.destroy()

    # Load menu to select recipients with whom to chat
    label = tkinter.Label(recipient_window, text='Recipient').pack(side=tkinter.LEFT)
    input_text = tkinter.StringVar()
    recipient_entry = tkinter.Entry(recipient_window, textvariable=input_text)
    recipient_entry.pack(side=tkinter.RIGHT)
    recipient_entry.bind('<Return>', get_input)

  """
    initialize_message_history()

    Open a GUI window to allow user to open a message history with a specific
    reicipient.
  """
  def __initialize_message_history(self):
    select_history_window = tkinter.Toplevel(self.main_menu)

    # Callback function to get the recipient's username and open the history window
    def view_history(_ = None):
      recipient = recipient_text.get()
      password = password_text.get()

      if recipient and password: message_histories[recipient] = MessageHistory.Reader(self.main_menu, self.username, recipient, password)

      select_history_window.destroy()

    # Load menu to load message history
    # Get history for recipient
    recipient_label = tkinter.Label(select_history_window, text='Recipient').grid(row=0, column=0)
    recipient_text = tkinter.StringVar()
    recipient_entry = tkinter.Entry(select_history_window, textvariable=recipient_text)
    recipient_entry.grid(row=0, column=1)

    # Authenticate user to view and decrypt history
    password_label = tkinter.Label(select_history_window, text='Password').grid(row=1, column=0)
    password_text = tkinter.StringVar()
    password_entry = tkinter.Entry(select_history_window, show='*', textvariable=password_text)
    password_entry.grid(row=1, column=1)
    password_entry.bind('<Return>', view_history)

    submit_button = tkinter.Button(select_history_window, text='Open History', command=view_history).grid(row=3, column=1)

  """
    delete_account()

    Re-authenticate the user and delete the account from the server.
  """
  def __delete_account(self):
    delete_account_window = tkinter.Toplevel(self.main_menu)

    # Callback function to delete the currently logged in account
    def delete_account():
      username = username_text.get()
      password = password_text.get()
      repeat_password = repeat_password_text.get()

      # Validate input
      if username and password and repeat_password:
        if confirm_deletion.get() is False:
          tkinter.messagebox.showinfo('Error', 'Account deletion not confirmed!')
          delete_account_window.destroy()
        else:
          if not password == repeat_password or not self.username == username:
            tkinter.messagebox.showinfo('Error', 'Incorrect credentials!')
            delete_account_window.destroy()
          else:
            # Request server to delete the account
            delete_success = ClientAuthentication.delete_account(self.client_socket, password)
            if delete_success is True: # Successful deletion
              tkinter.messagebox.showinfo('Success', 'Your account {} has been deleted!'.format(self.username))
              ConfigHelper.delete_user_config(self.username) # Try to delete user config and history
              ClientAuthentication.logout(self.client_socket)
              delete_account_window.destroy()
            else: # Failed deletion
              tkinter.messagebox.showinfo('Error', 'Account deletion failed!')
              delete_account_window.destroy()

    # Load menu to delete account
    # Get the username
    username_label = tkinter.Label(delete_account_window, text='Username').grid(row=0, column=0)
    username_text = tkinter.StringVar()
    username_entry = tkinter.Entry(delete_account_window, textvariable=username_text)
    username_entry.grid(row=0, column=1)

    # Get the password
    password_label = tkinter.Label(delete_account_window, text='Password').grid(row=1, column=0)
    password_text = tkinter.StringVar()
    password_entry = tkinter.Entry(delete_account_window, show='*', textvariable=password_text)
    password_entry.grid(row=1, column=1)

    # Request the password again
    repeat_password_label = tkinter.Label(delete_account_window, text='Repeat Password').grid(row=2, column=0)
    repeat_password_text = tkinter.StringVar()
    repeat_password_entry = tkinter.Entry(delete_account_window, show='*', textvariable=repeat_password_text)
    repeat_password_entry.grid(row=2, column=1)

    # Checkbox to confirm deletion
    confirm_deletion = tkinter.BooleanVar()
    confirm_deletion_button = tkinter.Checkbutton(delete_account_window, text='Confirm account deletion', variable=confirm_deletion, onvalue=True, offvalue=False).grid(row=3, column=0)

    tkinter.messagebox.showinfo('Attention', 'This will delete all of your data!')

    submit_button = tkinter.Button(delete_account_window, text='Delete Account', command=delete_account).grid(row=3, column=1)
