import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import threading
import webbrowser
import os
import json
import time
import random
from datetime import datetime
from search import perform_google_dork_search_live
from utils import save_results, categorize_url, load_results_structure

class DorkerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Valtus – OSINT Dorker")
        self.geometry("1400x850")
        self.minsize(1000, 700)

        self.category_map = load_results_structure("ResultsStructure.json")
        self.results = []
        self.bulk_vars = {}
        self.search_running = False
        self.stop_flag = False

        self.build_ui()
        self.log("Application started", "INFO")

    def build_ui(self):
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=1)

        top_frame = ctk.CTkFrame(self, corner_radius=10)
        top_frame.grid(row=0, column=0, padx=20, pady=(20,10), sticky="ew")
        top_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(top_frame, text="Target:", font=("Segoe UI", 14, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.target_entry = ctk.CTkEntry(top_frame, width=250, font=("Segoe UI", 14))
        self.target_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.target_entry.insert(0, "example.com")

        ctk.CTkLabel(top_frame, text="Template:", font=("Segoe UI", 14, "bold")).grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.template_var = ctk.StringVar()
        self.template_menu = ctk.CTkOptionMenu(top_frame, variable=self.template_var,
                                               values=self.get_template_list(),
                                               command=self.load_template, width=140)
        self.template_menu.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        self.template_menu.set("Select template")

        self.generate_btn = ctk.CTkButton(top_frame, text="Generate Dorks", command=self.generate_dorks,
                                          font=("Segoe UI", 14, "bold"), width=130)
        self.generate_btn.grid(row=0, column=4, padx=5, pady=5)

        ctk.CTkLabel(top_frame, text="Delay (sec):", font=("Segoe UI", 12, "bold")).grid(row=0, column=5, padx=5, pady=5, sticky="w")
        self.delay_entry = ctk.CTkEntry(top_frame, width=60, font=("Segoe UI", 12))
        self.delay_entry.insert(0, "30")
        self.delay_entry.grid(row=0, column=6, padx=5, pady=5, sticky="w")

        self.tor_var = tk.BooleanVar()
        self.tor_check = ctk.CTkCheckBox(top_frame, text="Tor", variable=self.tor_var,
                                         command=self.toggle_tor, font=("Segoe UI", 12, "bold"), width=60)
        self.tor_check.grid(row=0, column=7, padx=5, pady=5, sticky="w")

        self.proxy_entry = ctk.CTkEntry(top_frame, width=200, font=("Segoe UI", 12), placeholder_text="socks5://127.0.0.1:9050")
        self.proxy_entry.grid(row=0, column=8, padx=5, pady=5, sticky="w")
        self.proxy_entry.insert(0, "socks5://127.0.0.1:9050")
        self.proxy_entry.configure(state="disabled")

        self.search_btn = ctk.CTkButton(top_frame, text="Search All", command=self.start_search,
                                        font=("Segoe UI", 14, "bold"), width=100, fg_color="#2e7d32")
        self.search_btn.grid(row=0, column=9, padx=5, pady=5)

        self.test_btn = ctk.CTkButton(top_frame, text="Test One", command=self.test_single_dork,
                                      font=("Segoe UI", 12, "bold"), width=80, fg_color="#1e5f8e")
        self.test_btn.grid(row=0, column=10, padx=5, pady=5)

        self.stop_btn = ctk.CTkButton(top_frame, text="Stop", command=self.stop_search,
                                      font=("Segoe UI", 14, "bold"), width=80, state="disabled", fg_color="#b71c1c")
        self.stop_btn.grid(row=0, column=11, padx=5, pady=5)

        # Middle frame (dorks + results) unchanged
        middle_frame = ctk.CTkFrame(self, corner_radius=10)
        middle_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        middle_frame.grid_rowconfigure(0, weight=1)
        middle_frame.grid_columnconfigure(0, weight=1)
        middle_frame.grid_columnconfigure(1, weight=2)

        dork_frame = ctk.CTkFrame(middle_frame, corner_radius=10)
        dork_frame.grid(row=0, column=0, padx=(0,5), pady=0, sticky="nsew")
        dork_frame.grid_rowconfigure(0, weight=1)
        dork_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(dork_frame, text="Dorks", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=5, pady=(5,0))
        self.dork_text = ctk.CTkTextbox(dork_frame, font=("Courier New", 12), wrap="none")
        self.dork_text.pack(padx=5, pady=5, fill="both", expand=True)

        results_frame = ctk.CTkFrame(middle_frame, corner_radius=10)
        results_frame.grid(row=0, column=1, padx=(5,0), pady=0, sticky="nsew")
        results_frame.grid_rowconfigure(1, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)

        filter_frame = ctk.CTkFrame(results_frame, fg_color="transparent")
        filter_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        filter_frame.grid_columnconfigure(0, weight=0)
        filter_frame.grid_columnconfigure(1, weight=0)
        filter_frame.grid_columnconfigure(2, weight=1)

        ctk.CTkLabel(filter_frame, text="Category:", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, padx=5)
        self.category_var = ctk.StringVar()
        self.category_menu = ctk.CTkOptionMenu(filter_frame, variable=self.category_var,
                                               values=["All"], command=self.filter_results)
        self.category_menu.grid(row=0, column=1, padx=5)
        self.category_menu.set("All")

        self.progress_label = ctk.CTkLabel(filter_frame, text="Ready", font=("Segoe UI", 12))
        self.progress_label.grid(row=0, column=2, sticky="e", padx=5)

        self.results_scroll = ctk.CTkScrollableFrame(results_frame, label_text="Results")
        self.results_scroll.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        # Log panel (unchanged)
        log_frame = ctk.CTkFrame(self, corner_radius=10)
        log_frame.grid(row=2, column=0, padx=20, pady=(0,20), sticky="ew")
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(0, weight=0)
        log_frame.grid_rowconfigure(1, weight=1)

        log_header = ctk.CTkFrame(log_frame, fg_color="transparent")
        log_header.grid(row=0, column=0, sticky="ew", padx=5, pady=(5,0))
        log_header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(log_header, text="Log Console", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w")
        clear_log_btn = ctk.CTkButton(log_header, text="Clear Log", command=self.clear_log,
                                      font=("Segoe UI", 10), width=80, height=25)
        clear_log_btn.grid(row=0, column=1, sticky="e")

        self.log_text = ctk.CTkTextbox(log_frame, font=("Consolas", 11), height=120, wrap="word")
        self.log_text.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        # Bottom buttons (unchanged)
        bottom_btn_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="transparent")
        bottom_btn_frame.grid(row=3, column=0, padx=20, pady=(0,20), sticky="ew")
        bottom_btn_frame.grid_columnconfigure(3, weight=1)

        self.bulk_open_btn = ctk.CTkButton(bottom_btn_frame, text="Bulk Open Selected", command=self.bulk_open,
                                           font=("Segoe UI", 12, "bold"), width=150)
        self.bulk_open_btn.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.save_btn = ctk.CTkButton(bottom_btn_frame, text="Save Results", command=self.save_results,
                                      font=("Segoe UI", 12, "bold"), width=150)
        self.save_btn.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        self.archive_btn = ctk.CTkButton(bottom_btn_frame, text="Fetch Archive", command=self.open_archive_window,
                                         font=("Segoe UI", 12, "bold"), width=150)
        self.archive_btn.grid(row=0, column=2, padx=10, pady=10, sticky="w")

    def toggle_tor(self):
        if self.tor_var.get():
            self.proxy_entry.delete(0, tk.END)
            self.proxy_entry.insert(0, "socks5://127.0.0.1:9050")
            self.proxy_entry.configure(state="disabled")
            self.log("Tor proxy enabled", "INFO")
        else:
            self.proxy_entry.configure(state="normal")
            self.proxy_entry.delete(0, tk.END)
            self.proxy_entry.insert(0, "")
            self.log("Tor proxy disabled", "INFO")

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] [{level}] {message}\n"
        self.log_text.insert(tk.END, formatted)
        self.log_text.see(tk.END)
        print(formatted.strip())

    def clear_log(self):
        self.log_text.delete("1.0", tk.END)

    def get_template_list(self):
        folder = "dork_templates"
        if not os.path.isdir(folder):
            os.makedirs(folder, exist_ok=True)
            self.create_default_templates(folder)
        return [f for f in os.listdir(folder) if f.endswith(".txt")]

    def create_default_templates(self, folder):
        defaults = {
            "website.txt": "site:site.com (ext:doc OR ext:pdf OR ext:xls OR ext:sql)\n"
                           "site:site.com inurl:admin\n"
                           "site:site.com intitle:\"index of\"",
            "people.txt": "site:*.* \"Name Or Username\"\n"
                          "inurl:\"Name Or Username\" (phone|contact)",
            "socials.txt": "@Facebook Name\n@Twitter Name\n@LinkedIn Name"
        }
        for name, content in defaults.items():
            with open(os.path.join(folder, name), "w", encoding="utf-8") as f:
                f.write(content)

    def load_template(self, choice):
        if not choice or choice == "Select template":
            return
        path = os.path.join("dork_templates", choice)
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.dork_text.delete("1.0", tk.END)
            self.dork_text.insert("1.0", content)
            self.log(f"Loaded template: {choice}", "INFO")
        except Exception as e:
            self.log(f"Failed to load template {choice}: {e}", "ERROR")

    def generate_dorks(self):
        target = self.target_entry.get().strip()
        if not target:
            self.log("Cannot generate dorks: no target entered", "WARNING")
            return
        current = self.dork_text.get("1.0", tk.END)
        replacements = {"site.com": target, "Name Or Username": target, "NAME": target, "TARGET": target}
        new_text = current
        for placeholder, replacement in replacements.items():
            new_text = new_text.replace(placeholder, replacement)
        self.dork_text.delete("1.0", tk.END)
        self.dork_text.insert("1.0", new_text)
        self.log(f"Generated dorks with target '{target}'", "INFO")

    def test_single_dork(self):
        dork_lines = self.dork_text.get("1.0", tk.END).strip().splitlines()
        dorks = [line.strip() for line in dork_lines if line.strip()]
        if not dorks:
            self.log("No dorks to test.", "WARNING")
            return
        self.start_search_with_dorks([dorks[0]])

    def start_search_with_dorks(self, dorks):
        if not dorks:
            self.log("No dorks provided.", "WARNING")
            return
        try:
            delay = float(self.delay_entry.get().strip())
        except ValueError:
            self.log("Invalid delay, using 30s", "WARNING")
            delay = 30.0

        proxy = self.proxy_entry.get().strip() or None
        if proxy:
            self.log(f"Using proxy: {proxy}", "INFO")

        cooldown = random.uniform(30, 60)
        self.log(f"Pre-search cooldown: {cooldown:.1f}s", "INFO")
        self.progress_label.configure(text=f"Cooling down for {int(cooldown)}s...")
        self.search_btn.configure(state="disabled")
        for _ in range(int(cooldown)):
            if self.stop_flag:
                break
            time.sleep(1)
        if self.stop_flag:
            self.search_btn.configure(state="normal")
            return

        self.search_running = True
        self.stop_flag = False
        self.stop_btn.configure(state="normal")
        self.search_btn.configure(state="disabled")
        self.results = []
        self.bulk_vars = {}
        self.progress_label.configure(text="Searching...")
        self.log(f"Starting search with {len(dorks)} dorks, delay={delay}s", "INFO")

        for widget in self.results_scroll.winfo_children():
            widget.destroy()

        threading.Thread(target=self.perform_search, args=(dorks, delay, proxy), daemon=True).start()

    def start_search(self):
        dork_lines = self.dork_text.get("1.0", tk.END).strip().splitlines()
        dorks = [line.strip() for line in dork_lines if line.strip()]
        if not dorks:
            self.log("No dorks to search.", "WARNING")
            return
        self.start_search_with_dorks(dorks)

    def perform_search(self, dorks, delay, proxy):
        total = len(dorks)
        proxies = {"http": proxy, "https": proxy} if proxy else None

        for idx, dork in enumerate(dorks, 1):
            if self.stop_flag:
                self.log("Stopped by user", "INFO")
                break

            self.after(0, lambda i=idx, t=total: self.progress_label.configure(text=f"Dork {i}/{t}"))
            self.log(f"Processing dork {idx}/{total}: {dork[:50]}...", "DEBUG")

            retries = 0
            max_retries = 5
            success = False
            while retries <= max_retries and not success and not self.stop_flag:
                try:
                    for item in perform_google_dork_search_live(dork, num_results=3, pause=delay, proxies=proxies):
                        if self.stop_flag:
                            break
                        item["category"] = categorize_url(item["url"], self.category_map)
                        self.results.append(item)
                        self.after(0, self.add_result_item, item)
                    success = True
                except Exception as e:
                    error_str = str(e)
                    if "429" in error_str or "Too Many Requests" in error_str:
                        retries += 1
                        if retries <= max_retries:
                            wait_time = delay * (2 ** retries) + random.uniform(0, 10)
                            self.log(f"429. Retry {retries}/{max_retries} after {wait_time:.1f}s", "WARNING")
                            for _ in range(int(wait_time)):
                                if self.stop_flag:
                                    break
                                time.sleep(1)
                        else:
                            self.log(f"Max retries for dork: {dork[:50]}...", "ERROR")
                    else:
                        self.log(f"Error: {e}", "ERROR")
                        break

            if idx < total and not self.stop_flag:
                jitter = random.uniform(0, 10)
                total_delay = delay + jitter
                self.log(f"Waiting {total_delay:.1f}s before next dork", "DEBUG")
                time.sleep(total_delay)

        self.search_running = False
        self.after(0, self.finish_search)

    def add_result_item(self, item):
        url = item["url"]
        title = item.get("title", "No Title")
        category = item.get("category", "Other")

        frame = ctk.CTkFrame(self.results_scroll, fg_color="transparent")
        frame.pack(pady=2, fill="x")

        var = tk.BooleanVar()
        self.bulk_vars[url] = var
        chk = ctk.CTkCheckBox(frame, text="", variable=var, width=20)
        chk.pack(side="left", padx=(0,5))

        btn_text = f"{title[:60]}..." if len(title) > 60 else title
        btn = ctk.CTkButton(frame, text=btn_text,
                            command=lambda u=url: webbrowser.open(u),
                            fg_color="transparent", hover_color="#333333",
                            anchor="w", font=("Segoe UI", 12))
        btn.pack(side="left", fill="x", expand=True)

        cat_label = ctk.CTkLabel(frame, text=category, font=("Segoe UI", 10, "bold"),
                                 fg_color="#2b2b2b", corner_radius=5, padx=5)
        cat_label.pack(side="right", padx=5)

        categories = set(item["category"] for item in self.results)
        categories.add("All")
        self.category_menu.configure(values=sorted(categories))
        if self.category_var.get() not in categories:
            self.category_var.set("All")

    def finish_search(self):
        self.stop_btn.configure(state="disabled")
        self.search_btn.configure(state="normal")
        self.progress_label.configure(text=f"Done. Found {len(self.results)} results.")
        self.log(f"Search finished. Total: {len(self.results)}", "INFO")
        self.filter_results()

    def stop_search(self):
        self.stop_flag = True
        self.stop_btn.configure(state="disabled")
        self.progress_label.configure(text="Stopping...")

    def filter_results(self, *args):
        selected = self.category_var.get()
        for widget in self.results_scroll.winfo_children():
            widget.destroy()
        filtered = self.results if selected == "All" else [r for r in self.results if r.get("category") == selected]
        for item in filtered:
            self.add_result_item(item)

    def bulk_open(self):
        opened = 0
        for url, var in self.bulk_vars.items():
            if var.get():
                webbrowser.open(url)
                opened += 1
        self.log(f"Opened {opened} selected URLs", "INFO")

    def save_results(self):
        if not self.results:
            self.log("No results to save", "WARNING")
            return
        grouped = {}
        for item in self.results:
            cat = item.get("category", "Other")
            grouped.setdefault(cat, []).append(item)
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if file_path:
            save_results(grouped, file_path)
            self.log(f"Saved to {file_path}", "INFO")

    def open_archive_window(self):
        win = ctk.CTkToplevel(self)
        win.title("Archive Fetcher")
        win.geometry("700x550")

        frame = ctk.CTkFrame(win)
        frame.pack(padx=20, pady=20, fill="x")
        ctk.CTkLabel(frame, text="Domain:", font=("Segoe UI", 12, "bold")).pack(side="left", padx=5)
        domain_entry = ctk.CTkEntry(frame, width=300)
        domain_entry.pack(side="left", padx=10, fill="x", expand=True)
        domain_entry.insert(0, self.target_entry.get())

        progress_label = ctk.CTkLabel(win, text="")
        progress_label.pack(pady=5)

        list_frame = ctk.CTkFrame(win)
        list_frame.pack(padx=20, pady=10, fill="both", expand=True)
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                             bg="#2E2E2E", fg="white", selectbackground="#555", font=("Courier New", 10))
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=listbox.yview)

        def fetch_archive():
            domain = domain_entry.get().strip()
            if not domain:
                self.log("Archive: no domain", "WARNING")
                return
            progress_label.configure(text="Fetching...")
            listbox.delete(0, tk.END)
            try:
                import requests
                base = "https://web.archive.org/cdx/search/cdx"
                params = {"url": f"{domain}*", "output": "text", "fl": "original", "collapse": "urlkey"}
                with requests.get(base, params=params, stream=True, timeout=30) as r:
                    r.raise_for_status()
                    count = 0
                    for line in r.iter_lines(decode_unicode=True):
                        if line:
                            url = line.strip()
                            listbox.insert(tk.END, url)
                            count += 1
                            if count % 1000 == 0:
                                progress_label.configure(text=f"{count} links...")
                progress_label.configure(text=f"Done. Total: {count}")
                self.log(f"Archive fetched {count} URLs for {domain}", "INFO")
            except Exception as e:
                self.log(f"Archive error: {e}", "ERROR")
                progress_label.configure(text="Error")

        fetch_btn = ctk.CTkButton(win, text="Fetch Archive", command=fetch_archive,
                                  font=("Segoe UI", 12, "bold"))
        fetch_btn.pack(pady=10)

        def bulk_open_archive():
            selected = listbox.curselection()
            for idx in selected:
                url = listbox.get(idx)
                if url.startswith("http"):
                    webbrowser.open(url)
            self.log(f"Opened {len(selected)} archive URLs", "INFO")

        bulk_btn = ctk.CTkButton(win, text="Bulk Open Selected", command=bulk_open_archive,
                                 font=("Segoe UI", 12, "bold"))
        bulk_btn.pack(pady=10)


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    app = DorkerGUI()
    app.mainloop()
