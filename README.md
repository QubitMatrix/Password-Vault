# Password-Vault
Secure CLI based password vault built using Python.   

## Features 
- No password is visible as plaintext, all passwords entered on the terminal are hidden
- Retrieved password is not displayed anywhere, it is directly copied to the clipboard
- Clipboard cleared after every use to avoid password leakage
- Follows Defence-in-Depth and uses three levels of authentication before retrieving a password and two levels to enter or modify passwords
- Passwords are stored into the database after encrypting it twice, first with a random session key and second with a master key inputted by user, 128 bit AES encryption used
- Reminder at login to change passwords that are older than 60 days
- Inbuilt password generator
- App name can only be alphanumeric to avoid SQL injection   

## Steps to Execute
### Initial Setup
1. Clone the repo   
`git clone https://github.com/QubitMatrix/Password-Vault.git`
2. Install the required packages   
`cd Password-Vault/  && pip install -r requirements.txt`
3. Create a separate user and database in MySQL   
`CREATE DATABASE databasename;`   
`CREATE USER 'username'@'localhost' IDENTIFIED BY "password";`   
`GRANT ALL ON databasename.* TO 'username'@'localhost';`   
    > Replace `databasename`, `password` and `username` as needed and replace it in the program as well

**Hurray!! The initial setup is now complete and moving along further just a single line command is enough to add and manage your passwords!**

### Execution   
Windows:   
`python vault.py`   
Unix:   
`python3 vault.py`   

A master key will be needed for all the passwords, retrieved passwords will be copied to the clipboard.

> Ensure the values for `databasename` and `username` in the program is replaced as required.   
> Follow the instructions to ensure all the database connections are closed, don't use forced exit like CTRL+C, CTRL+Z, etc as it will leave the connections open and can lead to password leak.
