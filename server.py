from flask import Flask, render_template_string, render_template, Response, request, redirect, url_for
from cryptography.fernet import Fernet
import base64
import pymongo
import random
import os
import ssl

# url if you're using a domain, else leave as localhost
WEBSITE_URL = "localhost"

# generate key on launch for privacy purposes
key = Fernet.generate_key()
f = Fernet(key)

app = Flask(__name__)
myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["priv8notes"]
noteDB = mydb["notes"]

class privateNote:
    def __init__(self, note):
        self.note = note
        self.id = ''.join([random.choice(string.ascii_letters + string.digits) for i in range(32)])


def findNote(noteId):
    myquery = { "_id": noteId }
    mydoc = noteDB.find(myquery)
    if mydoc:
        return True
    else:
        return False

def openNote(noteId):
    found = False
    foundNote = privateNote('')
    for n in notes:
        if noteId == n.id:
            found = True
            foundNote = n
            notes.remove(n)
            break

    if found:
        return foundNote.note

    else:
        return "not found"


@app.route('/')
def index():
    return render_template('views/index.html')

@app.route('/createNote', methods=["GET", "POST"])
def createNote():
    if request.method == 'POST':
        n = request.form['note'].encode()
        if len(n) > 0:
            encrypted = f.encrypt(n)
            newNote = privateNote(encrypted)
            noteDict = {"_id": newNote.id, "note": newNote.note}
            noteDB.insert_one(noteDict)
            return render_template('views/success.html', link=f'{WEBSITE_URL}/read?id={newNote.id}')

    if request.method == 'GET':
        return redirect('/')


@app.route('/read', methods=["GET"])
def read():
    if request.method == 'GET':
        noteId = request.args.get('id')
        found = findNote(noteId)
        if found:
            return render_template('views/read.html', id=noteId)

        else:
            return render_template('views/error.html', err='note not found.')

@app.route('/readNote', methods=["POST"])
def readNote():
    if request.method == 'POST':
        noteId = request.args.get('id')
        myquery = {'_id': noteId}
        mydoc = noteDB.find(myquery)
        try:
            decrypted = f.decrypt(mydoc[0]['note']).decode()
            noteDB.delete_one(myquery)
            return render_template('views/readNote.html', msg=decrypted)
        except:
            return render_template('views/error.html', err='could not find a note with that id.')

@app.errorhandler(404)
def page_not_found(e):
    return redirect('/')

if __name__ == '__main__':
    app.run(port=80)
