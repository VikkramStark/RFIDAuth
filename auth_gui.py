import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk
from cryptography.fernet import Fernet
import os
import RPi.GPIO as GPIO
import mfrc522 as MFRC522

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
    with open("key.txt", "wb") as f:
        f.write(key)
    print("Key Successfully Generated!")

def create_encrypted_file(filename):
    key = open("key.txt", "rb").read()
    with open(filename, "r") as f:
        data = f.read().encode()
    fernet = Fernet(key)
    enc_data = fernet.encrypt(data)
    with open(filename, "wb") as f:
        f.write(enc_data)
        f.flush()
    print(f"Encrypted File Created! for {filename}")

def access_files(username, password):
    if username != None and password != None:
        with open("key.txt", "rb") as f:
            key = f.read()
        file = input("Enter FileName:")
        with open(file, "rb") as f:
            enc_data = f.read()
        fernet = Fernet(key)
        data = fernet.decrypt(enc_data).decode()
        with open("decrypted.txt", "w") as out:
            out.write(data)
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
    cursor.execute('SELECT * FROM cards WHERE uid = ?', (card_uid,))
    result = cursor.fetchone()

    if result:
        messagebox.showinfo("Info", "Card already exists in the database.")
    else:
        cursor.execute('INSERT INTO cards (uid, username, password) VALUES (?, ?, ?)',
                       (card_uid, 'default_user', 'default_password'))
        conn.commit()
        messagebox.showinfo("Info", "Card added to the database.")

    conn.close()

# GUI Setup
class RFIDApp:
    def __init__(self, master):
        self.master = master
        master.title("RFID Authentication System")
        master.geometry("600x300") 
        master.minsize(600, 300)

        # Configure ttk style
        style = ttk.Style()
        style.theme_use("clam")  # Use a theme of your choice

        # Set background color
        master.configure(bg="#093145") #f2f2f2

        # Heading
        self.heading_label = ttk.Label(master, text="RFIDAuth", background="#093145", foreground="#ebc944", font=("Arial", 24, "bold"))
        self.heading_label.pack(pady=20)

        # Custom button style
        style.configure("TButton", background="#ebc944", foreground="#093145", font=("Arial", 12, "bold"))
        style.map("TButton", background=[("active", "#d1b547")])

        self.add_card_button = ttk.Button(master, text="Add New RFID", command=self.add_card)
        self.add_card_button.pack(pady=10)  

        self.authenticate_button = ttk.Button(master, text="Authenticate User", command=self.authenticate)
        self.authenticate_button.pack(pady=10)

        self.quit_button = ttk.Button(master, text="Quit", command=master.quit)
        self.quit_button.pack(pady=20)

    def add_card(self):
        add_card_to_database()

    def authenticate(self):
        username, password = authenticate()
        access_files(username, password)


if __name__ == '__main__':
    create_database()

    root = tk.Tk()
    app = RFIDApp(root)
    root.mainloop()
