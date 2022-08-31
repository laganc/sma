# Secure Messaging Application

This is the Gitlab repository for Secure Messaging Application for **Group 16: Gordon Chiang, Lagan Chohan, Tyler Fowler, and Alex Li**.

Secure Messaging Application is a Python program that allows users to securely and synchronously message one another.

[A video demo of Secure Messaging Application in action can be found here](https://gitlab.csc.uvic.ca/courses/2021091/SENG360/teams/group-16/sma/-/blob/main/doc/Demo_Video.mp4).

## Documentation

**Please refer to the [Gitlab Wiki](https://gitlab.csc.uvic.ca/courses/2021091/SENG360/teams/group-16/sma/-/wikis/home) for more in-depth documentation**.

**Please refer to the [archived legacy Gitlab repo](https://gitlab.csc.uvic.ca/courses/2021091/SENG360/teams/group-16/sm-legacy) to view the project's activity history**. Secure Messaging Application moved repos because of a bug that prevented us from pushing changes to the legacy repo. The legacy repo was cloned to this repo--this repo is now the most up-to-date.

## Installation

Secure Messaging Application requires **Python 3.9 or higher**.

After cloning the repo, run `pip install -r requirements.txt` from the root directory to install all dependencies.

## Usage

### Server

1. Setup the server from the **root directory** to generate a certificate: `python3 ./server/server.py`.
    * The pathing ensures the client can locate and load the certificate to establish a TLS connection with the server.
2. The server will prompt for the private key PEM's pass phrase, which is currently hardcoded as `passphrase`.
3. The server will output `Listening for events` to the terminal when it is setup and ready to accept clients and listen for events.

![Screenshot of server output](doc/server_output_example.png)

### Client

1. With the server running, create a client instance: `python3 ./client/client.py`.
2. The client's GUI will load which will prompt the user for account management events:
    1. Login: login to an existing account with the server using a username and password.
    2. Register: register a new account with the server using a username and password.
    3. Exit: close the client.

![Screenshot of the login menu](doc/login_menu_example.png)

3. Once the user is authenticated into a user account, they may choose various options:
    1. Chat: select a user with whom to chat synchronously.
    2. Message History: view the saved message history with a user (password-protected).
    3. Delete Account: delete the currently logged in account from the server (password-protected).
    4. Exit: close the client.

![Screenshot of the main menu](doc/main_menu_example.png)

4. You may create multiple client instances for testing purposes.

![Screenshot of example 1:1 messenging](doc/messenging_example.png)
