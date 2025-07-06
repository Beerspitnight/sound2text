# transcribe_gui.py

import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import os

try:
    from transcription_logic import transcribe_audio
except ImportError:
    messagebox.showerror(
        "Error", 
        "Could not find 'transcription_logic.py'.\n"
        "Please make sure the original script has been renamed and is in the same folder as this GUI."
    )
    exit()

class TranscriptionApp:
    def __init__(self, root_window):
        self.root = root_window
        self.root.title("sound2text - Whisper Transcription")
        self.root.eval('tk::PlaceWindow . center')
        self.audio_file_path = None
        
        # Main frame
        self.frame = tk.Frame(root_window, padx=15, pady=15)
        self.frame.pack(padx=10, pady=10, fill=tk.X)
        
        # File selection
        self.select_button = tk.Button(self.frame, text="1. Select Audio File", command=self.select_file)
        self.select_button.pack(fill=tk.X, pady=(0, 5))
        self.file_label = tk.Label(self.frame, text="No file selected", fg="grey", wraplength=400, justify=tk.LEFT)
        self.file_label.pack(fill=tk.X, pady=5)
        
        # Options frame
        self.options_frame = tk.Frame(self.frame)
        self.options_frame.pack(fill=tk.X, pady=10)
        
        # Line numbers checkbox
        self.include_line_numbers = tk.BooleanVar(value=True)
        self.line_numbers_checkbox = tk.Checkbutton(
            self.options_frame, 
            text="Include line numbers in SRT file", 
            variable=self.include_line_numbers
        )
        self.line_numbers_checkbox.pack(anchor=tk.W)
        
        # Transcription button
        self.transcribe_button = tk.Button(self.frame, text="2. Transcribe and Save", command=self.start_transcription_thread)
        self.transcribe_button.pack(fill=tk.X, pady=10)
        self.status_label = tk.Label(self.frame, text="Welcome! Please select a file.", fg="blue")
        self.status_label.pack(fill=tk.X, pady=5)
        
    def select_file(self):
        """Opens a file dialog to let the user pick an audio file."""
        path = filedialog.askopenfilename(
            title="Select an audio file",
            filetypes=(("Audio Files", "*.mp3 *.wav *.m4a *.flac"), ("All files", "*.*"))
        )
        if path:
            self.audio_file_path = path
            self.file_label.config(text=os.path.basename(path), fg="black")
            self.status_label.config(text="File selected. Ready to transcribe.", fg="blue")

    def start_transcription_thread(self):
        """Starts the transcription process in a separate thread to prevent the GUI from freezing."""
        if not self.audio_file_path:
            messagebox.showwarning("Warning", "Please select an audio file first.")
            return

        output_path = filedialog.asksaveasfilename(
            title="Save transcription as...",
            defaultextension=".srt",
            filetypes=(("SRT Subtitles", "*.srt"), ("All files", "*.*"))
        )
        
        if not output_path:
            return
            
        transcription_thread = threading.Thread(
            target=self.run_transcription,
            args=(output_path,)
        )
        transcription_thread.start()
        
        self.status_label.config(text="Transcribing... This may take a moment.", fg="orange")
        self.select_button.config(state=tk.DISABLED)
        self.transcribe_button.config(state=tk.DISABLED)
        self.line_numbers_checkbox.config(state=tk.DISABLED)

    def run_transcription(self, output_path):
        """The function that runs in the background thread."""
        try:
            # Get the line numbers option from the checkbox
            include_line_numbers = self.include_line_numbers.get()
            
            # MODIFICATION: The logic function now returns the number of chunks.
            chunk_count = transcribe_audio(self.audio_file_path, output_path, include_line_numbers)
            # We pass this number to the success function.
            self.root.after(0, self.on_transcription_success, output_path, chunk_count)
        except Exception as e:
            self.root.after(0, self.on_transcription_error, e)

    def on_transcription_success(self, output_path, chunk_count):
        """Updates the GUI after a successful transcription."""
        # MODIFICATION: Check if the transcription was empty.
        if chunk_count > 0:
            messagebox.showinfo("Success", f"Transcription complete!\nFile saved to: {os.path.basename(output_path)}")
            self.status_label.config(text="Success! Ready for next file.", fg="green")
        else:
            # If the transcription produced 0 chunks, show a warning.
            messagebox.showwarning("Warning", "Transcription finished, but no content was generated.\nThe audio file may be silent, empty, or in an unsupported format.")
            self.status_label.config(text="Finished with no content.", fg="orange")
            
        self.select_button.config(state=tk.NORMAL)
        self.transcribe_button.config(state=tk.NORMAL)
        self.line_numbers_checkbox.config(state=tk.NORMAL)

    def on_transcription_error(self, error):
        """Updates the GUI after a failed transcription."""
        messagebox.showerror("Transcription Failed", f"An error occurred:\n{error}")
        self.status_label.config(text="An error occurred. Please try again.", fg="red")
        self.select_button.config(state=tk.NORMAL)
        self.transcribe_button.config(state=tk.NORMAL)
        self.line_numbers_checkbox.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = TranscriptionApp(root)
    root.mainloop()