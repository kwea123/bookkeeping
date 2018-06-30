from flask import Flask, render_template, flash, Response, render_template_string, stream_with_context, request
import pandas as pd
# import tempfile
# from gtts import gTTS
# import time
# import wave
# from pygame import mixer
import re
# import sys
# import numpy as np
from datetime import datetime, timedelta
import os
from utils import *

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'C:/Users/kwea123/Downloads/MyProject-e85ed8c91456.json'

if os.path.isfile('data.csv'):
    df = pd.read_csv('data.csv')
    df['日期'] = pd.to_datetime(df['日期'])
    df['刪除'] = "<input type='checkbox'>"
else:
    df = pd.DataFrame(columns=['日期', '名稱', '價錢', '刪除'])
# df = df.append({'日期': datetime.strptime('2018-06-30', "%Y-%m-%d").date(), '名稱': 'text', '價錢': 12, '刪除': '<input type="checkbox">'}, ignore_index=True)
# df = df.append({'日期': datetime.strptime('2018-07-01', "%Y-%m-%d").date(), '名稱': 'text', '價錢': 12, '刪除': '<input type="checkbox">'}, ignore_index=True)

# def speak(sentence, lang='zh-tw'):
#     with tempfile.NamedTemporaryFile(delete=True) as fp:
#         tts =gTTS(text=sentence, lang=lang)
#         tts.save(fp.name+'.mp3')
#         mixer.music.load(fp.name+'.mp3')
#         mixer.music.play()
#     return sentence

def date_of_last_day_of_month(date):
    next_month = date.replace(day=28) + timedelta(days=4)
    return next_month - timedelta(days=next_month.day)

def df_of_this_moth(df):
    today = datetime.now().date()
    df_this_month = df[df['日期']<=date_of_last_day_of_month(today)]
    return {'data':df_this_month.to_html(escape=False), 'sum':sum(df_this_month['價錢']), 'size':len(df_this_month), 'date':today}

def df_of_date(df, date):
    today = datetime.now().date()
    df_date = df[df['日期']==date]
    return {'data':df_date.to_html(escape=False), 'sum':sum(df_date['價錢']), 'size':len(df_date), 'date': today}

app = Flask(__name__)

@app.route('/')
def result(): # print the whole dataframe
    today = datetime.now().date()
    return render_template('index.html', **df_of_this_moth(df))

@app.route("/", methods=['POST'])
def process():
    today = datetime.now().date()
    if request.form['function']=='delete':
        to_delete = list(map(int, request.form['value'].split(',')))
        df.drop(to_delete, inplace=True)
        df.reset_index(drop=True, inplace=True)
        return render_template('index.html', **df_of_date(df, today))
    if request.form['function']=='save':
        df[df.columns[:-1]].to_csv('data.csv', index=None)
        return render_template('index.html', warning='已儲存至 data.csv ！', **df_of_date(df, today))
    if request.form['function']=='view_date':
        date = datetime.strptime(request.form['date'], "%Y-%m-%d").date()
        return render_template('index.html', **df_of_date(df, date))
    if request.form['function']=='view_month':
        return render_template('index.html', **df_of_this_moth(df))
    
    transcripts = []
    def generate(transcripts): # max 65 seconds
        global df
        language_code = 'zh-tw'
        client = speech.SpeechClient()
        config = types.RecognitionConfig(
            encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=RATE,
            language_code=language_code)
        streaming_config = types.StreamingRecognitionConfig(
            config=config,
            interim_results=True)
        
        with MicrophoneStream(RATE, CHUNK) as stream:
            audio_generator = stream.generator()
            requests = (types.StreamingRecognizeRequest(audio_content=content)
                        for content in audio_generator)
            responses = client.streaming_recognize(streaming_config, requests)
            for response in responses:
                if not response.results:
                    continue

                result = response.results[0]
                if not result.alternatives:
                    continue

                transcript = result.alternatives[0].transcript
                
                if '停止' in transcript or '停'==transcript or '結束'==transcript:
                    # speak('現在停止')
                    transcript = ''.join(transcripts)
                    objs = transcript.split('元')[:-1]
                    for i in range(len(objs)):
                        objs[i] = str(i+1)+'.'+objs[i]+'元'

                    for obj in objs:
                        obj = obj.split('.')[1]
                        text = re.sub('\d+元$','',obj)
                        number = int(obj.replace(text, '')[:-1])
                        df = df.append({'日期': today, '名稱': text, '價錢': number, '刪除': "<input type='checkbox'>"}, ignore_index=True)
                        df['日期'] = pd.to_datetime(df['日期'])
                    
                    yield render_template('index.html', **df_of_date(df, today))
                    return
                
                if result.is_final:
                    template = '<p class="transcript" style="margin:0">{{ transcript }}</p>'
                    context = {'transcript':transcript}
                    # if '元' in transcript:
                    transcripts += [transcript]
                    yield render_template_string(template, **context) # final result that is printed
                    
    return Response(stream_with_context(generate(transcripts)))

if __name__ == '__main__':
    app.run(debug=True)