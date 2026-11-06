import socket
import threading

def handle_client(conn, addr):
    http_response = b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\nConnection: keep-alive\r\n\r\nOK"
    
    while True:
        print("read")
        try:
            # Read up to 1024 bytes
            buf = conn.recv(1024)
        except Exception:
            break
            
        bytes_read = len(buf)
        print("buf:")
        print(buf)
        print(f"Got answered: {bytes_read}")
        
        if bytes_read <= 0:
            print("break no bytes read")
            break
            
        print("send")
        conn.sendall(http_response)
        
    conn.close()

def main():
    host = "0.0.0.0"
    port = 8080
    
    # Set up the TCP server
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Allow immediate reuse of the port
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    server.bind((host, port))
    server.listen()
    print(f"Listening on {host}:{port}...")
    
    while True:
        conn, addr = server.accept()
        # Handle each client in a new thread so it doesn't block the server
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

if __name__ == "__main__":
    main()
