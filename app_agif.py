import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, UnidentifiedImageError
from pydub import AudioSegment
import struct
import io
import pygame

# Definire i colori
LIGHT_PINK = "#FFB6C1"  # Rosa chiaro
PAPYRUS_YELLOW = "#FAEBD7"  # Giallo papiro

# Funzioni di utility per la creazione del file AGIF
def get_gif_frames(gif_path):
    gif = Image.open(gif_path)
    frames = []
    try:
        while True:
            # Salva il frame con una compressione maggiore
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
    audio.export(mp3_buffer, format="mp3", bitrate=f"{bitrate}k")  # Riduci il bitrate
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

# Funzione per leggere il file .agif
def read_agif(file_path):
    with open(file_path, 'rb') as f:
        header = f.read(14)  # Leggi l'header di 14 byte
        signature, version, num_frames, mp3_size, options = struct.unpack('<4sBBII', header)
        
        if signature != b'AGIF':
            raise ValueError("File non riconosciuto come formato .agif")

        frames = []
        for _ in range(num_frames):
            frame_size_data = f.read(4)
            frame_size = struct.unpack('<I', frame_size_data)[0]
            frame_data = f.read(frame_size)
            frames.append(frame_data)
        
        mp3_data = f.read(mp3_size)
        
    return frames, mp3_data

# Funzione per convertire i frame della GIF in immagini PIL
def frames_to_images(frames):
    images = []
    for index, frame in enumerate(frames):
        try:
            img = Image.open(io.BytesIO(frame))
            images.append(img)
        except UnidentifiedImageError as e:
            print(f"Errore nella conversione del frame {index}: {e}")
    return images

# Player Grafico con tkinter per la GIF
class AgifPlayer(tk.Toplevel):
    def __init__(self, frames, mp3_data, gif_duration, mp3_duration):
        super().__init__()
        self.frames = frames
        self.gif_duration = gif_duration
        self.mp3_data = mp3_data
        self.frame_index = 0
        self.label = tk.Label(self)
        self.label.pack()
        
        # Avvia l'audio in un thread separato
        pygame.mixer.init()
        pygame.mixer.music.load(io.BytesIO(mp3_data))
        pygame.mixer.music.play(-1)  # Riproduci in loop infinito

        # Avvia l'animazione della GIF
        self.update_frame()

        # Override del metodo destroy per fermare l'audio
        self.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def update_frame(self):
        frame_image = ImageTk.PhotoImage(self.frames[self.frame_index])
        self.label.config(image=frame_image)
        self.label.image = frame_image
        self.frame_index = (self.frame_index + 1) % len(self.frames)
        
        # Aggiorna il frame della GIF ogni 'gif_duration' ms
        self.after(self.gif_duration, self.update_frame)

    def on_close(self):
        # Ferma la riproduzione dell'audio
        pygame.mixer.music.stop()
        pygame.mixer.quit()
        
        # Chiudi la finestra
        self.destroy()

# Funzione per aprire e riprodurre il file AGIF
def open_and_play_agif():
    agif_path = filedialog.askopenfilename(filetypes=[("AGIF files", "*.agif")])
    if not agif_path:
        return
    
    try:
        # Lettura del file .agif
        frames, mp3_data = read_agif(agif_path)
        
        # Converti i frame della GIF in immagini
        images = frames_to_images(frames)
        
        if not images:
            messagebox.showerror("Errore", "Non è possibile convertire i frame della GIF.")
            return
        
        # Calcola le durate in millisecondi
        gif_duration = 1000 // len(frames)  # Durata di ogni frame della GIF
        mp3_duration = AudioSegment.from_file(io.BytesIO(mp3_data), format="mp3").duration_seconds * 1000

        # Crea e avvia il player
        player = AgifPlayer(images, mp3_data, gif_duration, mp3_duration)
        player.title("AGIF Player")
    except Exception as e:
        messagebox.showerror("Errore", str(e))

# Creazione dell'interfaccia principale
root = tk.Tk()
root.title("AGIF Tool")
root.configure(bg=LIGHT_PINK)

# Creazione delle schede (tabs)
tab_control = ttk.Notebook(root)
tab_control.pack(expand=1, fill="both")

# Stile per le schede e i frame
style = ttk.Style()
style.configure('TNotebook', background=LIGHT_PINK)
style.configure('TFrame', background=LIGHT_PINK)
style.configure('TLabel', background=LIGHT_PINK, foreground='black')
style.configure('TButton', background=PAPYRUS_YELLOW, foreground='black', borderwidth=0)

# Tab per la creazione di AGIF
tab_create = ttk.Frame(tab_control)
tab_control.add(tab_create, text="Crea AGIF")

gif_path = tk.StringVar()
mp3_path = tk.StringVar()

# Layout per la scheda di creazione
tk.Label(tab_create, text="Seleziona GIF:", bg=LIGHT_PINK).grid(row=0, column=0, padx=10, pady=10)
gif_entry = tk.Entry(tab_create, textvariable=gif_path, width=40, bg=PAPYRUS_YELLOW)
gif_entry.grid(row=0, column=1, padx=10, pady=10)

tk.Button(tab_create, text="Sfoglia", command=select_gif, bg=PAPYRUS_YELLOW).grid(row=0, column=2, padx=10, pady=10)

tk.Label(tab_create, text="Seleziona MP3:", bg=LIGHT_PINK).grid(row=1, column=0, padx=10, pady=10)
mp3_entry = tk.Entry(tab_create, textvariable=mp3_path, width=40, bg=PAPYRUS_YELLOW)
mp3_entry.grid(row=1, column=1, padx=10, pady=10)

tk.Button(tab_create, text="Sfoglia", command=select_mp3, bg=PAPYRUS_YELLOW).grid(row=1, column=2, padx=10, pady=10)

tk.Button(tab_create, text="Crea AGIF", command=create_agif_button, width=20, bg=PAPYRUS_YELLOW).grid(row=2, column=0, columnspan=3, pady=20)

# Tab per la riproduzione di AGIF
tab_play = ttk.Frame(tab_control)
tab_control.add(tab_play, text="Riproduci AGIF")

# Imposta lo sfondo del tab "Riproduci AGIF"
tab_play.configure(bg=PAPYRUS_YELLOW)

tk.Label(tab_play, text="Player per il formato AGIF", bg=PAPYRUS_YELLOW).pack(pady=10)
tk.Button(tab_play, text="Apri e Visualizza AGIF", command=open_and_play_agif, bg=PAPYRUS_YELLOW).pack(pady=20)

# Aggiunta delle schede al root
root.mainloop()
