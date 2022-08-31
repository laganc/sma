import sys
import tkinter
import tkinter.messagebox

import ClientAuthentication
import ConfigHelper
import MainMenu

"""
  LoginMenu

  Prompt an un-logged in user to:
  - login
  - register a new account
  - exit
"""
class LoginMenu:
  # Draw the GUI window
  def __init__(self, client_socket):
    self.client_socket = client_socket
    self.login_menu = tkinter.Tk()

    # Style chat menu window
    self.login_menu.geometry('300x100')
    self.login_menu.title('Login Menu')
    tkinter.Label(self.login_menu, text='Login Menu').pack(fill=tkinter.X)

    # Add functional buttons
    login_button = tkinter.Button(self.login_menu, text='Login', command=self.__login).pack()
    register_button = tkinter.Button(self.login_menu, text='Register', command=self.__register).pack()
    exit_button = tkinter.Button(self.login_menu, text='Exit', command=lambda: sys.exit(0)).pack()

    # Exit if socket to server not created
    if self.client_socket is None:
      tkinter.messagebox.showinfo('Error', 'Unable to connect to the server!')
      sys.exit(1)

    self.login_menu.mainloop()

  """
    register()

    Get account credentials from the user and attempt to use the credentials to
    register a new account on the server.
  """
  def __register(self):
    register_window = tkinter.Toplevel(self.login_menu)

    # Callback function to register a new account with the server
    def register(_ = None):
      username = username_text.get()
      password = password_text.get()
      repeat_password = repeat_password_text.get()

      # Validate input
      if username and password and repeat_password:
        if ClientAuthentication.validate_username_input(username) is False or ClientAuthentication.validate_password_input(password) is False:
          tkinter.messagebox.showinfo('Error', 'Invalid input!')
          register_window.destroy()
        elif not password == repeat_password:
          tkinter.messagebox.showinfo('Error', 'Passwords do not match!')
          register_window.destroy()
        else:
          # Input validated; attempt to register
          register_success = ClientAuthentication.register(self.client_socket, username, password)
          if register_success is True: # Successful registration
            tkinter.messagebox.showinfo('Success', 'Your account {} has been registered!'.format(username))
            register_window.destroy()
          else: # Failed registration
            tkinter.messagebox.showinfo('Error', 'Registration failed!')
            register_window.destroy()

    # Load menu to register
    # Get the username
    username_label = tkinter.Label(register_window, text='Username').grid(row=0, column=0)
    username_text = tkinter.StringVar()
    username_entry = tkinter.Entry(register_window, textvariable=username_text)
    username_entry.grid(row=0, column=1)

    # Get the password
    password_label = tkinter.Label(register_window, text='Password').grid(row=1, column=0)
    password_text = tkinter.StringVar()
    password_entry = tkinter.Entry(register_window, show='*', textvariable=password_text)
    password_entry.grid(row=1, column=1)

    repeat_password_label = tkinter.Label(register_window, text='Repeat Password').grid(row=2, column=0)
    repeat_password_text = tkinter.StringVar()
    repeat_password_entry = tkinter.Entry(register_window, show='*', textvariable=repeat_password_text)
    repeat_password_entry.grid(row=2, column=1)
    repeat_password_entry.bind('<Return>', register)

    submit_button = tkinter.Button(register_window, text='Register', command=register).grid(row=3, column=1)

  """
    login()

    Get account credentials from the user and attempt to use the credentials to
    login to an existing account on the server.
  """
  def __login(self):
    login_window = tkinter.Toplevel(self.login_menu)

    # Callback function to login to the server with username and password
    def login(_ = None):
      username = username_text.get()
      password = password_text.get()

      # Validate input
      if username and password:
        login_success = ClientAuthentication.login(self.client_socket, username, password)
        if login_success is True: # Successful login
          ConfigHelper.create_user_config(self.client_socket.get_username(), password)
          MainMenu.MainMenu(self.login_menu, self.client_socket)
          self.login_menu.withdraw()
          login_window.destroy()
        else: # Failed login
          tkinter.messagebox.showinfo('Error', 'Login failed!')
          login_window.destroy()

    # Load menu to login
    # Get the username
    username_label = tkinter.Label(login_window, text='Username').grid(row=0, column=0)
    username_text = tkinter.StringVar()
    username_entry = tkinter.Entry(login_window, textvariable=username_text)
    username_entry.grid(row=0, column=1)

    # Get the password
    password_label = tkinter.Label(login_window, text='Password').grid(row=1, column=0)
    password_text = tkinter.StringVar()
    password_entry = tkinter.Entry(login_window, show='*', textvariable=password_text)
    password_entry.grid(row=1, column=1)
    password_entry.bind('<Return>', login)

    submit_button = tkinter.Button(login_window, text='Login', command=login).grid(row=3, column=1)
