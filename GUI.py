from tkinter import *
from tkinter import ttk
from tkinter.filedialog import asksaveasfile 
from os import path
import srt

from tkinter import filedialog
from videoToText import Subtitle, Transcription

def browseFiles():
    fileName = filedialog.askopenfilename(initialdir = "/", 
                                          title = "Select a File", 
                                          filetypes = (("Video Files", 
                                                        "*.mp4*"), 
                                                       ("all files", 
                                                        "*.*")))
    entry.insert(END, fileName)

def saveSubtitle(videoFile, duration, thresh, language):
   files = [('Subtitle Files', '*.srt'), ('Text Document', '*.txt')]
   fileName = asksaveasfile(filetypes = files, defaultextension = files)
   if fileName:
       f = open(fileName.name, "w")
       f.write(srt.compose(Subtitle(videoFile, duration, thresh, language)))
       f.close()
       
def saveTranscription(videoFile):
   files = [('Text Document', '*.txt'), ('All Files', '*.*')]
   fileName = asksaveasfile(filetypes = files, defaultextension = files) 
   if fileName:
       f = open(fileName.name, "w")
       f.write(Transcription(videoFile))
       f.close()


window = Tk()
window.title('File Explorer') 
window.geometry("600x400") 
window.config(background = "dark red") 

upperFrame = Frame(window, bg = "dark green", bd = 5)
upperFrame.place(relx = 0.5, rely = 0.1, relwidth = 0.75, relheight = 0.1, anchor = "n")

entry = Entry(upperFrame, font=("Arial", 12))
entry.place(relwidth=0.8, relheight=1)

button = Button(upperFrame, text = "Browse", font = ("Arial", 12), bg = "white", fg = 'black', command = lambda:entry.insert(END, browseFiles()))
button.place(relx = 0.85, relheight = 1, relwidth = 0.15)


middleFrame = Frame(window, bg = "light grey", bd = 5)
middleFrame.place(relx = 0.5, rely = 0.5, relwidth = 0.9, relheight = 0.1, anchor = "n")

label1 = Label(middleFrame, text="Silent Duration (ms)", bg = "light grey")
label1.place(relx = 0.1, rely = 0.2, anchor = "n")

entrySilentDuration = Entry(middleFrame, font=("Arial", 12))
entrySilentDuration.place(relx = 0.21, rely = 0.2, relwidth = 0.1)

label2 = Label(middleFrame, text="Silent Threshold (dB)", bg = "light grey")
label2.place(relx = 0.48, rely = 0.2, anchor = "n")

entryThreshold = Entry(middleFrame, font=("Arial", 12))
entryThreshold.place(relx = 0.59, rely = 0.2, relwidth = 0.1)

label3 = Label(middleFrame, text="Language", bg = "light grey")
label3.place(relx = 0.8, rely = 0.2, anchor = "n")

entryLanguage = Entry(middleFrame, font=("Arial", 12))
entryLanguage.place(relx = 0.86, rely = 0.2, relwidth = 0.1)


bottomFrame = Frame(window, bg = "yellow", bd = 5)
bottomFrame.place(relx = 0.5, rely = 0.8, relwidth = 0.75, relheight = 0.1, anchor = "n")

button2 = Button(bottomFrame, text = "Generate Subtitle", font = ("Arial", 12), bg = "black", fg = "white" , command = lambda:saveSubtitle(entry.get(), entrySilentDuration.get(), entryThreshold.get(), entryLanguage.get()))
button2.place(relx = 0.55, relheight = 1)

button3 = Button(bottomFrame, text = "Generate Text File", font = ("Arial", 12), bg = "black", fg = "white" , command = lambda:saveTranscription(entry.get()))
button3.place(relx = 0.1, relheight = 1)


window.mainloop() 