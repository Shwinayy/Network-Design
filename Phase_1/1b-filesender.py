from socket import *
import struct
import os

# Same local setup as 1a
SERVER_NAME = "127.0.0.1"
SERVER_PORT = 12000

CHUNK_SIZE = 1024
HEADER_FMT = "!IHB"   # seq (4 bytes), data_len (2 bytes), is_last (1 byte)

FILENAME = "input.bmp"   # CHANGE if your bmp has a different name

clientSocket = socket(AF_INET, SOCK_DGRAM)
clientSocket.settimeout(3.0)

def send_and_wait_ack(packet, seq):
    while True:
        clientSocket.sendto(packet, (SERVER_NAME, SERVER_PORT))
        try:
            ack, _ = clientSocket.recvfrom(2048)
            if ack.decode(errors="ignore") == f"ACK:{seq}":
                return
        except timeout:
            print(f"[1b CLIENT] Timeout waiting for ACK:{seq}, resending...")

try:
    filesize = os.path.getsize(FILENAME)
    num_chunks = (filesize + CHUNK_SIZE - 1) // CHUNK_SIZE

    print(f"[1b CLIENT] Sending {FILENAME} ({filesize} bytes)")
    print(f"[1b CLIENT] Total chunks: {num_chunks}")

    seq = 0
    with open(FILENAME, "rb") as f:
        while True:
            data = f.read(CHUNK_SIZE)
            if not data:
                break

            data_len = len(data)
            is_last = 1 if f.tell() == filesize else 0

            header = struct.pack(HEADER_FMT, seq, data_len, is_last)
            packet = header + data

            print(f"[1b CLIENT] -> sending seq={seq}, bytes={data_len}, is_last={is_last}")
            send_and_wait_ack(packet, seq)

            seq += 1

    print("[1b CLIENT] File transfer complete.")

except FileNotFoundError:
    print(f"[1b CLIENT] ERROR: File '{FILENAME}' not found.")
except KeyboardInterrupt:
    print("\n[1b CLIENT] Cancelled.")
except Exception as e:
    print(f"[1b CLIENT] ERROR: {e}")
finally:
    clientSocket.close()
