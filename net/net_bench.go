package main

import (
	"fmt"
	"net"
)

func handleClient(conn net.Conn) {
	// Ensure the connection is closed when the function exits
	defer conn.Close()
	
	buf := make([]byte, 1024)
	httpResponse := []byte("HTTP/1.1 200 OK\r\nContent-Length: 2\r\nConnection: keep-alive\r\n\r\nOK")

	for {
		fmt.Println("read")
		bytesRead, err := conn.Read(buf)
		
		fmt.Println("buf:")
		// Slicing the buffer to only print the bytes that were actually read
		fmt.Println(string(buf[:bytesRead]))
		fmt.Println("Got answered:", bytesRead)

		// err != nil usually means EOF (client disconnected)
		if err != nil || bytesRead <= 0 {
			fmt.Println("break no bytes read")
			break
		}

		fmt.Println("send")
		conn.Write(httpResponse)
	}
}

func main() {
	// Start a TCP listener on 0.0.0.0:8080
	server, err := net.Listen("tcp", "0.0.0.0:8080")
	if err != nil {
		panic(err)
	}
	defer server.Close()
	
	fmt.Println("Listening on 0.0.0.0:8080...")

	for {
		conn, err := server.Accept()
		if err != nil {
			fmt.Println("Error accepting connection:", err)
			continue
		}
		
		// Spawn a new goroutine to handle the client concurrently
		go handleClient(conn)
	}
}
