## Sound2Text
# GUI Audio Transcriber

This a simple and minimalistic desktop app that transcribes audio files using OpenAI's Whisper API. The script provides a graphical user interface to select an audio file and save the resulting transcription file
Output = An .srt-light subtitle file chuncked and timestamped by word, including punctuation, which was a pain in the butt to sort out.

## Features

* Select local audio files (`.mp3`, `.wav`, etc.).
* Generates punctuated, timestamped transcriptions.
* Saves output in the standard `.srt` format.
* Simple, minimalistic user interface.

## How to Use

1.  Ensure you have Python 3 installed.
2.  Install the required library: `pip install openai`
3.  Set your OpenAI API key as an environment variable named `OPENAI_API_KEY`.
4.  Run the application: `python transcribe_gui.py`

## Acknowledgements

* This tool is powered by the **OpenAI Whisper API**.
* The code for this project was developed with some assistance from Google's Gemini.