## Sound2Text
# GUI Audio Transcriber

* This a simple and minimalistic desktop app that transcribes audio files using OpenAI's Whisper API. The script provides a graphical user interface to select an audio file and save the resulting transcription file
* Output Options = An .srt subtitle file chuncked and timestamped by word, including punctuation, which was a pain in the butt to sort out. 
* Users have the option to have line numbers included or excluded.

## Features

* Select local audio files (`.mp3`, `.wav`, etc.).
* Generates punctuated, timestamped transcriptions.
* Saves output in the standard `.srt` format (transcribe_logic_line_numbs.py)
* Saves output  `.srt` format, without line numbers (Useful for OpenShot) (transcribe_logic.py)
* Simple, minimalistic user interface.

## How to Use

1.  Ensure you have Python 3 installed.
2.  Install the required dependencies: `pip install -r requirements.txt`
3.  Set your OpenAI API key as an environment variable named `OPENAI_API_KEY`.
4.  Run the application: `python transcribe_gui.py`
* The GUI shows a checkbox that allows users to choose whether they want to exclude line numbers in their SRT output.
* The command line version supports the --no-line-numbers flag for the same functionality.

## Acknowledgements

* This tool is powered by the **OpenAI Whisper API**.
* The code for this project was developed with some assistance from Google's Gemini.
* Bruno's You Don't Have To - The short-form pod: sub-4-minutes of irreverent nonsense