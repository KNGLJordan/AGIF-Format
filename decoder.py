import struct
from PIL import Image
import io

def read_agif(file_path):
    with open(file_path, 'rb') as f:
        # Leggi l'header del file (14 byte come specificato nell'encoder)
        header = f.read(14)

        # Decodifica l'header secondo la struttura definita nell'encoder
        signature, version, num_frames, mp3_size, options = struct.unpack('<4sBBII', header)
        
        # Verifica che il formato sia corretto
        if signature != b'AGIF':
            raise ValueError("File non riconosciuto come formato .agif")

        # Leggi i frame della GIF
        frames = []
        for _ in range(num_frames):
            frame_size_data = f.read(4)  # Leggi la dimensione del frame
            frame_size = struct.unpack('<I', frame_size_data)[0]
            frame_data = f.read(frame_size)  # Leggi il frame in base alla dimensione
            frames.append(frame_data)
        
        # Leggi i dati MP3
        mp3_data = f.read(mp3_size)  # Leggi la dimensione dei dati MP3
        
        # Restituisci i dati letti
        return frames, mp3_data

# Esempio di utilizzo
file_agif_name = 'files/output.agif'  # Inserire il nome del file .agif
frames, mp3_data = read_agif(file_agif_name)

print(f"Numero di frame GIF: {len(frames)}")
print(f"Dimensione dati MP3: {len(mp3_data)} bytes")

'''

#############################################
# Visualizza i frame della GIF
for frame_data in frames:
    try:
        img = Image.open(io.BytesIO(frame_data))
        img.show()  # Mostra l'immagine per verifica
    except Exception as e:
        print(f"Errore nella conversione del frame: {e}")

#############################################
# Salva i dati MP3 in un file "test.mp3"
with open("test.mp3", "wb") as f:
    f.write(mp3_data)

'''
