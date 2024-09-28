import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
from pydub import AudioSegment
import struct
import io

# Funzioni di utility per la creazione del file AGIF
def get_gif_frames(gif_path):
    gif = Image.open(gif_path)
    frames = []
    try:
        while True:
            frames.append(gif.copy())
            gif.seek(gif.tell() + 1)
    except EOFError:
        pass
    return frames

def get_mp3_data(mp3_path):
    audio = AudioSegment.from_file(mp3_path, format="mp3")
    mp3_buffer = io.BytesIO()
    audio.export(mp3_buffer, format="mp3")
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
            with io.BytesIO() as frame_buffer:
                frame.save(frame_buffer, format='PNG')
                frame_bytes = frame_buffer.getvalue()
            frame_header = struct.pack('<I', len(frame_bytes))
            f.write(frame_header)
            f.write(frame_bytes)
        f.write(mp3_data)
    messagebox.showinfo("Successo", f"File AGIF creato: {output_path}")

# Funzione per selezionare GIF
def select_gif():
    file_path = filedialog.askopenfilename(filetypes=[("GIF files", "*.gif")])
    if file_path:
        gif_path.set(file_path)

# Funzione per selezionare MP3
def select_mp3():
    file_path = filedialog.askopenfilename(filetypes=[("MP3 files", "*.mp3")])
    if file_path:
        mp3_path.set(file_path)

# Funzione per creare AGIF
def create_agif_button():
    gif = gif_path.get()
    mp3 = mp3_path.get()
    if not gif or not mp3:
        messagebox.showwarning("Attenzione", "Seleziona sia un file GIF che un file MP3!")
        return

    output_path = filedialog.asksaveasfilename(defaultextension=".agif", filetypes=[("AGIF files", "*.agif")])
    if output_path:
        create_agif(gif, mp3, output_path)

# Creazione dell'interfaccia
root = tk.Tk()
root.title("AGIF Creator")

gif_path = tk.StringVar()
mp3_path = tk.StringVar()

# Layout
tk.Label(root, text="Seleziona GIF:").grid(row=0, column=0, padx=10, pady=10)
tk.Entry(root, textvariable=gif_path, width=40).grid(row=0, column=1, padx=10, pady=10)
tk.Button(root, text="Sfoglia", command=select_gif).grid(row=0, column=2, padx=10, pady=10)

tk.Label(root, text="Seleziona MP3:").grid(row=1, column=0, padx=10, pady=10)
tk.Entry(root, textvariable=mp3_path, width=40).grid(row=1, column=1, padx=10, pady=10)
tk.Button(root, text="Sfoglia", command=select_mp3).grid(row=1, column=2, padx=10, pady=10)

tk.Button(root, text="Crea AGIF", command=create_agif_button, width=20).grid(row=2, column=0, columnspan=3, pady=20)

root.mainloop()
