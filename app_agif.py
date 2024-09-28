import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, UnidentifiedImageError
from pydub import AudioSegment
import struct
import io
import pygame

# Define colors
LIGHT_PINK = "#FFB6C1"  # Light Pink
PAPYRUS_YELLOW = "#FAEBD7"  # Papyrus Yellow

# Utility functions for creating the AGIF file
def get_gif_frames(gif_path):
    gif = Image.open(gif_path)
    frames = []
    try:
        while True:
            # Save the frame with higher compression
            frame_io = io.BytesIO()
            gif.save(frame_io, format='PNG', optimize=True, compress_level=9)
            frames.append(frame_io.getvalue())
            gif.seek(gif.tell() + 1)
    except EOFError:
        pass
    return frames

def get_mp3_data(mp3_path, bitrate=64):
    audio = AudioSegment.from_file(mp3_path, format="mp3")
    mp3_buffer = io.BytesIO()
    audio.export(mp3_buffer, format="mp3", bitrate=f"{bitrate}k")  # Reduce bitrate
    return mp3_buffer.getvalue(), audio.frame_rate, audio.channels, audio.sample_width

def create_agif(gif_path, mp3_path, output_path):
    frames = get_gif_frames(gif_path)
    mp3_data, sample_rate, channels, sample_width = get_mp3_data(mp3_path)

    agif_header = struct.pack(
        '<4sBBII',
        b'AGIF',
        1,
        len(frames),
        len(mp3_data),
        0
    )

    with open(output_path, 'wb') as f:
        f.write(agif_header)
        for frame in frames:
            frame_header = struct.pack('<I', len(frame))
            f.write(frame_header)
            f.write(frame)
        f.write(mp3_data)
    messagebox.showinfo("Success", f"AGIF file created: {output_path}")

# Function to select GIF
def select_gif():
    file_path = filedialog.askopenfilename(filetypes=[("GIF files", "*.gif")])
    if file_path:
        gif_path.set(file_path)

# Function to select MP3
def select_mp3():
    file_path = filedialog.askopenfilename(filetypes=[("MP3 files", "*.mp3")])
    if file_path:
        mp3_path.set(file_path)

# Function to create AGIF
def create_agif_button():
    gif = gif_path.get()
    mp3 = mp3_path.get()
    if not gif or not mp3:
        messagebox.showwarning("Warning", "Please select both a GIF file and an MP3 file!")
        return

    output_path = filedialog.asksaveasfilename(defaultextension=".agif", filetypes=[("AGIF files", "*.agif")])
    if output_path:
        create_agif(gif, mp3, output_path)

# Function to read .agif file
def read_agif(file_path):
    with open(file_path, 'rb') as f:
        header = f.read(14)  # Read the 14-byte header
        signature, version, num_frames, mp3_size, options = struct.unpack('<4sBBII', header)
        
        if signature != b'AGIF':
            raise ValueError("File not recognized as .agif format")

        frames = []
        for _ in range(num_frames):
            frame_size_data = f.read(4)
            frame_size = struct.unpack('<I', frame_size_data)[0]
            frame_data = f.read(frame_size)
            frames.append(frame_data)
        
        mp3_data = f.read(mp3_size)
        
    return frames, mp3_data

# Function to convert GIF frames to PIL images
def frames_to_images(frames):
    images = []
    for index, frame in enumerate(frames):
        try:
            img = Image.open(io.BytesIO(frame))
            images.append(img)
        except UnidentifiedImageError as e:
            print(f"Error converting frame {index}: {e}")
    return images

# GUI Player for AGIF using tkinter
class AgifPlayer(tk.Toplevel):
    def __init__(self, frames, mp3_data, gif_duration, mp3_duration):
        super().__init__()
        self.frames = frames
        self.gif_duration = gif_duration
        self.mp3_data = mp3_data
        self.frame_index = 0
        self.label = tk.Label(self)
        self.label.pack()
        
        # Start audio in a separate thread
        pygame.mixer.init()
        pygame.mixer.music.load(io.BytesIO(mp3_data))
        pygame.mixer.music.play(-1)  # Play in infinite loop

        # Start GIF animation
        self.update_frame()

        # Override the destroy method to stop the audio
        self.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def update_frame(self):
        frame_image = ImageTk.PhotoImage(self.frames[self.frame_index])
        self.label.config(image=frame_image)
        self.label.image = frame_image
        self.frame_index = (self.frame_index + 1) % len(self.frames)
        
        # Update GIF frame every 'gif_duration' ms
        self.after(self.gif_duration, self.update_frame)

    def on_close(self):
        # Stop audio playback
        pygame.mixer.music.stop()
        pygame.mixer.quit()
        
        # Close the window
        self.destroy()

# Function to open and play the AGIF file
def open_and_play_agif():
    agif_path = filedialog.askopenfilename(filetypes=[("AGIF files", "*.agif")])
    if not agif_path:
        return
    
    try:
        # Read the .agif file
        frames, mp3_data = read_agif(agif_path)
        
        # Convert GIF frames to images
        images = frames_to_images(frames)
        
        if not images:
            messagebox.showerror("Error", "Cannot convert GIF frames.")
            return
        
        # Calculate durations in milliseconds
        gif_duration = 1000 // len(frames)  # Duration of each GIF frame
        mp3_duration = AudioSegment.from_file(io.BytesIO(mp3_data), format="mp3").duration_seconds * 1000

        # Create and start the player
        player = AgifPlayer(images, mp3_data, gif_duration, mp3_duration)
        player.title("AGIF Player")
    except Exception as e:
        messagebox.showerror("Error", str(e))

# Create the main interface
root = tk.Tk()
root.title("AGIF Tool")
root.configure(bg=LIGHT_PINK)

# Create tabs
tab_control = ttk.Notebook(root)
tab_control.pack(expand=1, fill="both")

# Style for the tabs and frames
style = ttk.Style()
style.configure('TNotebook', background=LIGHT_PINK)
style.configure('TFrame', background=LIGHT_PINK)
style.configure('TLabel', background=LIGHT_PINK, foreground='black')
style.configure('TButton', background=PAPYRUS_YELLOW, foreground='black', borderwidth=0)

# Tab for creating AGIF
tab_create = ttk.Frame(tab_control)
tab_control.add(tab_create, text="Create AGIF")

gif_path = tk.StringVar()
mp3_path = tk.StringVar()

# Layout for the creation tab
tk.Label(tab_create, text="Select GIF:", bg=LIGHT_PINK).grid(row=0, column=0, padx=10, pady=10)
gif_entry = tk.Entry(tab_create, textvariable=gif_path, width=40, bg=PAPYRUS_YELLOW)
gif_entry.grid(row=0, column=1, padx=10, pady=10)

tk.Button(tab_create, text="Browse", command=select_gif, bg=PAPYRUS_YELLOW).grid(row=0, column=2, padx=10, pady=10)

tk.Label(tab_create, text="Select MP3:", bg=LIGHT_PINK).grid(row=1, column=0, padx=10, pady=10)
mp3_entry = tk.Entry(tab_create, textvariable=mp3_path, width=40, bg=PAPYRUS_YELLOW)
mp3_entry.grid(row=1, column=1, padx=10, pady=10)

tk.Button(tab_create, text="Browse", command=select_mp3, bg=PAPYRUS_YELLOW).grid(row=1, column=2, padx=10, pady=10)

tk.Button(tab_create, text="Create AGIF", command=create_agif_button, width=20, bg=PAPYRUS_YELLOW).grid(row=2, column=0, columnspan=3, pady=20)

# Tab for playing AGIF
tab_play = ttk.Frame(tab_control)
tab_control.add(tab_play, text="Play AGIF")

# Set the background of the "Play AGIF" tab
tab_play.configure(bg=PAPYRUS_YELLOW)

tk.Label(tab_play, text="Player for AGIF format", bg=PAPYRUS_YELLOW).pack(pady=10)
tk.Button(tab_play, text="Open and View AGIF", command=open_and_play_agif, bg=PAPYRUS_YELLOW).pack(pady=20)

# Add tabs to the root window
root.mainloop()
