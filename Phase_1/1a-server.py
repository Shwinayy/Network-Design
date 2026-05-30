from socket import *

SERVER_PORT = 12000
BUFFER_SIZE = 2048

serverSocket = socket(AF_INET, SOCK_DGRAM)

# Bind to all interfaces on this machine
serverSocket.bind(("", SERVER_PORT))

print(f"[SERVER] Ready to receive on UDP port {SERVER_PORT}")

while True:
    try:
        message, clientAddress = serverSocket.recvfrom(BUFFER_SIZE)
        print(f"[SERVER] Received {message!r} from {clientAddress}")

        modifiedMessage = message.decode(errors="ignore").upper()
        serverSocket.sendto(modifiedMessage.encode(), clientAddress)
        print(f"[SERVER] Sent back {modifiedMessage!r} to {clientAddress}")

    except KeyboardInterrupt:
        print("\n[SERVER] Shutting down.")
        break
    except Exception as e:
        print(f"[SERVER] Error: {e}")

serverSocket.close()
