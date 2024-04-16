import pandas as pd
from youtube_transcript_api import YouTubeTranscriptApi as YTapi
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from googletrans import Translator, constants
from pprint import pprint
from pytube import YouTube
from flask import Flask, request, send_from_directory, render_template, jsonify, Response
from gtts import gTTS
from IPython.display import Audio
from flask_cors import CORS, cross_origin
import os

app = Flask(__name__)
app.config['STATIC_FOLDER'] = 'static'

def videoID(link):
    video_id = link.split("=")[1]
    return video_id

def GetTranscript(video_id):
    try:
        transcript = YTapi.get_transcript(video_id)
        FinalTranscript = ' '.join([i['text'] for i in transcript])
    except Exception as e:
        print(e)

    return FinalTranscript

def summarize(toenizer, model, text):

    """
    Function to summarize the text(transcript)
    """
    inputs = toenizer(text,
                    max_length=1024,
                    truncation=True,
                    return_tensors="pt")

    summary_ids = model.generate(inputs["input_ids"])
    summary = toenizer.batch_decode(summary_ids,
                                  skip_special_tokens=True,
                                  clean_up_tokenization_spaces=False)
    return summary

youtube_link = "https://www.youtube.com/watch?v=A4OmtyaBHFE"

@app.route('/api/healthy', methods=['GET'])
@cross_origin(support_credentials=True)
def health_check():
  return "I'm healthy"

# @app.route('/get_summary', methods=['GET'])
def get_summary(url, lang):
  youtube_link = url
  id = videoID(youtube_link)
  transcript_en = GetTranscript(id)
  transcript_list  = YTapi.list_transcripts(id)
  
  for transcript in transcript_list:
    ln = transcript.language
    check = transcript.is_translatable
  for transcript in transcript_list:
    available_ln = transcript.translation_languages
    dataFrame=pd.DataFrame(available_ln)

  Language=lang
  filtered_df = dataFrame[dataFrame['language'].str.contains(Language)]
  #print(filtered_df)
  Code=filtered_df.language_code
  # drop the index columns}
  p=Code.reset_index(drop=True, inplace=False)
  print(p[0])
  code = str(p[0])
  #transcript_en = ' '.join([i['text'] for i in transcript.translate(code).fetch()])

  checkpoint3 = "sshleifer/distilbart-cnn-12-6"
  tokenizer3 = AutoTokenizer.from_pretrained(checkpoint3)
  model3 = AutoModelForSeq2SeqLM.from_pretrained(checkpoint3)

  Summary = summarize(tokenizer3, model3, transcript_en)

  # init the Google API translator
  translator = Translator()
  # translate a spanish text to arabic for instance
  translation1 = translator.translate(Summary[0], dest=code).text

  language = code
  myobj = gTTS(text=translation1, lang=language, slow=False)
  myobj.save("static/summary.mp3")
  os.system("mpg321 static/summary.mp3")

  return translation1
  


@app.route("/", methods=["GET", "POST"])  # Allow both GET and POST requests
def home():
  if request.method == "GET":
    # Display the form (GET request)
    return render_template("index.html")  # "form.html" contains the HTML form
  else:
    # Process form submission (POST request)
    url = request.form["url"]  # Access form data by name attribute
    lang = request.form["lang"]
    if (url != '') and (lang != ''):
      summary = get_summary(url, lang)
      filename = "static/summary.mp3"
      # audio_file = open(filename, "rb")
      # data = {"audio_data": audio_file.read(), "summary": summary}
      # response = jsonify(data)
      # response.headers.set('Content-Type', 'application/json')
      # return send_from_directory("./",filename, as_attachment=True)
      return render_template("output.html", summary=summary)
    return f"Invalid Input Parameters!"


@app.route("/stream_audio")
def stream_audio():
    audio_file = open("static/summary.mp3", "rb")  # Replace with your path
    response = Response(audio_file, mimetype="audio/mpeg")
    response.headers.set('Content-Disposition', 'attachment', filename='static/summary.mp3')
    return response

@app.route("/download_audio")
def download_audio():
    audio_path = "summary.mp3"  # Replace with your path
    return send_from_directory( app.config['STATIC_FOLDER'],audio_path, mimetype="audio/mpeg", as_attachment=True)
  


if __name__ == '__main__':
  app.run(debug=True)
  # gunicorn.run(app, host="0.0.0.0", port=8000, workers=1)
