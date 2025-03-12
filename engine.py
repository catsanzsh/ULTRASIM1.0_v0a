# test.py
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import queue
import logging
from pathlib import Path
from sdl2 import *
import ctypes

class EmulatorCore:
    def __init__(self, queue):
        self.queue = queue
        self.running = False
        self.rom_data = None
        self.window = None
        self.renderer = None

    def init_video(self):
        if SDL_Init(SDL_INIT_VIDEO) != 0:
            raise RuntimeError(f"SDL initialization failed: {SDL_GetError()}")

        self.window = SDL_CreateWindow(b"N64 Emulator",
                                      SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
                                      640, 480, SDL_WINDOW_SHOWN)
        self.renderer = SDL_CreateRenderer(self.window, -1, 
                                          SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC)

    def load_rom(self, path):
        try:
            with open(path, "rb") as f:
                self.rom_data = f.read()
            self.queue.put(('log', f"Loaded ROM: {Path(path).name}"))
            return True
        except Exception as e:
            self.queue.put(('error', f"ROM loading failed: {str(e)}"))
            return False

    def run(self):
        self.running = True
        try:
            self.init_video()
            while self.running:
                # Basic emulation loop
                self.process_input()
                self.execute_frame()
                self.render_frame()
        except Exception as e:
            self.queue.put(('error', str(e)))
        finally:
            self.shutdown()

    def process_input(self):
        event = SDL_Event()
        while SDL_PollEvent(ctypes.byref(event)):
            if event.type == SDL_QUIT:
                self.running = False

    def execute_frame(self):
        # Placeholder for CPU execution
        pass

    def render_frame(self):
        SDL_RenderClear(self.renderer)
        SDL_RenderPresent(self.renderer)

    def shutdown(self):
        if self.renderer:
            SDL_DestroyRenderer(self.renderer)
        if self.window:
            SDL_DestroyWindow(self.window)
        SDL_Quit()

class EmulatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("N64 Emulator")
        self.root.geometry("800x600")
        
        self.emulator_thread = None
        self.emulator_core = None
        self.queue = queue.Queue()
        
        self.setup_logging()
        self.create_widgets()
        self.setup_queue_handler()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename='n64_emulator.log'
        )

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=5)

        self.load_button = ttk.Button(
            control_frame, 
            text="Load ROM",
            command=self.load_rom
        )
        self.load_button.pack(side=tk.LEFT, padx=5)

        self.start_button = ttk.Button(
            control_frame,
            text="Start",
            state=tk.DISABLED,
            command=self.start_emulation
        )
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(
            control_frame,
            text="Stop",
            state=tk.DISABLED,
            command=self.stop_emulation
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)

        self.canvas = tk.Canvas(main_frame, width=640, height=480, bg='black')
        self.canvas.pack(pady=10)

        self.log_text = tk.Text(main_frame, height=10, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(main_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def setup_queue_handler(self):
        def check_queue():
            while True:
                try:
                    msg_type, content = self.queue.get_nowait()
                    if msg_type == 'log':
                        self.log(f"[INFO] {content}")
                    elif msg_type == 'error':
                        self.log(f"[ERROR] {content}", error=True)
                except queue.Empty:
                    break
            self.root.after(100, check_queue)
        self.root.after(100, check_queue)

    def load_rom(self):
        path = filedialog.askopenfilename(
            filetypes=[("N64 ROMs", "*.n64 *.v64 *.z64"), ("All files", "*.*")]
        )
        if path:
            self.emulator_core = EmulatorCore(self.queue)
            if self.emulator_core.load_rom(path):
                self.start_button.config(state=tk.NORMAL)
                self.stop_button.config(state=tk.DISABLED)

    def start_emulation(self):
        if self.emulator_core:
            self.emulator_thread = threading.Thread(
                target=self.emulator_core.run, 
                daemon=True
            )
            self.emulator_thread.start()
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.log("Emulation started")

    def stop_emulation(self):
        if self.emulator_core:
            self.emulator_core.running = False
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.log("Emulation stopped")

    def log(self, message, error=False):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        if error:
            logging.error(message)
        else:
            logging.info(message)

if __name__ == "__main__":
    root = tk.Tk()
    app = EmulatorGUI(root)
    root.mainloop()
