import os
import shutil
import threading
import tkinter as tk
from tkinter import filedialog, scrolledtext
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


def sync_all(src, dest):
    if not os.path.exists(src):
        raise ValueError(f"Source directory '{src}' does not exist")
    os.makedirs(dest, exist_ok=True)
    for root, dirs, files in os.walk(src):
        rel = os.path.relpath(root, src)
        dest_root = os.path.join(dest, rel)
        os.makedirs(dest_root, exist_ok=True)
        for f in files:
            src_file = os.path.join(root, f)
            dest_file = os.path.join(dest_root, f)
            shutil.copy2(src_file, dest_file)

class MirrorHandler(FileSystemEventHandler):
    def __init__(self, src_dir, dest_dir, log_func):
        self.src_dir = os.path.abspath(src_dir)
        self.dest_dir = os.path.abspath(dest_dir)
        self.log = log_func

    def on_created(self, event):
        self._handle_event(event, "created")

    def on_modified(self, event):
        self._handle_event(event, "modified")

    def on_deleted(self, event):
        self._handle_event(event, "deleted")

    def on_moved(self, event):
        rel_src = os.path.relpath(event.src_path, self.src_dir)
        rel_dest = os.path.relpath(event.dest_path, self.src_dir)
        src_target = os.path.join(self.dest_dir, rel_src)
        dest_target = os.path.join(self.dest_dir, rel_dest)
        if os.path.exists(src_target):
            shutil.move(src_target, dest_target)
        self.log(f"moved: {rel_src} -> {rel_dest}")

    def _handle_event(self, event, action):
        rel = os.path.relpath(event.src_path, self.src_dir)
        target_path = os.path.join(self.dest_dir, rel)
        if event.is_directory:
            if action == "created":
                os.makedirs(target_path, exist_ok=True)
            elif action == "deleted":
                shutil.rmtree(target_path, ignore_errors=True)
            self.log(f"{action}: {rel}/")
            return
        if action == "created" or action == "modified":
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            try:
                shutil.copy2(event.src_path, target_path)
            except FileNotFoundError:
                return
        elif action == "deleted":
            if os.path.exists(target_path):
                os.remove(target_path)
        self.log(f"{action}: {rel}")

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Directory Mirror Sync")
        self.src_dir = ""
        self.dest_dir = ""
        self.observer = None

        tk.Button(root, text="Select Source", command=self.select_source).pack()
        self.src_entry = tk.Entry(root, width=60)
        self.src_entry.pack()

        tk.Button(root, text="Select Target", command=self.select_dest).pack()
        self.dest_entry = tk.Entry(root, width=60)
        self.dest_entry.pack()

        self.start_btn = tk.Button(root, text="Start Sync", command=self.start_sync)
        self.start_btn.pack()
        self.stop_btn = tk.Button(root, text="Stop Sync", command=self.stop_sync, state="disabled")
        self.stop_btn.pack()

        self.status = scrolledtext.ScrolledText(root, width=60, height=20, state="disabled")
        self.status.pack()

    def select_source(self):
        path = filedialog.askdirectory()
        if path:
            self.src_dir = path
            self.src_entry.delete(0, tk.END)
            self.src_entry.insert(0, path)

    def select_dest(self):
        path = filedialog.askdirectory()
        if path:
            self.dest_dir = path
            self.dest_entry.delete(0, tk.END)
            self.dest_entry.insert(0, path)

    def log(self, message):
        self.root.after(0, self._append_log, message)

    def _append_log(self, message):
        self.status.config(state="normal")
        self.status.insert(tk.END, message + "\n")
        self.status.see(tk.END)
        self.status.config(state="disabled")

    def start_sync(self):
        if not self.src_dir or not self.dest_dir:
            self.log("Please select both source and target directories.")
            return
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.log("Starting initial sync...")
        sync_all(self.src_dir, self.dest_dir)
        self.log("Initial sync completed.")
        handler = MirrorHandler(self.src_dir, self.dest_dir, self.log)
        self.observer = Observer()
        self.observer.schedule(handler, self.src_dir, recursive=True)
        self.observer.start()
        self.log("Watching for changes...")

    def stop_sync(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.log("Sync stopped.")

    def on_close(self):
        self.stop_sync()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = App(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()

if __name__ == "__main__":
    main()
