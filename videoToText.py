import speech_recognition as sr
from os import path
import moviepy.editor as mp
import datetime as dt
import pydub
import srt
from punctuator import Punctuator

def videoToWav(videoFile):
    videoClip = mp.VideoFileClip(videoFile)
    videoClip.audio.write_audiofile(r"Extracted.wav")


def Subtitle(videoFile, duration, thresh, language1):
    videoToWav(videoFile)

    r = sr.Recognizer()
    
    myaudio = pydub.AudioSegment.from_wav('Extracted.wav')
    speak = pydub.silence.detect_nonsilent(myaudio, min_silence_len = int(duration), silence_thresh = int(thresh))
    speak = [(int(start/1000), int(stop/1000)) for start, stop in speak]
    
    speakClear = []
    skip = []
    for idx, val in enumerate(speak):
        if idx not in skip:
            if val[1] - val[0] < 3:
                try:
                    speakClear.append(val[0], speak[idx + 1][1])
                    skip.append(idx + 1)
                except:
                    speakClear.append(val)
            
            else:
                speakClear.append(val)
    
    
    subs = []
    timer = 0
    
    with sr.AudioFile("Extracted.wav") as source:
        for i, v in enumerate(speakClear):
            audioText = r.record(source, duration = v[1] - timer)
            
            try:
                word = r.recognize_google(audioText, language = language1)
                subs.append(srt.Subtitle(index = (i+1), start=dt.timedelta(seconds = v[0]), end = dt.timedelta(seconds=v[1]), content = word))
                timer += (v[1]-timer)
                print(v[1])
            except sr.UnknownValueError:
                print("Something Wrong")
            except Exception as e:
                print(e)
    print("Process Finished.")
                
    return subs
    

def Transcription(videoFile):
    try:
        videoToWav(videoFile)
        
        r = sr.Recognizer()
        audio_clip = sr.AudioFile("{}".format("extracted.wav"))
        with audio_clip as source:
            audio_file = r.record(source)
        print("Please wait ...")
        resultTemp = r.recognize_google(audio_file, language = "en-EN")
        punctuator = Punctuator('en')
        resultTemp = punctuator.punct([resultTemp], batch_size = 32)
        empty = " "
        resultFinal3 = empty.join(resultTemp)
        
        print("Speech to text conversion successfull.")
        
        return resultFinal3
    except Exception as e:
        print("Attempt failed -- ", e)