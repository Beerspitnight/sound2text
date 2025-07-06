#!/usr/bin/env python3
"""
transcription_logic.py

This file contains the core logic for transcribing audio with Whisper.
It is imported by transcribe_gui.py.
"""
import argparse
import openai
import os
import sys

def get_openai_client():
    """Initialize and return OpenAI client with API key validation."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        sys.exit("Error: OPENAI_API_KEY environment variable not set.")
    return openai.OpenAI(api_key=api_key)

def srt_timestamp(seconds):
    """Converts seconds to a SubRip (SRT) timestamp format."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def create_punctuated_chunks(response, chunk_size=1):
    """
    Creates small, timestamped chunks while preserving punctuation by aligning
    the master word list with the punctuated segment list.
    """
    if not response.segments or not response.words:
        print("Warning: Transcription resulted in no segments or words. The audio file might be silent or empty.")
        return []

    # Get the two parallel lists from the API response
    segments = response.segments
    all_words = response.words
    
    word_index = 0  # A pointer to our position in the all_words list
    all_chunks = []

    for segment in segments:
        segment_text = segment.text.strip()
        
        # Manually collect the words from the master list that belong to this segment
        segment_words = []
        while word_index < len(all_words) and all_words[word_index].start <= segment.end:
            # Check if the current word from the master list is within this segment's time range
            if all_words[word_index].start >= segment.start:
                segment_words.append(all_words[word_index])
            word_index += 1

        if not segment_words:
            continue

        text_cursor = 0
        for i in range(0, len(segment_words), chunk_size):
            word_group = segment_words[i:i + chunk_size]
            
            start_time = word_group[0].start
            end_time = word_group[-1].end

            chunk_end_char_index = len(segment_text)
            
            if i + chunk_size < len(segment_words):
                next_word_obj = segment_words[i + chunk_size]
                try:
                    chunk_end_char_index = segment_text.index(next_word_obj.word, text_cursor)
                except ValueError:
                    pass
            
            chunk_text = segment_text[text_cursor:chunk_end_char_index].strip()
            text_cursor = chunk_end_char_index

            if chunk_text:
                all_chunks.append({
                    "start": srt_timestamp(start_time),
                    "end": srt_timestamp(end_time),
                    "text": chunk_text
                })

    return all_chunks

def transcribe_whisper(audio_path):
    """
    Transcribes the audio file and returns a list of small, punctuated word chunks.
    """
    client = get_openai_client()
    
    with open(audio_path, "rb") as audio_file:
        print("Sending audio to OpenAI Whisper API...")
        
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json",
            timestamp_granularities=["segment", "word"]
        )
        
        print("Transcription complete. Aligning punctuation...")
        return create_punctuated_chunks(response, chunk_size=1)


def transcribe_audio(input_file, output_file=None, include_line_numbers=True):
    """
    Handles the transcription process and writes the punctuated chunks to an SRT file.
    Returns the number of chunks created.
    
    Args:
        input_file: Path to the audio file to transcribe
        output_file: Path to the output SRT file (optional)
        include_line_numbers: Whether to include line numbers in SRT output (default: True)
    """
    chunks = transcribe_whisper(input_file)
    
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            if chunks:
                for i, chunk in enumerate(chunks):
                    if include_line_numbers:
                        f.write(f"{i + 1}\n")
                    f.write(f"{chunk['start']} --> {chunk['end']}\n")
                    f.write(f"{chunk['text']}\n\n")
    
    return len(chunks)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transcribe audio using OpenAI Whisper with advanced punctuation alignment.")
    parser.add_argument("input_file", help="Path to input audio file (e.g., input.mp3).")
    parser.add_argument("-o", "--output", help="Path to output SRT file (e.g., output.srt).")
    parser.add_argument("--no-line-numbers", action="store_true", help="Exclude line numbers from SRT output.")
    args = parser.parse_args()

    include_line_numbers = not args.no_line_numbers
    transcribe_audio(args.input_file, args.output, include_line_numbers)