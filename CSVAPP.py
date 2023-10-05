import tkinter as tk
from tkinter import ttk
import sv_ttk
import requests
import pandas as pd
from io import StringIO
from datetime import datetime
import threading
from tkinter import messagebox
from tkcalendar import DateEntry
import os
from sys import platform

class CSVApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CSV Title Viewer")
        def resource_path(relative_path):
            try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
                base_path = sys._MEIPASS
            except Exception:
                base_path = os.path.abspath(".")
                
            return os.path.join(base_path, relative_path)

        # Main Frame with padding
        main_frame = ttk.Frame(root)
        main_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        # Create a frame for search label and entry within the main frame
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(pady=10, fill=tk.X)
        iconPath = resource_path('targetIcon.ico')
        self.root.iconbitmap(iconPath)

        # Create Search Label and Entry within the frame
        ttk.Label(search_frame, text="Search Title:").pack(side=tk.LEFT, padx=5)  # Packed to the left
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)  # Packed to the left, next to the label
        self.search_entry.bind("<KeyRelease>", self.filter_titles)
        
        # Create Treeview
        self.tree = ttk.Treeview(main_frame, columns=('Title', 'Activity Type', 'GeoTarget', 'URLs', 'Live', 'End Date'), show='headings')
        self.tree.heading('Title', text='Title')
        self.tree.heading('Activity Type', text='Activity Type')
        self.tree.column('Activity Type', width=100)  # Adjust the width as needed
        self.tree.heading('GeoTarget', text='GeoTarget')
        self.tree.column('GeoTarget', width=80)  # Adjust the width as needed
        self.tree.heading('URLs', text='URLs')  # Hidden from view
        self.tree.heading('Live', text='Live')  # Hidden from view
        self.tree.heading('End Date', text='End Date')  # Hidden from view
        self.tree.column('URLs', width=0, stretch=tk.NO)  
        self.tree.column('Live', width=0, stretch=tk.NO)  
        self.tree.column('End Date', width=0, stretch=tk.NO)  # Hide the End Date column
        self.tree.pack(pady=20, fill=tk.BOTH, expand=True)
        self.tree.bind("<ButtonRelease-1>", self.on_item_click)
        
        # Add a Scrollbar
        self.scrollbar = ttk.Scrollbar(main_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Text widget to display multiple URLs and live status
        self.info_text = tk.Text(main_frame, height=7)
        self.info_text.pack(pady=20, fill=tk.BOTH)
        
        self.add_button = ttk.Button(main_frame, text="Add New Entry", command=self.open_add_entry_popup)
        self.add_button.pack(pady=10)
        self.refresh_button = ttk.Button(main_frame, text="Refresh Data", command=self.refresh_data)
        self.refresh_button.pack(pady=10)

        
        # Fetch and Load CSV data
        self.load_data()


    def load_data(self):
        url = "http://target.mts-studios.com/download"
        headers = {
            "Authorization": "Bearer 76cdc8491313c226dd2ffac76e1b544d"
        }
        response = requests.get(url, headers=headers)
    
        # Check for successful response before processing the CSV data
        if response.status_code == 200:
            csv_data = StringIO(response.text)
            self.df = pd.read_csv(csv_data, sep=',')
            self.populate_tree()
        else:
            # Handle potential error (e.g., invalid token, server error, etc.)
            print(f"Error {response.status_code}: {response.text}")

    def populate_tree(self):
        for _, row in self.df.iterrows():
            title = row.iloc[0]
            urls = row.iloc[1]
            live_status = row.iloc[2] if len(row) > 2 else "Unknown"
            end_date = row.iloc[3] if len(row) > 3 else "N/A"  # Get end date or set to N/A if missing
            
            # Check if the end date has passed and is marked as live
            is_expired = False
            if str(live_status).lower() == "true" and end_date != "N/A" and isinstance(end_date, str):
                try:
                    date_format = "%Y-%m-%d"  # Assuming the date format in the CSV is 'YYYY-MM-DD'
                    end_date_obj = datetime.strptime(end_date, date_format)
                    if end_date_obj.date() < datetime.now().date():
                        is_expired = True
                except ValueError:
                    pass


            activity_type = row.iloc[1]
            geo_target = row.iloc[2]
            item = self.tree.insert('', tk.END, values=(title, activity_type, geo_target, urls, live_status, end_date))
            
            # Visual indication based on live status and expiration
            if is_expired:
                self.tree.item(item, tags='expired')
            elif str(live_status).lower() == "true":
                self.tree.item(item, tags='live')
            else:
                self.tree.item(item, tags='not_live')

        self.tree.tag_configure('live', foreground='green')
        self.tree.tag_configure('not_live', foreground='red')
        self.tree.tag_configure('expired', foreground='orange', background='#2c2c2c')  # Highlight with a different color


    def filter_titles(self, event):
        search_term = self.search_var.get().lower()
        self.tree.delete(*self.tree.get_children())
    
        # Filter data where title, URL or End Date contains the search term
        filtered_data = self.df[(self.df.iloc[:, 0].str.lower().str.contains(search_term)) |
                                (self.df.iloc[:, 1].str.lower().str.contains(search_term)) |
                                (self.df.iloc[:, 3].astype(str).str.lower().str.contains(search_term))]  # Add end date to search
        
        for _, row in filtered_data.iterrows():
            title = row.iloc[0]
            urls = row.iloc[1]
            live_status = row.iloc[2] if len(row) > 2 else "Unknown"  # Added safety check

            item = self.tree.insert('', tk.END, values=(title, urls, live_status))
            if str(live_status).lower() == "true":
                self.tree.item(item, tags='live')
            else:
                self.tree.item(item, tags='not_live')


    def on_item_click(self, event):
        selected_item = self.tree.selection()[0]
        urls = self.tree.item(selected_item, "values")[1]
        live_status = self.tree.item(selected_item, "values")[2]
        end_date = self.tree.item(selected_item, "values")[3]  # Get the end date from the selected item
        
        url_list = urls.split(";")  # Splitting URLs by the delimiter
        
        # Clear the text widget and add each URL on a new line
        self.info_text.delete(1.0, tk.END)
        for url in url_list:
            self.info_text.insert(tk.END, url + "\n")
        
        self.info_text.insert(tk.END, "\n")
        self.info_text.insert(tk.END, "Live: " + live_status + "\n")
        self.info_text.insert(tk.END, "End Date: " + end_date)  # Display the end date
        
    def open_add_entry_popup(self):
        self.popup = tk.Toplevel(self.root)
        self.popup.title("Add New Entry")

        ttk.Label(self.popup, text="Title:").grid(row=0, column=0, padx=10, pady=5, sticky='w')
        self.title_var = tk.StringVar()
        ttk.Entry(self.popup, textvariable=self.title_var).grid(row=0, column=1, padx=10, pady=5, sticky='e')
        
        ttk.Label(self.popup, text="Activity Type (activity or A/B):").grid(row=1, column=0, padx=10, pady=5, sticky='w')        
        self.activity_var = tk.StringVar()
        self.activity_combobox = ttk.Combobox(self.popup, textvariable=self.activity_var, values=["activity", "A/B"])
        self.activity_combobox.grid(row=1, column=1, padx=10, pady=5, sticky='e')
        self.activity_combobox.set("activity")  # Set a default value. Change to "A/B" if needed

        ttk.Label(self.popup, text="GeoTarget (True/False):").grid(row=2, column=0, padx=10, pady=5, sticky='w')
        self.geo_target_var = tk.StringVar()
        self.geo_target_combobox = ttk.Combobox(self.popup, textvariable=self.geo_target_var, values=["True", "False"])
        self.geo_target_combobox.grid(row=2, column=1, padx=10, pady=5, sticky='e')
        self.geo_target_combobox.set("False")  # Set a default value, you can change it to "True" if needed

        ttk.Label(self.popup, text="URLs (each on a new line):").grid(row=3, column=0, padx=10, pady=5, sticky='w')
        self.url_text = tk.Text(self.popup, height=5, width=30)  # Text widget to allow multiple lines
        self.url_text.grid(row=3, column=1, padx=10, pady=5, sticky='e')
        
        ttk.Label(self.popup, text="Live (True/False):").grid(row=4, column=0, padx=10, pady=5, sticky='w')
        self.live_var = tk.StringVar()
        self.live_combobox = ttk.Combobox(self.popup, textvariable=self.live_var, values=["True", "False"])
        self.live_combobox.grid(row=4, column=1, padx=10, pady=5, sticky='e')
        self.live_combobox.set("True")  # Set a default value. Change to "False" if needed
        
        ttk.Label(self.popup, text="Has End Date:").grid(row=5, column=0, padx=10, pady=5, sticky='w')        
        self.has_end_date = tk.BooleanVar()  # Variable to store the checkbox state
        self.check_end_date = ttk.Checkbutton(self.popup, variable=self.has_end_date, command=self.toggle_end_date)
        self.check_end_date.grid(row=5, column=1, padx=10, pady=5, sticky='e')
        
        ttk.Label(self.popup, text="End Date:").grid(row=6, column=0, padx=10, pady=5, sticky='w')
        self.end_date_var = tk.StringVar()
        self.end_date_entry = DateEntry(self.popup, textvariable=self.end_date_var, date_pattern='y-mm-dd')
        self.end_date_entry.grid(row=6, column=1, padx=10, pady=5, sticky='e')
        self.end_date_entry.config(state='disabled')  # Disable the entry by default


        ttk.Button(self.popup, text="Submit", command=self.add_new_entry).grid(row=7, column=0, columnspan=2, pady=10)
        
    def add_new_entry(self):
        title = self.title_var.get()
        
        # Fetching multiple URLs from the Text widget
        urls = self.url_text.get("1.0", tk.END).strip().replace("\n", ";")

        live_status = self.live_var.get()
        activity_type = self.activity_var.get()
        geo_target = self.geo_target_var.get()
        
        end_date = 'NAN' if not self.has_end_date.get() else self.end_date_var.get()

        # Adding to the DataFrame
        new_row = {'title': title, 'activity': activity_type, 'geo_target': geo_target, 'url': urls, 'live': live_status, 'end date': end_date}
        self.df.loc[len(self.df)] = new_row

        # Adding to the Treeview
        item = self.tree.insert('', tk.END, values=(title, activity_type, geo_target, urls, live_status, end_date))
        if str(live_status).lower() == "true":
            self.tree.item(item, tags='live')
        else:
            self.tree.item(item, tags='not_live')

        print(f"Title: {title}")
        print(f"URLs: {urls}")
        print(f"Live Status: {live_status}")
        print(f"End Date: {end_date}")

        print(self.df.tail())
        start_upload = messagebox.askyesno("Upload to Server", "Do you want to upload the new entry to the server?")
        if start_upload:
            self.start_upload()

        # Closing the popup
        self.popup.destroy()

        
    def upload_to_server(self):
        url = "http://target.mts-studios.com/upload"
        headers = {
            "Authorization": "Bearer 76cdc8491313c226dd2ffac76e1b544d"
        }
        
        csv_data = self.df.to_csv(index=False)
        files = {'file': ('target.csv', csv_data)}
        
        response = requests.post(url, headers=headers, files=files)
        
        if response.status_code == 200:
            messagebox.showinfo("Success", "File uploaded successfully!")
        else:
            messagebox.showerror("Error", "File upload failed!")
            
    def start_upload(self):
        thread = threading.Thread(target=self.upload_to_server)
        thread.daemon = True
        thread.start()
        
    def refresh_data(self):
        self.tree.delete(*self.tree.get_children())
        self.load_data()
        self.populate_tree()
        
    def toggle_end_date(self):
        if self.has_end_date.get():
            self.end_date_entry.config(state='normal')
        else:
            self.end_date_entry.config(state='disabled')
            self.end_date_var.set('')


if __name__ == "__main__":
    root = tk.Tk()
    root.title("CSV Title Viewer")
    
    # Apply sv_ttk dark theme
    sv_ttk.set_theme("dark")
    
    app = CSVApp(root)
    root.mainloop()