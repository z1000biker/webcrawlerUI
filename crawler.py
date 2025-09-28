import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import requests
from bs4 import BeautifulSoup
import trafilatura
from urllib.parse import urljoin, urlparse, urldefrag
from collections import deque
import time
import urllib.robotparser
import threading

class WebCrawlerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Web Content Extractor")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Configure styles
        self.style = ttk.Style()
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TButton', font=('Arial', 10))
        self.style.configure('TLabel', font=('Arial', 10), background='#f0f0f0')
        self.style.configure('TEntry', font=('Arial', 10))
        
        # Create main frames
        self.create_frames()
        
        # Create input fields
        self.create_input_fields()
        
        # Create control buttons
        self.create_control_buttons()
        
        # Create progress display
        self.create_progress_display()
        
        # Create status bar
        self.create_status_bar()
        
        # Initialize variables
        self.results = {}
        self.crawling = False
        self.stop_requested = False

    def create_frames(self):
        # Input frame
        self.input_frame = ttk.Frame(self.root, padding="10")
        self.input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Control frame
        self.control_frame = ttk.Frame(self.root, padding="10")
        self.control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Progress frame
        self.progress_frame = ttk.Frame(self.root, padding="10")
        self.progress_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Status frame
        self.status_frame = ttk.Frame(self.root, padding="5")
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=5)

    def create_input_fields(self):
        # URL input
        ttk.Label(self.input_frame, text="Starting URL:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.url_entry = ttk.Entry(self.input_frame, width=70)
        self.url_entry.grid(row=0, column=1, sticky=tk.EW, pady=5)
        self.url_entry.insert(0, "https://example.com/index.html")
        
        # Parameters frame
        params_frame = ttk.LabelFrame(self.input_frame, text="Crawl Parameters", padding="5")
        params_frame.grid(row=1, column=0, columnspan=2, sticky=tk.EW, pady=10)
        
        # Max depth
        ttk.Label(params_frame, text="Max Depth:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.depth_var = tk.IntVar(value=2)
        depth_spin = ttk.Spinbox(params_frame, from_=1, to=5, textvariable=self.depth_var, width=5)
        depth_spin.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Max pages
        ttk.Label(params_frame, text="Max Pages:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.pages_var = tk.IntVar(value=50)
        pages_spin = ttk.Spinbox(params_frame, from_=10, to=200, textvariable=self.pages_var, width=5)
        pages_spin.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        
        # Delay
        ttk.Label(params_frame, text="Delay (sec):").grid(row=0, column=4, sticky=tk.W, padx=5, pady=5)
        self.delay_var = tk.DoubleVar(value=1.0)
        delay_spin = ttk.Spinbox(params_frame, from_=0.5, to=5.0, increment=0.5, textvariable=self.delay_var, width=5)
        delay_spin.grid(row=0, column=5, sticky=tk.W, padx=5, pady=5)
        
        # Configure column weights
        self.input_frame.columnconfigure(1, weight=1)
        params_frame.columnconfigure(6, weight=1)

    def create_control_buttons(self):
        # Start button
        self.start_button = ttk.Button(self.control_frame, text="Start Crawling", command=self.start_crawling)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        # Stop button
        self.stop_button = ttk.Button(self.control_frame, text="Stop", command=self.stop_crawling, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Save button
        self.save_button = ttk.Button(self.control_frame, text="Save Results", command=self.save_results, state=tk.DISABLED)
        self.save_button.pack(side=tk.LEFT, padx=5)
        
        # Clear button
        self.clear_button = ttk.Button(self.control_frame, text="Clear", command=self.clear_results)
        self.clear_button.pack(side=tk.LEFT, padx=5)
        
        # Configure frame to expand
        self.control_frame.columnconfigure(0, weight=1)

    def create_progress_display(self):
        # Progress label
        self.progress_label = ttk.Label(self.progress_frame, text="Crawl Progress:")
        self.progress_label.pack(anchor=tk.W, pady=5)
        
        # Progress text area
        self.progress_text = scrolledtext.ScrolledText(self.progress_frame, wrap=tk.WORD, height=15)
        self.progress_text.pack(fill=tk.BOTH, expand=True)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(self.progress_frame, orient=tk.HORIZONTAL, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=5)

    def create_status_bar(self):
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(self.status_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X)

    def log_message(self, message):
        """Add a message to the progress text area"""
        self.progress_text.insert(tk.END, f"{message}\n")
        self.progress_text.see(tk.END)
        self.root.update_idletasks()

    def update_status(self, status):
        """Update the status bar"""
        self.status_var.set(status)
        self.root.update_idletasks()

    def update_progress(self, value, maximum):
        """Update the progress bar"""
        self.progress_bar['maximum'] = maximum
        self.progress_bar['value'] = value
        self.root.update_idletasks()

    def start_crawling(self):
        """Start the crawling process in a separate thread"""
        if self.crawling:
            messagebox.showwarning("Warning", "Crawling is already in progress!")
            return
            
        # Get input values
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a valid URL!")
            return
            
        max_depth = self.depth_var.get()
        max_pages = self.pages_var.get()
        delay = self.delay_var.get()
        
        # Reset variables
        self.results = {}
        self.stop_requested = False
        self.crawling = True
        
        # Clear previous results
        self.progress_text.delete(1.0, tk.END)
        
        # Update UI
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.save_button.config(state=tk.DISABLED)
        self.update_status("Crawling in progress...")
        
        # Start crawling in a separate thread
        self.crawl_thread = threading.Thread(
            target=self.crawl_wrapper,
            args=(url, max_depth, max_pages, delay)
        )
        self.crawl_thread.daemon = True
        self.crawl_thread.start()

    def crawl_wrapper(self, url, max_depth, max_pages, delay):
        """Wrapper for the crawl function to handle exceptions and UI updates"""
        try:
            self.results = self.crawl(url, max_depth, max_pages, delay)
            
            if not self.stop_requested:
                self.log_message("\nCrawling completed successfully!")
                self.update_status(f"Completed! Extracted text from {len(self.results)} pages.")
                self.save_button.config(state=tk.NORMAL)
        except Exception as e:
            self.log_message(f"\nError during crawling: {str(e)}")
            self.update_status(f"Error: {str(e)}")
        finally:
            self.crawling = False
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.update_progress(0, 100)

    def stop_crawling(self):
        """Stop the crawling process"""
        if self.crawling:
            self.stop_requested = True
            self.log_message("\nStopping crawl process...")
            self.update_status("Stopping crawl...")
            self.stop_button.config(state=tk.DISABLED)

    def clear_results(self):
        """Clear the progress text area and results"""
        self.progress_text.delete(1.0, tk.END)
        self.results = {}
        self.save_button.config(state=tk.DISABLED)
        self.update_status("Results cleared")
        self.update_progress(0, 100)

    def save_results(self):
        """Save the extracted text to a file"""
        if not self.results:
            messagebox.showwarning("Warning", "No results to save!")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Save Extracted Text"
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for url, text in self.results.items():
                    f.write(f"URL: {url}\n\n")
                    f.write(text)
                    f.write("\n\n" + "="*80 + "\n\n")
            
            messagebox.showinfo("Success", f"Results saved to {file_path}")
            self.update_status(f"Results saved to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save results: {str(e)}")
            self.update_status(f"Error saving file: {str(e)}")

    # Web crawling functions (same as before)
    def normalize_url(self, url, base_url=None):
        if base_url:
            url = urljoin(base_url, url)
        url, _ = urldefrag(url)
        url = url.rstrip('/')
        return url

    def is_same_domain(self, url, base_domain):
        parsed = urlparse(url)
        return parsed.netloc == base_domain

    def can_fetch(self, url, user_agent='*'):
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        rp = urllib.robotparser.RobotFileParser()
        try:
            rp.set_url(urljoin(base_url, 'robots.txt'))
            rp.read()
            return rp.can_fetch(user_agent, url)
        except Exception:
            return True

    def crawl(self, start_url, max_depth=2, max_pages=50, delay=1):
        base_domain = urlparse(start_url).netloc
        visited = set()
        queue = deque()
        queue.append((start_url, 0))
        results = {}

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }

        self.log_message(f"Starting crawl from: {start_url}")
        self.log_message(f"Max depth: {max_depth}, Max pages: {max_pages}, Delay: {delay}s")
        self.log_message("-" * 80)

        page_count = 0
        while queue and page_count < max_pages and not self.stop_requested:
            url, depth = queue.popleft()
            normalized_url = self.normalize_url(url)
            
            if normalized_url in visited:
                continue
            visited.add(normalized_url)

            if depth > max_depth:
                continue

            if not self.can_fetch(normalized_url, headers['User-Agent']):
                self.log_message(f"Skipping (blocked by robots.txt): {normalized_url}")
                continue

            try:
                self.log_message(f"Crawling ({depth}): {normalized_url}")
                self.update_progress(page_count, max_pages)
                
                response = requests.get(normalized_url, headers=headers, timeout=10)
                content_type = response.headers.get('Content-Type', '')
                if 'text/html' not in content_type:
                    self.log_message(f"Skipping (non-HTML content): {normalized_url}")
                    continue

                text = trafilatura.extract(response.text)
                if text:
                    results[normalized_url] = text
                    page_count += 1
                    self.log_message(f"✓ Extracted content ({page_count}/{max_pages})")
                else:
                    self.log_message(f"⚠ No content extracted")

                if depth == max_depth:
                    continue

                soup = BeautifulSoup(response.text, 'html.parser')
                links_found = 0
                for a_tag in soup.find_all('a', href=True):
                    href = a_tag['href']
                    abs_url = self.normalize_url(href, normalized_url)
                    if self.is_same_domain(abs_url, base_domain) and abs_url not in visited:
                        queue.append((abs_url, depth + 1))
                        links_found += 1
                
                self.log_message(f"Found {links_found} new links")

                time.sleep(delay)

            except Exception as e:
                self.log_message(f"✗ Error processing {url}: {str(e)}")
                continue

        self.log_message("-" * 80)
        self.log_message(f"Crawl completed. Extracted text from {len(results)} pages.")
        return results

def main():
    root = tk.Tk()
    app = WebCrawlerGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()
