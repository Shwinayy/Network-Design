from socket import *

SERVER_NAME = "127.0.0.1"   # same machine: 127.0.0.1 or "localhost"
SERVER_PORT = 12000
BUFFER_SIZE = 2048

clientSocket = socket(AF_INET, SOCK_DGRAM)

# Prevent hanging forever if server doesn't reply
clientSocket.settimeout(3.0)

try:
    message = input("[CLIENT] Input lowercase sentence: ")

    print(f"[CLIENT] Sending to {SERVER_NAME}:{SERVER_PORT} -> {message!r}")
    clientSocket.sendto(message.encode(), (SERVER_NAME, SERVER_PORT))

    modifiedMessage, serverAddress = clientSocket.recvfrom(BUFFER_SIZE)
    print(f"[CLIENT] Received from {serverAddress}: {modifiedMessage.decode(errors='ignore')!r}")

except timeout:
    print("[CLIENT] Timed out waiting for server response. (Is the server running? Right port?)")
except KeyboardInterrupt:
    print("\n[CLIENT] Cancelled.")
except Exception as e:
    print(f"[CLIENT] Error: {e}")
finally:
    clientSocket.close()
