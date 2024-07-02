import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from pathlib import Path
import yt_dlp as youtube_dl
import vlc
import pygame

class RigoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Rigo - YouTube Downloader and Player")
        self.root.geometry("1120x470")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        pygame.mixer.init()

        # Left side: Download and output folder selection
        self.left_frame = tk.Frame(root)
        self.left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.url_label = tk.Label(self.left_frame, text="YouTube URL:")
        self.url_label.grid(row=0, column=0, pady=5, padx=10, sticky=tk.W)

        self.url_entry = tk.Entry(self.left_frame, width=50)
        self.url_entry.grid(row=0, column=1, pady=5, padx=10)

        self.file_type_label = tk.Label(self.left_frame, text="File Type:")
        self.file_type_label.grid(row=1, column=0, pady=5, padx=10, sticky=tk.W)

        self.file_type_var = tk.StringVar()
        self.file_type_combo = ttk.Combobox(self.left_frame, width=15, textvariable=self.file_type_var, state="readonly")
        self.file_type_combo['values'] = ('MP3', 'MP4')
        self.file_type_combo.current(0)
        self.file_type_combo.grid(row=1, column=1, pady=5, padx=10)

        self.download_button = tk.Button(self.left_frame, text="Download", command=self.download_file)
        self.download_button.grid(row=0, column=2, rowspan=2, pady=5, padx=10)

        self.output_label = tk.Label(self.left_frame, text="Output Folder:")
        self.output_label.grid(row=2, column=0, pady=5, padx=10, sticky=tk.W)

        self.output_entry = tk.Entry(self.left_frame, width=50)
        self.output_entry.grid(row=2, column=1, pady=5, padx=10)

        self.output_button = tk.Button(self.left_frame, text="Browse", command=self.browse_output_folder)
        self.output_button.grid(row=2, column=2, pady=5, padx=10)

        self.status_label = tk.Label(self.left_frame, text="")
        self.status_label.grid(row=3, column=0, columnspan=3, pady=5, padx=10)

        self.file_list_label = tk.Label(self.left_frame, text="Output Folder Contents:")
        self.file_list_label.grid(row=4, column=0, columnspan=2, pady=5, padx=10, sticky=tk.W)

        self.file_listbox = tk.Listbox(self.left_frame, width=70, height=10)
        self.file_listbox.grid(row=5, column=0, columnspan=3, pady=5, padx=10)
        self.file_listbox.bind("<Double-Button-1>", self.play_selected_file)

        music_folder = Path.home() / "Music"
        self.output_entry.insert(0, str(music_folder))

        # Right side: Media player and title display
        self.right_frame = tk.Frame(root, bg="black")
        self.right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        aspect_ratio = 16 / 9
        window_width = 800
        window_height = 600
        self.video_width = int(window_width * 0.7)
        self.video_height = int(self.video_width / aspect_ratio)

        self.video_frame = tk.Frame(self.right_frame, width=self.video_width, height=self.video_height, bg="black")
        self.video_frame.pack(pady=20)

        self.media_title_label = tk.Label(self.right_frame, text="", fg="white", bg="black", font=("Arial", 12, "bold"))
        self.media_title_label.pack(pady=10)

        self.play_pause_button = tk.Button(self.right_frame, text="Pause", command=self.toggle_play_pause)
        self.play_pause_button.pack(pady=10)

        self.instance = vlc.Instance("--no-xlib")
        self.player = self.instance.media_player_new()
        self.playing = False
        self.paused = False

    def browse_output_folder(self):
        folder_selected = filedialog.askdirectory()
        self.output_entry.delete(0, tk.END)
        self.output_entry.insert(0, folder_selected)
        self.update_file_list()

    def download_file(self):
        url = self.url_entry.get()
        output_folder = self.output_entry.get()
        file_type = self.file_type_var.get().lower()

        if not url or not output_folder:
            messagebox.showerror("Error", "Please enter a URL and select an output folder")
            return

        try:
            self.status_label.config(text="Downloading...")

            ydl_opts = {
                'format': 'bestaudio/best' if file_type == 'mp3' else 'best',
                'outtmpl': os.path.join(output_folder, '%(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }] if file_type == 'mp3' else [],
                'noplaylist': True,
            }

            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            self.status_label.config(text="Download complete!")
            self.update_file_list()
        except youtube_dl.utils.DownloadError as e:
            messagebox.showerror("Error", f"Download error: {e}")
            self.status_label.config(text="")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
            self.status_label.config(text="")

    def update_file_list(self):
        output_folder = self.output_entry.get()
        self.file_listbox.delete(0, tk.END)

        try:
            files = os.listdir(output_folder)
            for file in files:
                if file.lower().endswith(".mp3") or file.lower().endswith(".mp4"):
                    self.file_listbox.insert(tk.END, file)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to list files: {e}")

    def play_selected_file(self, event):
        selected_file = self.file_listbox.get(tk.ACTIVE)
        file_path = os.path.join(self.output_entry.get(), selected_file)

        if selected_file.lower().endswith(".mp3"):
            self.play_mp3(file_path)
            self.media_title_label.config(text=f"Now playing: {os.path.basename(file_path)}")
        elif selected_file.lower().endswith(".mp4"):
            self.play_mp4(file_path)
            self.media_title_label.config(text=f"Now playing: {os.path.basename(file_path)}")

    def play_mp3(self, file_path):
        self.stop_media()
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        self.playing = True
        self.paused = False

    def play_mp4(self, file_path):
        self.stop_media()
        try:
            media = self.instance.media_new(file_path)
            self.player.set_media(media)
            self.player.set_hwnd(self.video_frame.winfo_id())
            self.player.play()
            self.playing = True
            self.paused = False
        except Exception as e:
            messagebox.showerror("Error", f"Failed to play MP4: {e}")

    def toggle_play_pause(self):
        if self.playing:
            if self.paused:
                if pygame.mixer.music.get_busy():
                    pygame.mixer.music.unpause()
                else:
                    self.player.play()
                self.play_pause_button.config(text="Pause")
                self.paused = False
            else:
                if pygame.mixer.music.get_busy():
                    pygame.mixer.music.pause()
                else:
                    self.player.pause()
                self.play_pause_button.config(text="Play")
                self.paused = True

    def stop_media(self):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        if self.player.is_playing():
            self.player.stop()
        self.playing = False
        self.paused = False

    def on_closing(self):
        self.stop_media()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = RigoApp(root)
    root.mainloop()
