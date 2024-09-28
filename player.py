import struct
from PIL import Image, ImageTk, UnidentifiedImageError
import pygame
import tkinter as tk
import io
from pydub import AudioSegment
from pydub.playback import _play_with_simpleaudio

# Funzione per leggere il file .agif
def read_agif(file_path):
    with open(file_path, 'rb') as f:
        header = f.read(14)  # Leggi l'header di 14 byte (non 16)
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
        # Verifica i primi byte del frame per controllare se è un'immagine valida
        print(f"Frame {index} header: {frame[:10]}")
        
        try:
            img = Image.open(io.BytesIO(frame))
            images.append(img)
        except UnidentifiedImageError as e:
            print(f"Errore nella conversione del frame {index}: {e}")
    return images

# Funzione per riprodurre l'audio MP3
def play_mp3(mp3_data):
    audio = AudioSegment.from_file(io.BytesIO(mp3_data), format="mp3")
    _play_with_simpleaudio(audio)

# Player Grafico con tkinter per la GIF
class AgifPlayer(tk.Tk):
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
    
    def update_frame(self):
        frame_image = ImageTk.PhotoImage(self.frames[self.frame_index])
        self.label.config(image=frame_image)
        self.label.image = frame_image
        self.frame_index = (self.frame_index + 1) % len(self.frames)
        
        # Aggiorna il frame della GIF ogni 'gif_duration' ms
        self.after(self.gif_duration, self.update_frame)

# Funzione principale
def main():
    # Percorso al file .agif
    agif_path = 'files/bradipo2.agif'
    
    # Lettura del file .agif
    frames, mp3_data = read_agif(agif_path)
    
    # Converti i frame della GIF in immagini
    images = frames_to_images(frames)
    
    # Calcola le durate in millisecondi
    gif_duration = 1000 // len(frames)  # Durata di ogni frame della GIF
    mp3_duration = AudioSegment.from_file(io.BytesIO(mp3_data), format="mp3").duration_seconds * 1000

    # Crea e avvia il player
    player = AgifPlayer(images, mp3_data, gif_duration, mp3_duration)
    player.mainloop()

# Esegui il player
if __name__ == '__main__':
    main()
