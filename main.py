from flask import Flask, render_template, request, redirect, url_for
from flaskext.markdown import Markdown
import pickle
from os import path as os_path, mkdir as os_mkdir, remove as os_remove
from datetime import datetime
import sys, getopt
import boto3

app = Flask("Champagne")
Markdown(app)
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('notes')
noteList = []

print("Getting all notes from dynamodb")
noteList = table.scan()['Items']
print(noteList)


@app.route("/")
def home():
    return render_template("home.html", notes=noteList)

@app.route("/addNote")
def addNote():
    return render_template("noteForm.html", headerLabel="New Note", submitAction="createNote", cancelUrl=url_for('home'))

@app.route("/createNote", methods=["post"])
def createNote():
    # get next note id
    if len(noteList):
        idList = [ int(i['id']) for i in noteList ]
        noteId = str(max(idList)+1)
    else:
        noteId = "1"

    lastModifiedDate = datetime.now()
    lastModifiedDate = lastModifiedDate.strftime("%d-%b-%Y %H:%M:%S")

    noteTitle = request.form['noteTitle']
    noteMessage = request.form['noteMessage']

    note = {'id': noteId, 'title': noteTitle, 'lastModifiedDate': lastModifiedDate, 'message': noteMessage}

    print("Creating note")
    table.put_item(Item=note)

    # add metadata to list of notes for display on home page
    noteList.append({'id': noteId, 'title': noteTitle, 'lastModifiedDate': lastModifiedDate})


    return redirect(url_for('viewNote', noteId=noteId))

@app.route("/viewNote/<int:noteId>")
def viewNote(noteId):
    noteId = str(noteId)

    print("Getting note")
    note = table.get_item(Key={'id': noteId})['Item']

    return render_template("viewNote.html", note=note, submitAction="/saveNote")

@app.route("/editNote/<int:noteId>")
def editNote(noteId):
    noteId = str(noteId)

    note = table.get_item(Key={'id': noteId})['Item']

    cancelUrl = url_for('viewNote', noteId=noteId)
    return render_template("noteForm.html", headerLabel="Edit Note", note=note, submitAction="/saveNote", cancelUrl=cancelUrl)

@app.route("/saveNote", methods=["post"])
def saveNote():
    lastModifiedDate = datetime.now()
    lastModifiedDate = lastModifiedDate.strftime("%d-%b-%Y %H:%M:%S")

    noteId = str(int(request.form['noteId']))
    noteTitle = request.form['noteTitle']
    noteMessage = request.form['noteMessage']


    note = {'id': noteId, 'title': noteTitle, 'lastModifiedDate': lastModifiedDate, 'message': noteMessage}

    print("Saving note")
    table.put_item(Item=note)

    # remove the old version of the note from the list of note metadata and add the new version
    global noteList
    newNoteList = [ i for i in noteList if not (i['id'] == noteId) ]
    noteList = newNoteList

    # add metadata to list of notes for display on home page
    noteList.append({'id': noteId, 'title': noteTitle, 'lastModifiedDate': lastModifiedDate})

    return redirect(url_for('viewNote', noteId=noteId))

@app.route("/deleteNote/<int:noteId>")
def deleteNote(noteId):
    print("type of noteid")
    print(type(noteId))
    table.delete_item(Key={'id': str(noteId)})

    # remove the note from the list of note metadata
    global noteList
    newNoteList = [ i for i in noteList if not (i['id'] == str(noteId)) ]
    noteList = newNoteList


    return redirect("/")

if __name__ == "__main__":
    debug = False

    try:
        opts, args = getopt.getopt(sys.argv[1:], "h:p:", ["debug"])
    except getopt.GetoptError:
        print('usage: main.py [-h 0.0.0.0] [-p 5000] [--debug]')
        sys.exit(2)

    port = "5000"
    host = "0.0.0.0"
    print(opts)
    for opt, arg in opts:
        if opt == '-p':
            port = arg
        elif opt == '-h':
            host = arg
        elif opt == "--debug":
            debug = True

    app.run(host=host, port=port, debug=debug)

