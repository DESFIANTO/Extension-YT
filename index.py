import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import yt_dlp
import threading
import os
import subprocess
import traceback

class YouTubeHDDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube HD Downloader (Fixed)")
        self.root.geometry("600x450")
        
        # Variabel
        self.url_var = tk.StringVar()
        self.save_path_var = tk.StringVar(value=os.path.expanduser("~/Downloads"))
        self.status_var = tk.StringVar()
        self.quality_var = tk.StringVar(value="1080p")
        self.codec_var = tk.StringVar(value="best")  # Default ke codec terbaik
        self.fps_var = tk.StringVar(value="best")
        
        # Setup UI
        self.setup_ui()
        
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="YouTube HD Downloader (Fixed Errors)", 
                 font=('Helvetica', 14, 'bold')).grid(row=0, column=0, columnspan=3, pady=10)
        
        # URL Input
        ttk.Label(main_frame, text="YouTube URL:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.url_var, width=50).grid(row=1, column=1, columnspan=2, sticky=tk.EW)
        
        # Quality Options
        ttk.Label(main_frame, text="Resolution:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Combobox(main_frame, textvariable=self.quality_var, 
                    values=["720p", "1080p", "1440p", "2160p", "best"], state="readonly").grid(row=2, column=1, sticky=tk.W)
        
        ttk.Label(main_frame, text="Video Codec:").grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Combobox(main_frame, textvariable=self.codec_var, 
                    values=["h264", "vp9", "av01", "best"], state="readonly").grid(row=3, column=1, sticky=tk.W)
        
        # Save Path
        ttk.Label(main_frame, text="Save Location:").grid(row=4, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.save_path_var, width=40).grid(row=4, column=1, sticky=tk.EW)
        ttk.Button(main_frame, text="Browse", command=self.browse_folder).grid(row=4, column=2, sticky=tk.W, padx=5)
        
        # Status
        ttk.Label(main_frame, text="Status:").grid(row=5, column=0, sticky=tk.W, pady=5)
        ttk.Label(main_frame, textvariable=self.status_var, wraplength=400).grid(row=5, column=1, columnspan=2, sticky=tk.W)
        
        # Progress
        self.progress = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, length=450, mode='determinate')
        self.progress.grid(row=6, column=0, columnspan=3, pady=15)
        
        # Download Button
        ttk.Button(main_frame, text="Download HD Video", command=self.start_download, 
                  style='Accent.TButton').grid(row=7, column=0, columnspan=3, pady=10)
        
        # Configure grid
        main_frame.columnconfigure(1, weight=1)
        
        # Style for accent button
        style = ttk.Style()
        style.configure('Accent.TButton', font=('Helvetica', 10, 'bold'))
    
    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.save_path_var.set(folder)
    
    def start_download(self):
        threading.Thread(target=self.download_hd_video, daemon=True).start()
    
    def download_hd_video(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter YouTube URL")
            return
            
        save_path = self.save_path_var.get()
        if not save_path:
            messagebox.showerror("Error", "Please select save location")
            return
            
        try:
            self.status_var.set("Preparing download...")
            self.root.update()
            
            quality = self.quality_var.get()
            codec = self.codec_var.get()
            
            # Format selection with fallback options
            format_selector = []
            
            # Try user's preferred codec first
            if codec != "best":
                format_selector.append(
                    f"bestvideo[height<={quality[:-1]}][vcodec*={codec}]+bestaudio/best"
                )
            
            # Fallback to any codec with preferred resolution
            format_selector.append(
                f"bestvideo[height<={quality[:-1]}]+bestaudio/best"
            )
            
            # Final fallback
            format_selector.append("best")
            
            ydl_opts = {
                'outtmpl': os.path.join(save_path, '%(title)s [%(resolution)s].%(ext)s'),
                'format': '/'.join(format_selector),
                'merge_output_format': 'mkv',
                'progress_hooks': [self.progress_hook],
                'noplaylist': True,
                'no_warnings': False,
                'ignoreerrors': True,  # Jangan abort saat ada error
                'quiet': False,
                'verbose': True,
                'ffmpeg_location': self.find_ffmpeg(),
                'postprocessor_args': [
                    '-crf', '22',  # Balance antara kualitas dan ukuran file
                ],
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self.status_var.set("Starting download...")
                ydl.download([url])
                
            self.status_var.set("Download completed!")
            messagebox.showinfo("Success", "Video downloaded successfully!")
            
        except Exception as e:
            error_msg = f"Error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            self.status_var.set("Download failed")
            messagebox.showerror("Download Error", error_msg)
        finally:
            self.progress['value'] = 0
    
    def find_ffmpeg(self):
        try:
            subprocess.run(['ffmpeg', '-version'], check=True, 
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return None
        except:
            common_paths = [
                '/usr/bin/ffmpeg',
                '/usr/local/bin/ffmpeg',
                'C:\\ffmpeg\\bin\\ffmpeg.exe',
                'C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe'
            ]
            for path in common_paths:
                if os.path.exists(path):
                    return path
            self.status_var.set("FFmpeg not found - quality may be affected")
            return None
    
    def progress_hook(self, d):
        if d['status'] == 'downloading':
            if d.get('total_bytes'):
                percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
            elif d.get('total_bytes_estimate'):
                percent = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
            else:
                percent = 0
                
            self.progress['value'] = percent
            self.status_var.set(
                f"Downloading {d.get('_percent_str', '')} | "
                f"Speed: {d.get('_speed_str', '')} | "
                f"ETA: {d.get('_eta_str', '')}"
            )
            self.root.update_idletasks()
        elif d['status'] == 'error':
            self.status_var.set(f"Error: {d.get('msg', 'Unknown error')}")

if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeHDDownloader(root)
    root.mainloop()