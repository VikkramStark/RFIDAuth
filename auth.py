import sqlite3
import RPi.GPIO as GPIO
import mfrc522 as MFRC522
import os
from cryptography.fernet import Fernet

fernet = None

# Database setup
DB_FILE = 'authentication.db'

def create_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Create a table to store RFID card data
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY,
            uid TEXT,
            username TEXT,
            password TEXT
        )
    ''')

    conn.commit()
    conn.close()



# RFID reader setup
reader = MFRC522.MFRC522()

def create_key():
   key = Fernet.generate_key()
   f = open("key.txt","wb")
   f.write(key)
   print("Key Successfully Generated!")

def create_encrypted_file(filename):
   key = open("key.txt","rb").read()
   f = open(filename, "r")
   data = f.read().encode()
   f.close()
   fernet = Fernet(key)
   enc_data = fernet.encrypt(data)
   f = open(filename,"wb")
   f.write(enc_data)
   f.flush()
   print(f"Encrypted File Created! for {filename}")

def access_files(username, password):
   if username!=None and password!=None:
      f = open("key.txt", "rb")
      key = f.read()
      f.close()
      fernet = Fernet(key)
      file = input("Enter FileName:")
      f = open(file, "rb")
      enc_data = f.read()
      data = fernet.decrypt(enc_data).decode()
      out = open("decrypted.txt", "w")
      out.write(data)
      out.close()
      print("File Decrypted and Ready for Access!")
   else:
      print("Authentication Failed..\n Invalid Credentials!")

def read_rfid():
    print("Hold an RFID card near the reader")
    while True:
        (status, TagType) = reader.MFRC522_Request(reader.PICC_REQIDL)
        if status == reader.MI_OK:
            print("Card detected")

            (status, uid) = reader.MFRC522_Anticoll()
            if status == reader.MI_OK:
                card_uid = ''.join([str(x) for x in uid])
                return card_uid

# Authentication function
def authenticate():
    card_uid = read_rfid()

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Check if the card UID exists in the database
    cursor.execute('SELECT * FROM cards WHERE uid = ?', (card_uid,))
    result = cursor.fetchone()

    if result:
        username, password = result[2], result[3]
        conn.close()
        return username, password
    else:
        conn.close()
        return None, None

# Add RFID card to the database
def add_card_to_database():
    card_uid = read_rfid()

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Check if the card UID already exists in the database
    cursor.execute('SELECT * FROM cards WHERE uid = ?', (card_uid,))
    result = cursor.fetchone()

    if result:
        print("Card already exists in the database.")
    else:
        # Add the new card to the database with a default username and password
        cursor.execute('INSERT INTO cards (uid, username, password) VALUES (?, ?, ?)',
                       (card_uid, 'default_user', 'default_password'))
        conn.commit()
        print("Card added to the database.")

    conn.close()

if __name__ == '__main__': 
    create_database()

    while True:
        print("1) Add New RFID")
        print("2) Authenticate User")
        print("3) Quit")
        op = input("Enter a option (q to quit)")
        if op == "3" or op == 'q':
            print("Quitting...")
            break
        elif op == "1":
            add_card_to_database()

        elif op == "2":
            username, password = authenticate()
            access_files(username, password)
        else:
            print("\nInvalid Input!, Retry...\n") 
    # Uncomment the next line to add a new card to the database
    #add_card_to_database()

    #username, password = authenticate()
    #access_files(username, password)