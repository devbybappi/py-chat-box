import tkinter as tk
from tkinter import scrolledtext, messagebox, Menu
import socket
import threading
import json
import random
import string
import time
from datetime import datetime
from chat_logic import ChatServer

class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat & Chat")
        self.root.geometry("900x600")
        self.root.configure(bg="#f0f0f0")
        
        # Connection variables
        self.chat_server = ChatServer(host='localhost', port=5555)
        self.connected = False
        self.my_code = None
        self.locked = False
        self.lock_password = None
        self.username = "User"
        self.peer_username = "Peer"
        self.port = 5555
        
        # New feature variables
        self.last_message_time = None
        self.typing_timer = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.message_receipts = {}  # Track message delivery
        
        # Create UI
        self.create_widgets()
        self.start_server()
        
    def create_widgets(self):
        """Create the main UI layout"""
        # Main container
        main_frame = tk.Frame(self.root, bg="#f0f0f0")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left Panel - User Setup
        left_panel = tk.Frame(main_frame, bg="white", relief=tk.RIDGE, borderwidth=2)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10), pady=10)
        
        # Title
        title_label = tk.Label(left_panel, text="Chat & Chat", font=("Arial", 14, "bold"), bg="white")
        title_label.pack(pady=10)
        
        # Your Name Section
        name_frame = tk.Frame(left_panel, bg="white")
        name_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(name_frame, text="Your Name:", font=("Arial", 10), bg="white").pack(anchor=tk.W)
        self.name_entry = tk.Entry(name_frame, font=("Arial", 10), width=20)
        self.name_entry.pack(fill=tk.X, pady=5)
        self.name_entry.insert(0, "User")
        
        # Lock Chat Section
        lock_frame = tk.Frame(left_panel, bg="white")
        lock_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(lock_frame, text="Lock This Chat:", font=("Arial", 10), bg="white").pack(anchor=tk.W)
        self.lock_entry = tk.Entry(lock_frame, font=("Arial", 10), width=20, show="*")
        self.lock_entry.pack(fill=tk.X, pady=5)
        
        lock_btn_frame = tk.Frame(lock_frame, bg="white")
        lock_btn_frame.pack(anchor=tk.W, pady=5)
        
        lock_btn = tk.Button(lock_btn_frame, text="Lock", command=self.lock_chat, bg="#333", fg="white", padx=10)
        lock_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.unlock_btn = tk.Button(lock_btn_frame, text="Unlock", command=self.unlock_chat, bg="#666", fg="white", padx=10, state=tk.DISABLED)
        self.unlock_btn.pack(side=tk.LEFT)
        
        # Input Code Section
        code_input_frame = tk.Frame(left_panel, bg="white")
        code_input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(code_input_frame, text="Input Code:", font=("Arial", 10), bg="white").pack(anchor=tk.W)
        self.code_entry = tk.Entry(code_input_frame, font=("Arial", 10), width=20)
        self.code_entry.pack(fill=tk.X, pady=5)
        
        connect_btn = tk.Button(code_input_frame, text="Connect", command=self.connect_to_peer, bg="#333", fg="#00ff00", padx=10, font=("Arial", 10, "bold"))
        connect_btn.pack(anchor=tk.W, pady=5)
        
        # Generate Code Section
        generate_frame = tk.Frame(left_panel, bg="white")
        generate_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(generate_frame, text="Generate Code:", font=("Arial", 10), bg="white").pack(anchor=tk.W)
        
        generate_btn = tk.Button(generate_frame, text="Generate", command=self.generate_code, bg="#333", fg="white", padx=10)
        generate_btn.pack(anchor=tk.W, pady=5)
        
        self.code_display = tk.Label(generate_frame, text="Your Code: N/A", font=("Arial", 10, "bold"), bg="white", fg="#00ff00")
        self.code_display.pack(anchor=tk.W, pady=5)
        
        # Right Panel - Chat Area and System Messages
        right_panel = tk.Frame(main_frame, bg="white", relief=tk.RIDGE, borderwidth=2)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Status
        self.status_label = tk.Label(right_panel, text="Not Connected", font=("Arial", 10, "bold"), bg="white", fg="red")
        self.status_label.pack(pady=10)
        
        # Chat and System Container
        chat_system_frame = tk.Frame(right_panel, bg="white")
        chat_system_frame.pack(fill=tk.BOTH, expand=True)
        
        # Chat Display (Left side of right panel)
        chat_frame = tk.Frame(chat_system_frame, bg="white")
        chat_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        tk.Label(chat_frame, text="Messages", font=("Arial", 9, "bold"), bg="white").pack(anchor=tk.W)
        self.chat_display = scrolledtext.ScrolledText(chat_frame, font=("Arial", 10), bg="#f9f9f9", state=tk.DISABLED)
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        
        # System Messages Display (Right side of right panel)
        system_frame = tk.Frame(chat_system_frame, bg="white")
        system_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        tk.Label(system_frame, text="System", font=("Arial", 9, "bold"), bg="white").pack(anchor=tk.W)
        self.system_display = scrolledtext.ScrolledText(system_frame, font=("Arial", 9), bg="#fffacd", state=tk.DISABLED)
        self.system_display.pack(fill=tk.BOTH, expand=True)
        
        # Message Input
        input_frame = tk.Frame(right_panel, bg="white")
        input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.msg_entry = tk.Entry(input_frame, font=("Arial", 10))
        self.msg_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self.msg_entry.bind("<Return>", lambda e: self.send_message())
        self.msg_entry.bind("<KeyRelease>", self._on_typing)
        
        # Emoji Button
        emoji_btn = tk.Button(input_frame, text="😊", command=self._show_emoji_menu, bg="#ffd700", padx=10, font=("Arial", 12))
        emoji_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        send_btn = tk.Button(input_frame, text="Send", command=self.send_message, bg="#333", fg="white", padx=20)
        send_btn.pack(side=tk.RIGHT, padx=(0, 5))
        
        clear_btn = tk.Button(input_frame, text="Clear", command=self.clear_chat, bg="#666", fg="white", padx=15)
        clear_btn.pack(side=tk.RIGHT)
        
        # Typing Indicator
        self.typing_label = tk.Label(right_panel, text="", font=("Arial", 8, "italic"), bg="white", fg="#999")
        self.typing_label.pack(pady=5)
        
    def generate_code(self):
        """Generate a connection code"""
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        self.my_code = code
        self.code_display.config(text=f"Your Code: {code}")
        self.display_system_message(f"Code generated: {code}. Share this with other user.")
        
    def lock_chat(self):
        """Lock the chat with a password"""
        password = self.lock_entry.get()
        if password:
            self.lock_password = password
            self.locked = True
            self.display_system_message("Chat locked with password.")
            self.unlock_btn.config(state=tk.NORMAL)
            messagebox.showinfo("Success", "Chat locked successfully!")
        else:
            messagebox.showerror("Error", "Please enter a password.")
    
    def unlock_chat(self):
        """Unlock the chat"""
        if self.locked:
            self.lock_password = None
            self.locked = False
            self.lock_entry.delete(0, tk.END)
            self.display_system_message("Chat unlocked.")
            self.unlock_btn.config(state=tk.DISABLED)
            messagebox.showinfo("Success", "Chat unlocked successfully!")
        else:
            messagebox.showinfo("Info", "Chat is not locked.")
            
    def connect_to_peer(self):
        """Connect to peer using code with auto-reconnect"""
        code = self.code_entry.get().strip()
        self.username = self.name_entry.get().strip() or "User"
        
        if not code:
            messagebox.showerror("Error", "Please enter a code.")
            return
        
        # Parse code format: IP:PORT or just code (assumes localhost with default port)
        try:
            if ':' in code:
                host, port_str = code.split(':')
                port = int(port_str)
            else:
                host = 'localhost'
                port = int(code) if code.isdigit() else self.port
            
            # Try to connect with auto-reconnect
            self._reconnect_with_retry(host, port)
        except Exception as e:
            messagebox.showerror("Error", f"Connection error: {str(e)}")
    
    def _reconnect_with_retry(self, host, port):
        """Try to connect with automatic retry"""
        self.reconnect_attempts = 0
        
        def attempt_connection():
            while self.reconnect_attempts < self.max_reconnect_attempts and not self.connected:
                try:
                    if self.chat_server.connect_to_peer(host, port, on_message=self._on_receive_message):
                        self.connected = True
                        self.reconnect_attempts = 0
                        self.status_label.config(text="You Both Are Connected", fg="green")
                        self.peer_username = "Peer"
                        self.display_system_message(f"Connected to {host}:{port}! Ready to chat.")
                        return True
                    else:
                        self.reconnect_attempts += 1
                        if self.reconnect_attempts < self.max_reconnect_attempts:
                            self.display_system_message(f"Connection failed. Retrying ({self.reconnect_attempts}/{self.max_reconnect_attempts})...")
                            time.sleep(2)
                except Exception as e:
                    self.reconnect_attempts += 1
                    if self.reconnect_attempts < self.max_reconnect_attempts:
                        self.display_system_message(f"Error: {str(e)}. Retrying...")
                        time.sleep(2)
            
            if not self.connected:
                self.display_system_message(f"Failed to connect after {self.max_reconnect_attempts} attempts.")
        
        threading.Thread(target=attempt_connection, daemon=True).start()

        
    def start_server(self):
        """Start listening for connections"""
        if self.chat_server.start_server(on_message=self._on_receive_message):
            self.display_system_message(f"Server started on localhost:{self.port}. Share this to connect.")
        else:
            messagebox.showerror("Error", "Failed to start server.")
    
    def _on_receive_message(self, message):
        """Handle received message with read receipts"""
        try:
            sender = message.get("sender", "Unknown")
            content = message.get("content", "")
            msg_type = message.get("type", "message")
            msg_id = message.get("id", None)
            
            if msg_type == "message":
                self.display_message(sender, content)
                # Send read receipt
                if msg_id:
                    self.chat_server.send_message(self.username, msg_id, msg_type="receipt")
            elif msg_type == "typing":
                self.typing_label.config(text=f"{sender} is typing...")
                # Clear typing indicator after 3 seconds
                if self.typing_timer:
                    self.root.after_cancel(self.typing_timer)
                self.typing_timer = self.root.after(3000, lambda: self.typing_label.config(text=""))
            elif msg_type == "receipt":
                # Message was read by peer
                self._update_message_receipt(content)
            elif msg_type == "system":
                self.display_message("System", content)
        except Exception as e:
            print(f"Error processing message: {e}")
        
    def send_message(self):
        """Send a message with read receipt tracking"""
        message = self.msg_entry.get().strip()
        if message:
            if not self.connected:
                messagebox.showerror("Error", "Not connected to a peer.")
                return
            
            self.username = self.name_entry.get().strip() or "User"
            
            # Generate message ID for tracking
            msg_id = str(int(time.time() * 1000))
            self.message_receipts[msg_id] = "sent"
            
            # Send via socket
            if self.chat_server.send_message(self.username, message, msg_type="message", msg_id=msg_id):
                self.display_message(self.username, message, msg_id)
                self.msg_entry.delete(0, tk.END)
                self.typing_label.config(text="")
            else:
                messagebox.showerror("Error", "Failed to send message.")
            
    def display_message(self, sender, message, msg_id=None):
        """Display message in chat area with timestamp log"""
        self.chat_display.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Calculate time difference from last message
        time_diff = ""
        if self.last_message_time:
            diff = time.time() - self.last_message_time
            if diff < 60:
                time_diff = f" (+{int(diff)}s)"
            elif diff < 3600:
                time_diff = f" (+{int(diff/60)}m)"
            else:
                time_diff = f" (+{int(diff/3600)}h)"
        
        self.last_message_time = time.time()
        
        # Add read receipt indicator for sent messages
        receipt_indicator = ""
        if msg_id and self.username == sender:
            receipt_indicator = " ✓"
        
        message_text = f"[{timestamp}{time_diff}] {sender}: {message}{receipt_indicator}\n"
        self.chat_display.insert(tk.END, message_text)
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
    
    def display_system_message(self, message):
        """Display system message in system area"""
        self.system_display.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.system_display.insert(tk.END, f"[{timestamp}] {message}\n")
        self.system_display.see(tk.END)
        self.system_display.config(state=tk.DISABLED)
    
    def clear_chat(self):
        """Clear the chat display area"""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state=tk.DISABLED)
        self.display_system_message("Chat cleared.")
    
    def _on_typing(self, event):
        """Send typing indicator when user types"""
        if self.connected and len(self.msg_entry.get()) > 0:
            self.chat_server.send_message(self.username, "", msg_type="typing")
    
    def _show_emoji_menu(self):
        """Show emoji picker menu"""
        emojis = ["😊", "😂", "❤️", "👍", "🔥", "✨", "😍", "😢", "😡", "🤔", "😎", "😴", "🎉", "🎈", "🎁"]
        
        emoji_menu = tk.Menu(self.root, tearoff=False)
        for emoji in emojis:
            emoji_menu.add_command(label=emoji, command=lambda e=emoji: self._insert_emoji(e))
        
        try:
            x = self.root.winfo_rootx() + 120
            y = self.root.winfo_rooty() + 450
            emoji_menu.tk_popup(x, y)
        except:
            pass
    
    def _insert_emoji(self, emoji):
        """Insert emoji into message entry"""
        current_pos = self.msg_entry.index(tk.INSERT)
        self.msg_entry.insert(current_pos, emoji)
        self.msg_entry.focus()
    
    def _update_message_receipt(self, msg_id):
        """Update message status to delivered/read"""
        if msg_id in self.message_receipts:
            self.message_receipts[msg_id] = "delivered"
            # Could update chat display with ✓✓ indicator Here

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    
    def on_closing():
        app.chat_server.close()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
