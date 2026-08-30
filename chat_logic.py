import socket
import threading
import json
from datetime import datetime

class ChatServer:
    """Handles peer-to-peer connection and messaging"""
    
    def __init__(self, host='localhost', port=5555):
        self.host = host
        self.port = port
        self.server_socket = None
        self.connection = None
        self.running = False
        self.message_callback = None
        
    def start_server(self, on_message=None):
        """Start the chat server"""
        self.message_callback = on_message
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(1)
            self.running = True
            
            # Start listening in background thread
            threading.Thread(target=self._listen_for_connections, daemon=True).start()
            return True
        except Exception as e:
            print(f"Error starting server: {e}")
            return False
    
    def _listen_for_connections(self):
        """Listen for incoming connections"""
        while self.running:
            try:
                self.connection, addr = self.server_socket.accept()
                print(f"Connected to: {addr}")
                
                # Start receiving messages
                self._receive_messages()
            except Exception as e:
                if self.running:
                    print(f"Error accepting connection: {e}")
    
    def _receive_messages(self):
        """Receive messages from connected peer"""
        while self.running and self.connection:
            try:
                data = self.connection.recv(1024).decode('utf-8')
                if data:
                    message = json.loads(data)
                    if self.message_callback:
                        self.message_callback(message)
                else:
                    break
            except Exception as e:
                if self.running:
                    print(f"Error receiving message: {e}")
                break
    
    def send_message(self, sender, content, msg_type="message", msg_id=None):
        """Send message to peer"""
        if not self.connection:
            return False
        
        try:
            message = {
                "sender": sender,
                "content": content,
                "type": msg_type,
                "timestamp": datetime.now().isoformat(),
                "id": msg_id
            }
            self.connection.send(json.dumps(message).encode('utf-8'))
            return True
        except Exception as e:
            print(f"Error sending message: {e}")
            return False
    
    def connect_to_peer(self, host, port, on_message=None):
        """Connect to another peer"""
        self.message_callback = on_message
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        try:
            self.connection.connect((host, port))
            self.running = True
            
            # Start receiving messages in background
            threading.Thread(target=self._receive_messages, daemon=True).start()
            return True
        except Exception as e:
            print(f"Error connecting to peer: {e}")
            return False
    
    def close(self):
        """Close the connection"""
        self.running = False
        if self.connection:
            self.connection.close()
        if self.server_socket:
            self.server_socket.close()
