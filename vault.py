from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Hash import SHA256
import getpass
import pyperclip
import random
import mysql.connector
import sys
from datetime import datetime

# Generate random 26 characters password 
def generate_password():
    numbers=['1','2','3','4','5','6','7','8','9','0']
    symbols=['@','#','&','*','_','!','$','%','?']
    alphabets= ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']
    count=0
    gen_password=""
    while(count<26):
        a=random.randint(1,4)
        if(a==1):
            b=random.randint(0,9)
            gen_password=gen_password+numbers[b]
        elif(a==2):
            b=random.randint(0,8)
            gen_password=gen_password+symbols[b]
        else:
            b=random.randint(0,25)
            if(a==3):
                gen_password=gen_password+alphabets[b]
            else:
                gen_password=gen_password+alphabets[b].upper()
        count+=1
    return bytes(gen_password,'utf-8')

# Handle inserting new app's password
def insert_new(password):
    app=input("Choose app\n")
    if(not app.isalnum()):
        print("App name should be alphanumeric only, no special characters")
        return
    session_key=get_random_bytes(16)
    cipher1=AES.new(session_key, AES.MODE_EAX)
    ciphertext1=cipher1.encrypt(password)
    nonce1=cipher1.nonce
    master_key=bytes(getpass.getpass(prompt="Enter master key (16bytes)\n"), 'utf-8')
    while(1):
        try:
            cipher2=AES.new(master_key,AES.MODE_EAX)
        except:
            master_key=bytes(getpass.getpass(prompt="Master key should have exactly 16 characters only\n"), 'utf-8')
        else:
            break
    ciphertext2=cipher2.encrypt(ciphertext1)
    nonce2=cipher2.nonce
    try:
        mycursor.execute("INSERT INTO vault (app, ciphertext, session_key, nonce1, nonce2) VALUE (%s,%s,%s,%s,%s);", (app, ciphertext2, session_key, nonce1, nonce2))
        mydb.commit()
        now=datetime.now().strftime("%Y-%m-%d")
        mycursor.execute("INSERT INTO times VALUE (%s,%s);", (app, now)) # Add modified time
        mydb.commit()
    except Exception as e:
        print("Database error: ",e)

# Handle updating existing app's password
def modify():
    app=input("Choose app\n")
    if(not app.isalnum()):
        print("App name should be alphanumeric only, no special characters")
        return
    choice1=input("Enter 0 to generate new, 1 to manually enter password, anything else to abort modify\n")
    if(choice1=='0'):
        password=generate_password()
    elif(choice1=='1'):
        password=bytes(getpass.getpass(prompt="Enter password\n"),'utf-8')
    else:
        return
    session_key=get_random_bytes(16)
    cipher1=AES.new(session_key, AES.MODE_EAX)
    ciphertext1=cipher1.encrypt(password)
    nonce1=cipher1.nonce
    master_key=bytes(getpass.getpass(prompt="Enter master key (16bytes)\n"), 'utf-8')
    while(1):
        try:
            cipher2=AES.new(master_key,AES.MODE_EAX)
        except:
            master_key=bytes(getpass.getpass(prompt="Master key should have exactly 16 characters only\n"), 'utf-8')
        else:
            break
    ciphertext2=cipher2.encrypt(ciphertext1)
    nonce2=cipher2.nonce
    try:
        mycursor.execute("UPDATE vault SET ciphertext=%s, nonce1=%s, nonce2=%s, session_key=%s WHERE app=%s;", (ciphertext2, nonce1, nonce2, session_key, app))
        mydb.commit()
        currtime=datetime.now().strftime("%Y-%m-%d")
        mycursor.execute("UPDATE times SET modified=%s WHERE app=%s;", (currtime, app))
        mydb.commit()
    except Exception as e:
        print("Database error ",e)

# Retrieve app's password and copy to clipboard
def retrieve():
    app=input("Choose app\n")
    if(not app.isalnum()):
        print("App name should be alphanumeric only, no special characters")
        return
    try:
        mycursor.execute("SELECT * FROM vault WHERE app=%s;", (app,))
        res=mycursor.fetchall()
    except Exception as e:
        print("Database error ",e)
    
    try:
        app, ciphertext2, session_key, nonce1, nonce2 = res[0]
    except IndexError:
        print("App not found")
    except Exception as e:
        print(e)
    else:
        master_key=bytes(getpass.getpass(prompt="Enter master key(16bytes)\n"), 'utf-8')
        while(1):
            try:
                cipher1=AES.new(master_key, AES.MODE_EAX, nonce=nonce2)
            except:
                master_key=bytes(getpass.getpass(prompt="Master key should have exactly 16 characters only\n"), 'utf-8')
            else:
                break
        text1=cipher1.decrypt(ciphertext2)
        cipher2=AES.new(session_key, AES.MODE_EAX, nonce=nonce1)
        text2=cipher2.decrypt(text1)
        try:
            app_password=text2.decode('utf-8')
        except:
            print("Wrong master key")
        else:
            pyperclip.copy(app_password) # copy to clipboard

# Check which passwords have exceeded 60 days
def get_timeout_passwords():
    currtime=datetime.now().strftime("%Y-%m-%d")
    mycursor.execute("SELECT app, modified FROM times;")
    res=mycursor.fetchall()
    l=[]
    for x in range(len(res)):
        mycursor.execute("SELECT DATEDIFF(%s,%s);",(currtime,res[x][1])) # Difference between current date and date of modification
        res1=mycursor.fetchall()
        if(res1[0][0]>60):
            l.append(res[x][0])
    return(l)

# Authenticate Login
def authentication():
    auth_password=bytes(getpass.getpass(prompt="Enter your vault login password\n"),'utf-8')
    hash_obj=SHA256.new(auth_password)
    current_hash=bytes(hash_obj.hexdigest(), 'utf-8')

    try:
        mycursor.execute("SELECT * FROM login;")
        res=mycursor.fetchall()
        hashval=res[0][0]
        nonceval=res[0][1]
    except Exception as e:
        print("Database error",e)
    else:
        auth_key=bytes(getpass.getpass(prompt="Enter your vault login key (16bytes)\n"),'utf-8')
        while(1):
            try:
                cipher=AES.new(auth_key, mode=AES.MODE_EAX, nonce=nonceval)
            except:
                auth_key=bytes(getpass.getpass(prompt="Login key should be 16 bytes\n"),'utf-8')
            else:
                break
        hashval=cipher.decrypt(hashval)

        return(current_hash==hashval)
            
def login():
    res=None
    res1=None
    try:
        mycursor.execute("SELECT * FROM login;")
        res=mycursor.fetchone()
        mycursor.execute("SELECT app FROM vault;")
        res1=mycursor.fetchone()
    except Exception as e:
        print("Error",e)

    # First time login
    if(res==None and res1==None):
        auth_onetime=getpass.getpass(prompt="Initial Setup...\nEnter a password for your vault\n")
        obj=SHA256.new(bytes(auth_onetime, 'utf-8'))
        hashed=obj.hexdigest()

        login_key=bytes(getpass.getpass(prompt="Enter a key for your vault (16bytes)\n"), 'utf-8')
        while(1):
            try:
                cipher=AES.new(login_key, mode=AES.MODE_EAX)
            except:
                login_key=bytes(getpass.getpass(prompt="Key for your vault should be 16bytes)\n"), 'utf-8')
            else:
                break
        hashed_enc=cipher.encrypt(bytes(hashed, 'utf-8'))
        nonce=cipher.nonce
        try:
            mycursor.execute("INSERT INTO login VALUE(%s,%s);",(hashed_enc,nonce))
            mydb.commit()
        except:
            sys.exit("Error in setup, try again")
        else:
            sys.exit("Successfully set up, execute again to start the vault")

    else:
        if(authentication()):
            apps=get_timeout_passwords()
            if(apps):
                print("The passwords for these apps have remained unchanged for over 60 days:", apps)

            while(1):
                choice=input("Choose 0 to generate and insert new, 1 to manually insert new, 2 to modify, 3 to retrieve, anything else to exit\n")
                pyperclip.copy("abc") # Change clipboard contents to abc to avoid leaking of passsword
                if(choice=='0'):
                    password=generate_password()
                    insert_new(password)
                elif(choice=='1'):
                    password=bytes(getpass.getpass(prompt="Enter password\n"),'utf-8')
                    insert_new(password)
                elif(choice=='2'):
                    modify()
                elif(choice=='3'):
                    retrieve()
                else:
                    mycursor.close()
                    mydb.close()
                    break
        else:
            sys.exit("Wrong login password")
    

if __name__ == "__main__":
    pwd=getpass.getpass(prompt="Enter database password")
    try:
        mydb=mysql.connector.connect(
            host="localhost",
            username="username", # Replace username with the username set while creating the database
            database="databasename", # Replace database name
            password=pwd
        )
        mycursor=mydb.cursor()
    except:
        sys.exit("Unable to connect to database, check password and mysql service status")

    try:
        mycursor.execute("CREATE TABLE IF NOT EXISTS vault(app VARCHAR(30) PRIMARY KEY, ciphertext VARBINARY(100) NOT NULL, session_key VARBINARY(100) NOT NULL, nonce1 VARBINARY(100) NOT NULL, nonce2 VARBINARY(100) NOT NULL);")
        mycursor.execute("CREATE TABLE IF NOT EXISTS times(app VARCHAR(30) PRIMARY KEY, modified DATE NOT NULL);")
        mycursor.execute("CREATE TABLE IF NOT EXISTS login(hashval VARBINARY(100) NOT NULL, nonce VARBINARY(100) NOT NULL);")
        mydb.commit()
    except Exception as e:
        print("Error in creating tables,",e)

    login()

    