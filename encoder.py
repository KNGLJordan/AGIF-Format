from PIL import Image
from pydub import AudioSegment
import struct
import io

# Funzione per leggere una GIF e ottenere i frame
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

# Funzione per leggere un file MP3 e restituire i dati in formato compresso MP3
def get_mp3_data(mp3_path):
    audio = AudioSegment.from_file(mp3_path, format="mp3")
    mp3_buffer = io.BytesIO()
    audio.export(mp3_buffer, format="mp3")
    return mp3_buffer.getvalue(), audio.frame_rate, audio.channels, audio.sample_width

# Funzione per creare un file .agif
def create_agif(gif_path, mp3_path, output_path):
    # Leggi i frame della GIF e i dati MP3
    frames = get_gif_frames(gif_path)
    mp3_data, sample_rate, channels, sample_width = get_mp3_data(mp3_path)
    
    # Definisci l'header del file .agif
    agif_header = struct.pack(
        '<4sBBII',    # Formato dell'header (4s = 4 caratteri, B = 1 byte, I = 4 byte int)
        b'AGIF',      # Signature
        1,            # Versione
        len(frames),  # Numero di frame GIF
        len(mp3_data),# Dimensione dati MP3
        0             # Placeholder per opzioni
    )
    
    # Scrivi l'header e i dati su file
    with open(output_path, 'wb') as f:
        f.write(agif_header)
        # Scrivi i frame della GIF come sequenza
        for frame in frames:
            with io.BytesIO() as frame_buffer:
                frame.save(frame_buffer, format='PNG')
                frame_bytes = frame_buffer.getvalue()
            frame_header = struct.pack('<I', len(frame_bytes))
            f.write(frame_header)
            f.write(frame_bytes)
        # Scrivi i dati MP3
        f.write(mp3_data)

# Esempio di utilizzo
file_gif_name = 'files/bradipo.gif'  # Inserire il nome del file GIF
file_mp3_name = 'files/clacson.mp3'  # Inserire il nome del file MP3
output_agif_name = 'files/bradipoclacson.agif'  # Inserire il nome del file .agif di output

create_agif(file_gif_name, file_mp3_name, output_agif_name)
