import re
import sys
from datetime import datetime, timedelta
import os

def parse_time(time_str):
    """
    Parse SRT timestamp format (HH:MM:SS,mmm) to datetime object
    """
    try:
        time_str = time_str.replace(',', '.')
        return datetime.strptime(time_str, '%H:%M:%S.%f')
    except ValueError as e:
        raise ValueError(f"Invalid time format '{time_str}': {e}") from e


def format_time(dt):
    """
    Format datetime object back to SRT timestamp format (HH:MM:SS,mmm)
    """
    return dt.strftime('%H:%M:%S,%f')[:-3]


# Configuration constants
MIN_DURATION_MS = 100
ADJUSTMENT_MS = 150
MIN_ENTRY_DURATION_MS = 100
MIN_GAP_MS = 10


def load_srt_file(filename):
    """
    Load and validate SRT file content.
    
    Args:
        filename: Path to SRT file
        
    Returns:
        str: File content
        
    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If file can't be read
        UnicodeDecodeError: If file encoding is invalid
        ValueError: If file is empty
    """
    if not filename:
        raise ValueError("No filename provided")
    
    if not filename.lower().endswith('.srt'):
        print("Warning: File doesn't have .srt extension. Proceeding anyway...")
    
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if not content.strip():
        raise ValueError("File is empty")
    
    return content


def parse_srt_entries(content):
    """
    Parse SRT file content into structured entries.
    
    Args:
        content: Raw SRT file content
        
    Returns:
        list: Parsed SRT entries with number, start_time, end_time, text
    """
    entries = content.strip().split('\n\n')
    parsed_entries = []
    
    # Try standard SRT format first (with sequence numbers)
    entry_regex = re.compile(r'(\d+)\n([\d:,]+)\s-->\s([\d:,]+)\n([\s\S]+)', re.DOTALL)
    # Alternative format without sequence numbers
    entry_regex_alt = re.compile(r'([\d:,]+)\s-->\s([\d:,]+)\n([\s\S]+)', re.DOTALL)
    
    for i, entry in enumerate(entries):
        if match := entry_regex.match(entry):
            # Standard format with sequence number
            try:
                start_time = parse_time(match[2])
                end_time = parse_time(match[3])
                
                # Validate chronological order
                if start_time >= end_time:
                    print(f"Warning: Entry {i+1} has invalid time range (start >= end)")
                    continue
                
                parsed_entries.append({
                    'number': int(match[1]),
                    'start_time': start_time,
                    'end_time': end_time,
                    'text': match[4].strip(),
                })
            except ValueError as e:
                print(f"Warning: Skipping malformed entry {i+1}: {e}")
                continue
        elif match := entry_regex_alt.match(entry):
            # Alternative format without sequence number
            try:
                start_time = parse_time(match[1])
                end_time = parse_time(match[2])
                
                # Validate chronological order
                if start_time >= end_time:
                    print(f"Warning: Entry {i+1} has invalid time range (start >= end)")
                    continue
                
                parsed_entries.append({
                    'number': i + 1,  # Generate sequence number
                    'start_time': start_time,
                    'end_time': end_time,
                    'text': match[3].strip(),
                })
            except ValueError as e:
                print(f"Warning: Skipping malformed entry {i+1}: {e}")
                continue
        else:
            print(f"Warning: Skipping malformed entry {i+1}: doesn't match expected format")
    
    return parsed_entries


def write_srt_file(entries, filename):
    """
    Write SRT entries to file.
    
    Args:
        entries: List of SRT entry dictionaries
        filename: Output filename
    """
    with open(filename, 'w', encoding='utf-8') as f:
        for entry in entries:
            f.write(f"{entry['number']}\n")
            f.write(f"{format_time(entry['start_time'])} --> {format_time(entry['end_time'])}\n")
            f.write(f"{entry['text']}\n\n")


def adjust_srt_file(input_filename):
    """
    Analyzes an SRT file and adjusts timestamps for entries with a duration
    less than a specified threshold. Prints a report of all changes.
    
    Args:
        input_filename: Path to input SRT file
    """
    try:
        content = load_srt_file(input_filename)
        parsed_entries = parse_srt_entries(content)

        if not parsed_entries:
            print("No valid entries found in the file.")
            return

        # Validate chronological order across entries
        for i in range(len(parsed_entries) - 1):
            if parsed_entries[i]['end_time'] > parsed_entries[i + 1]['start_time']:
                print(f"Warning: Overlapping timestamps between entries {i+1} and {i+2}")

    except (FileNotFoundError, PermissionError, ValueError) as e:
        print(f"Error: {e}")
        return
    except Exception as e:
        print(f"Unexpected error reading file: {e}")
        return

    # Adjust short duration entries
    modification_reports = adjust_short_durations(parsed_entries)

    # Write the adjusted SRT file
    base, ext = os.path.splitext(input_filename)
    output_filename = f"{base}_adjusted{ext}"
    try:
        write_srt_file(parsed_entries, output_filename)
    except OSError as e:
        print(f"Error writing output file: {e}")
        return
    except Exception as e:
        print(f"Unexpected error writing file: {e}")
        return

    # Print the final report
    print("\n--- Modification Report ---")
    if modification_reports:
        print(f"Total modifications made: {len(modification_reports)}")
        for report in modification_reports:
            print(report)
    else:
        print("No modifications were needed.")
    print("-------------------------\n")
    print(f"Adjustment complete. New file saved as '{output_filename}'")


def adjust_short_durations(parsed_entries):
    """
    Adjust entries with duration less than MIN_DURATION_MS.
    
    Args:
        parsed_entries: List of SRT entry dictionaries
        
    Returns:
        list: Modification reports
    """
    modification_reports = []
    
    for idx, entry in enumerate(parsed_entries):
        duration_ms = (entry['end_time'] - entry['start_time']).total_seconds() * 1000
        
        if duration_ms < MIN_DURATION_MS:
            old_duration = duration_ms
            
            if idx == 0:
                # First entry: extend end time safely
                needed_ms = MIN_DURATION_MS - duration_ms
                if idx + 1 < len(parsed_entries):
                    next_start = parsed_entries[idx + 1]['start_time']
                    max_extend = (next_start - entry['end_time']).total_seconds() * 1000 - MIN_GAP_MS
                    extend_ms = min(needed_ms, max(0, max_extend))
                    entry['end_time'] += timedelta(milliseconds=extend_ms)
                else:
                    entry['end_time'] += timedelta(milliseconds=needed_ms)
                    
            elif idx == len(parsed_entries) - 1:
                # Last entry: shift start time safely
                needed_ms = MIN_DURATION_MS - duration_ms
                if idx > 0:
                    prev_end = parsed_entries[idx - 1]['end_time']
                    max_shift = (entry['start_time'] - prev_end).total_seconds() * 1000 - MIN_GAP_MS
                    shift_ms = min(needed_ms, max(0, max_shift))
                    entry['start_time'] -= timedelta(milliseconds=shift_ms)
                else:
                    entry['start_time'] -= timedelta(milliseconds=needed_ms)
                    
            else:
                # Middle entry: use safe borrowing
                adjust_middle_entry_safely(parsed_entries, idx)
            
            # Create modification report
            new_duration_ms = (entry['end_time'] - entry['start_time']).total_seconds() * 1000
            report = (
                f"  - Entry {entry['number']} ('{entry['text'][:30]}...'): "
                f"Duration {int(old_duration)}ms → {int(new_duration_ms)}ms"
            )
            modification_reports.append(report)
    
    return modification_reports


def adjust_middle_entry_safely(parsed_entries, idx):
    """
    Safely adjust a middle entry by borrowing time from neighbors.
    
    Args:
        parsed_entries: List of SRT entry dictionaries
        idx: Index of entry to adjust
    """
    prev_entry = parsed_entries[idx - 1]
    curr_entry = parsed_entries[idx]
    next_entry = parsed_entries[idx + 1]
    
    needed_ms = MIN_DURATION_MS - (curr_entry['end_time'] - curr_entry['start_time']).total_seconds() * 1000
    
    # Calculate safe borrowing from previous entry
    prev_duration = (prev_entry['end_time'] - prev_entry['start_time']).total_seconds() * 1000
    prev_available = max(0, prev_duration - MIN_ENTRY_DURATION_MS)
    prev_borrow = min(needed_ms / 2, prev_available)
    
    # Calculate safe extension into gap
    gap_to_next = (next_entry['start_time'] - curr_entry['end_time']).total_seconds() * 1000
    next_available = max(0, gap_to_next - MIN_GAP_MS)
    extend_amount = min(needed_ms / 2, next_available)
    
    # Apply adjustments if they help
    if prev_borrow > 0:
        prev_entry['end_time'] -= timedelta(milliseconds=prev_borrow)
        curr_entry['start_time'] -= timedelta(milliseconds=prev_borrow)
    
    if extend_amount > 0:
        curr_entry['end_time'] += timedelta(milliseconds=extend_amount)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 adjust_srt.py <your_srt_file.srt>")
    else:
        adjust_srt_file(sys.argv[1])