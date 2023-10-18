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
import urlFileChecker
import babel.numbers

import webbrowser
from PIL import Image, ImageTk
SERVER_URL = "http://webp.mts-studios.com:5000/current_version_target"
currentVersion = "1.0.0"
headers = {
    'User-Agent': 'targetLookUp/1.0'
}

class CSVApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Target Activity Look Up")
        self.title_var = tk.StringVar()
        self.activity_var = tk.StringVar()
        self.geo_target_var = tk.StringVar()
        self.url_text = tk.Text()
        self.live_var = tk.StringVar()
        self.end_date_var = tk.StringVar()
        self.has_end_date = tk.BooleanVar()
        self.business_unit_var = tk.StringVar()
        self.environment_var = tk.StringVar()
        self.activity_combobox = None

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
        
        self.button_frame = ttk.Frame(main_frame)  # Change `main_frame` to the correct parent if needed
        self.button_frame.pack(pady=10, side=tk.TOP, fill=tk.X)  # Adjust packing options based on your layout

        # Create a frame for search label and entry within the main frame
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(pady=10, fill=tk.X)
        iconPath = resource_path('targetIcon.ico')
        self.root.iconbitmap(iconPath)

        # Create Search Label and Entry within the frame
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=5)  # Packed to the left
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)  # Packed to the left, next to the label
        self.search_entry.bind("<KeyRelease>", self.filter_titles)
        
        # Filter comboboxes
        ttk.Label(search_frame, text="Activity Type:").pack(side=tk.LEFT, padx=5)
        self.activity_combobox_filter = ttk.Combobox(search_frame, values=["","activity", "A/B"], postcommand=self.filter_treeview)
        self.activity_combobox_filter.pack(side=tk.LEFT, fill=tk.X, padx=5)

        ttk.Label(search_frame, text="Live:").pack(side=tk.LEFT, padx=5)
        self.live_combobox_filter = ttk.Combobox(search_frame, values=["","True", "False"], postcommand=self.filter_treeview)
        self.live_combobox_filter.pack(side=tk.LEFT, fill=tk.X, padx=5)

        ttk.Label(search_frame, text="Business Unit:").pack(side=tk.LEFT, padx=5)
        self.business_unit_combobox_filter = ttk.Combobox(search_frame, values=["","Corp", "School", "HigherEd", "Sharpen", "Professional"], postcommand=self.filter_treeview)
        self.business_unit_combobox_filter.pack(side=tk.LEFT, fill=tk.X, padx=5)
        
        self.activity_combobox_filter.bind("<<ComboboxSelected>>", lambda e: self.filter_treeview())
        self.live_combobox_filter.bind("<<ComboboxSelected>>", lambda e: self.filter_treeview())
        self.business_unit_combobox_filter.bind("<<ComboboxSelected>>", lambda e: self.filter_treeview())


        
        # Create Treeview
        self.tree = ttk.Treeview(main_frame, columns=('Title', 'Activity Type', 'GeoTarget', 'Business Unit', 'URLs', 'Live', 'End Date', 'Environment'), show='headings')
        self.tree.heading('Title', text='Title')
        self.tree.heading('Business Unit', text='Business Unit')
        self.tree.column('Business Unit', width=100)  # Adjust width as needed
        self.tree.heading('Activity Type', text='Activity Type')
        self.tree.column('Activity Type', width=100)  # Adjust the width as needed
        self.tree.heading('GeoTarget', text='GeoTarget')
        self.tree.column('GeoTarget', width=80)  # Adjust the width as needed
        self.tree.heading('URLs', text='URLs')  # Hidden from view
        self.tree.heading('Live', text='Live')  # Hidden from view
        self.tree.heading('End Date', text='End Date')  # Hidden from view
        self.tree.heading("Environment", text="Environment")
        self.tree.column("Environment", width=150)
        self.tree.column("Environment", width=150)
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
        self.add_button.pack(pady=10, padx=5, side=tk.LEFT)
        self.edit_button = ttk.Button(main_frame, text="Edit Entry", command=self.open_edit_entry_popup, state=tk.DISABLED)  # Start disabled
        self.edit_button.pack(pady=10, padx=5, side=tk.LEFT)
        self.refresh_button = ttk.Button(main_frame, text="Refresh Data", command=self.refresh_data)
        self.refresh_button.pack(pady=10, padx=5, side=tk.RIGHT)
        self.clear_filter_btn = ttk.Button(main_frame, text="Clear Filter", command=self.clear_filter)
        self.clear_filter_btn.pack(pady=10, padx=5, side=tk.RIGHT)  # You can adjust the placement using pack, grid or place as per your layout.

        self.setup_menu()
        # Fetch and Load CSV data
        self.load_data()
        
    def check_for_updates_at_start(self):
        # Check for updates
        isAvailable = is_update_available(currentVersion)
        boolAvailable = isAvailable[0]
        if boolAvailable:
            return True
        else:
            return False
        
    def update_menu_button_text(self):
        # Set button text based on whether an update is available
        btn_text = "≡"
        if self.update_available:
            btn_text = "! " + btn_text
        
        # Update the text of the already initialized menu_button
        self.menu_button.config(text=btn_text)

    def update_dropdown_menu(self):
        # Set menu text based on whether an update is available
        menu_text = "Check for Updates"
        if self.update_available:
            menu_text = "! " + menu_text
        
        self.dropdown_menu.add_command(label=menu_text, command=self.check_and_update)
        self.dropdown_menu.add_command(label="About", command=self.show_about)


    def setup_menu(self):
        # Hamburger menu button
        self.menu_button = ttk.Button(self.button_frame, text="≡", command=self.show_menu) # You can adjust the position
        self.menu_button.pack(side=tk.RIGHT, padx=5, pady=5)
        self.menu_button.config(width=1, cursor="hand2")
        
        # Dropdown menu for the hamburger menu button
        self.dropdown_menu = tk.Menu(self.root, tearoff=0)
        self.dropdown_menu.add_command(label="Check for Updates", command=self.check_and_update)
        self.dropdown_menu.add_command(label="About", command=self.show_about)
        
    def show_menu(self):
        # Display the dropdown menu below the menu button
        self.dropdown_menu.post(self.menu_button.winfo_rootx(), self.menu_button.winfo_rooty() + self.menu_button.winfo_height())

    def load_data(self):
        # Reset the DataFrame
        self.df = pd.DataFrame()

        url = urlFileChecker.url
        headers = urlFileChecker.headers
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
        self.tree.delete(*self.tree.get_children()) 
        for _, row in self.df.iterrows():
            title = row['title']
            urls = row['url']
            live_status = row['live']
            end_date = row['end date']
            activity_type = row['activity']
            geo_target = row['geo_target']
            business_unit = row['business_unit']
            environment = row['environment']
            
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
            business_unit = row.get('business_unit', '')
            item = self.tree.insert('', tk.END, values=(title, activity_type, geo_target, business_unit, urls, live_status, end_date, environment))
            
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

        # Filter data where title, activity type, URL, or end date contains the search term
        filtered_data = self.df[
            (self.df['title'].str.lower().str.contains(search_term)) |
            (self.df['activity'].str.lower().str.contains(search_term)) |
            (self.df['geo_target'].astype(str).str.lower().str.contains(search_term)) |
            (self.df['url'].astype(str).str.lower().str.contains(search_term))
        ]

        # Apply the combobox filters on top of the title filter
        activity_type = self.activity_combobox_filter.get()
        live_status = self.live_combobox_filter.get()
        business_unit = self.business_unit_combobox_filter.get()
        filtered_data = self.df[
            (self.df['title'].str.lower().str.contains(search_term)) |
            (self.df['activity'].str.lower().str.contains(search_term)) |
            (self.df['geo_target'].astype(str).str.lower().str.contains(search_term)) |
            (self.df['url'].astype(str).str.lower().str.contains(search_term))
        ]

        for _, row in filtered_data.iterrows():
            title = row['title']
            urls = row['url']
            live_status = row['live']
            end_date = row['end date']
            activity_type = row['activity']
            geo_target = row['geo_target']
            business_unit = row['business_unit']

            item = self.tree.insert('', tk.END, values=(title, activity_type, geo_target, business_unit, urls, live_status, end_date))
            
            if str(live_status).lower() == "true":
                self.tree.item(item, tags='live')
            else:
                self.tree.item(item, tags='not_live')

                
    def filter_treeview(self):
        # Get values from the comboboxes
        activity_type = self.activity_combobox_filter.get()
        live_status = self.live_combobox_filter.get()
        business_unit = self.business_unit_combobox_filter.get()

        # Start with a mask that's all True (i.e., include all rows)
        mask = [True] * len(self.df)

        # Update the mask based on comboboxes' values
        if activity_type:
            mask = (mask) & (self.df['activity'] == activity_type)
        if live_status:
            # Convert the tag to a Boolean value
            if live_status == "True":
                live_boolean = True
            elif live_status == "False":
                live_boolean = False

            if live_boolean is not None:
                mask = (mask) & (self.df['live'] == live_boolean)
        if business_unit:
            mask = (mask) & (self.df['business_unit'] == business_unit)

        filtered_data = self.df[mask]

        # Clear the treeview and populate it with filtered data
        self.tree.delete(*self.tree.get_children())
        for _, row in filtered_data.iterrows():
            title = row['title']
            urls = row['url']
            live_status_row = row['live']
            end_date = row['end date']
            activity_type = row['activity']
            geo_target = row['geo_target']
            business_unit = row['business_unit']

            item = self.tree.insert('', tk.END, values=(title, activity_type, geo_target, business_unit, urls, live_status_row, end_date))
            
            if str(live_status_row).lower() == "true":
                self.tree.item(item, tags='live')
            else:
                self.tree.item(item, tags='not_live')
                
    def clear_filter(self):
        # Reset combobox selections
        self.activity_combobox_filter.set('')
        self.live_combobox_filter.set('')
        self.business_unit_combobox_filter.set('')

        # Call filter_treeview to reset the treeview data
        self.filter_treeview()



    def on_item_click(self, event):
        selected_item = self.tree.selection()[0]
        urls = self.tree.item(selected_item, "values")[4]
        live_status = self.tree.item(selected_item, "values")[5]
        end_date = self.tree.item(selected_item, "values")[6]  # Get the end date from the selected item
        
        url_list = urls.split(";")  # Splitting URLs by the delimiter
        
        # Clear the text widget and add each URL on a new line
        self.info_text.delete(1.0, tk.END)
        for url in url_list:
            self.info_text.insert(tk.END, url + "\n")
        
        self.info_text.insert(tk.END, "\n")
        self.info_text.insert(tk.END, "Live: " + live_status + "\n")
        self.info_text.insert(tk.END, "End Date: " + end_date)  # Display the end date
        self.edit_button.config(state=tk.NORMAL)
        
    def open_add_entry_popup(self):
        self.popup = tk.Toplevel(self.root)
        self.popup.title("Add New Entry")

        ttk.Label(self.popup, text="Title:").grid(row=0, column=0, padx=10, pady=5, sticky='w')
        ttk.Entry(self.popup, textvariable=self.title_var).grid(row=0, column=1, padx=10, pady=5, sticky='e')
        
        ttk.Label(self.popup, text="Business Unit:").grid(row=7, column=0, padx=10, pady=5, sticky='w')
        self.business_unit_combobox = ttk.Combobox(self.popup, textvariable=self.business_unit_var, values=["Corp", "School", "HigherEd", "Sharpen", "Professional"])
        self.business_unit_combobox.grid(row=7, column=1, padx=10, pady=5, sticky='e')
        self.business_unit_combobox.set("Corp")  # Set a default value


        ttk.Label(self.popup, text="Environment:").grid(row=8, column=0, padx=10, pady=5, sticky='w')
        self.environment_combobox = ttk.Combobox(self.popup, textvariable=self.environment_var, values=["QALV", "PROD"])
        self.environment_combobox.grid(row=8, column=1, padx=10, pady=5, sticky='e')
        self.environment_combobox.set("QALV")  # Set a default value

        
        ttk.Label(self.popup, text="Activity Type (activity or A/B):").grid(row=1, column=0, padx=10, pady=5, sticky='w')        
        self.activity_combobox = ttk.Combobox(self.popup, textvariable=self.activity_var, values=["activity", "A/B"])
        self.activity_combobox.grid(row=1, column=1, padx=10, pady=5, sticky='e')
        self.activity_combobox.set("activity")  # Set a default value. Change to "A/B" if needed

        ttk.Label(self.popup, text="GeoTarget (True/False):").grid(row=2, column=0, padx=10, pady=5, sticky='w')
        self.geo_target_combobox = ttk.Combobox(self.popup, textvariable=self.geo_target_var, values=["True", "False"])
        self.geo_target_combobox.grid(row=2, column=1, padx=10, pady=5, sticky='e')
        self.geo_target_combobox.set("False")  # Set a default value, you can change it to "True" if needed

        ttk.Label(self.popup, text="URLs (each on a new line):").grid(row=3, column=0, padx=10, pady=5, sticky='w')
        self.url_text = tk.Text(self.popup, height=5, width=30)  # Text widget to allow multiple lines
        self.url_text.grid(row=3, column=1, padx=10, pady=5, sticky='e')
        
        ttk.Label(self.popup, text="Live (True/False):").grid(row=4, column=0, padx=10, pady=5, sticky='w')
        self.live_combobox = ttk.Combobox(self.popup, textvariable=self.live_var, values=["True", "False"])
        self.live_combobox.grid(row=4, column=1, padx=10, pady=5, sticky='e')
        self.live_combobox.set("True")  # Set a default value. Change to "False" if needed
        
        ttk.Label(self.popup, text="Has End Date:").grid(row=5, column=0, padx=10, pady=5, sticky='w')        # Variable to store the checkbox state
        self.check_end_date = ttk.Checkbutton(self.popup, variable=self.has_end_date, command=self.toggle_end_date)
        self.check_end_date.grid(row=5, column=1, padx=10, pady=5, sticky='e')
        
        ttk.Label(self.popup, text="End Date:").grid(row=6, column=0, padx=10, pady=5, sticky='w')
        self.end_date_entry = DateEntry(self.popup, textvariable=self.end_date_var, date_pattern='y-mm-dd')
        self.end_date_entry.grid(row=6, column=1, padx=10, pady=5, sticky='e')
        self.end_date_entry.config(state='disabled')  # Disable the entry by default


        ttk.Button(self.popup, text="Submit", command=self.add_new_entry).grid(row=9, column=0, columnspan=2, pady=10)
        
    def open_edit_entry_popup(self):
        selected_item = self.tree.selection()[0]
        if not selected_item:
            return

        data = self.tree.item(selected_item, "values")
        
        self.popup = tk.Toplevel(self.root)
        self.popup.title("Edit Entry")

        ttk.Label(self.popup, text="Title:").grid(row=0, column=0, padx=10, pady=5, sticky='w')
        ttk.Entry(self.popup, textvariable=self.title_var).grid(row=0, column=1, padx=10, pady=5, sticky='e')
        
        ttk.Label(self.popup, text="Activity Type (activity or A/B):").grid(row=1, column=0, padx=10, pady=5, sticky='w')        
        self.activity_combobox = ttk.Combobox(self.popup, textvariable=self.activity_var, values=["activity", "A/B"])
        self.activity_combobox.grid(row=1, column=1, padx=10, pady=5, sticky='e')
        self.activity_combobox.set("activity")  # Set a default value. Change to "A/B" if needed

        ttk.Label(self.popup, text="GeoTarget (True/False):").grid(row=2, column=0, padx=10, pady=5, sticky='w')
        self.geo_target_combobox = ttk.Combobox(self.popup, textvariable=self.geo_target_var, values=["True", "False"])
        self.geo_target_combobox.grid(row=2, column=1, padx=10, pady=5, sticky='e')
        self.geo_target_combobox.set("False")  # Set a default value, you can change it to "True" if needed

        ttk.Label(self.popup, text="URLs (each on a new line):").grid(row=3, column=0, padx=10, pady=5, sticky='w')
        self.url_text = tk.Text(self.popup, height=5, width=30)  # Text widget to allow multiple lines
        self.url_text.grid(row=3, column=1, padx=10, pady=5, sticky='e')
        
        ttk.Label(self.popup, text="Live (True/False):").grid(row=4, column=0, padx=10, pady=5, sticky='w')
        self.live_combobox = ttk.Combobox(self.popup, textvariable=self.live_var, values=["True", "False"])
        self.live_combobox.grid(row=4, column=1, padx=10, pady=5, sticky='e')
        self.live_combobox.set("True")  # Set a default value. Change to "False" if needed
        
        ttk.Label(self.popup, text="Has End Date:").grid(row=5, column=0, padx=10, pady=5, sticky='w')        # Variable to store the checkbox state
        self.check_end_date = ttk.Checkbutton(self.popup, variable=self.has_end_date, command=self.toggle_end_date)
        self.check_end_date.grid(row=5, column=1, padx=10, pady=5, sticky='e')
        
        ttk.Label(self.popup, text="End Date:").grid(row=6, column=0, padx=10, pady=5, sticky='w')
        self.end_date_entry = DateEntry(self.popup, textvariable=self.end_date_var, date_pattern='y-mm-dd')
        self.end_date_entry.grid(row=6, column=1, padx=10, pady=5, sticky='e')
        self.end_date_entry.config(state='disabled')  # Disable the entry by default
        
        ttk.Label(self.popup, text="Business Unit:").grid(row=7, column=0, padx=10, pady=5, sticky='w')
        self.business_unit_combobox = ttk.Combobox(self.popup, textvariable=self.business_unit_var, values=["Corp", "School", "HigherEd", "Sharpen", "Professional"])
        self.business_unit_combobox.grid(row=7, column=1, padx=10, pady=5, sticky='e')
        
        ttk.Label(self.popup, text="Environment:").grid(row=9, column=0, padx=10, pady=5, sticky='w')
        self.environment_combobox = ttk.Combobox(self.popup, textvariable=self.environment_var, values=["QALV", "PROD"])
        self.environment_combobox.grid(row=9, column=1, padx=10, pady=5, sticky='e')
        # Assuming data[7] contains the environment info
        self.environment_var.set(data[7])

        self.title_var.set(data[0])
        self.activity_var.set(data[1])
        self.geo_target_var.set(data[2])
        self.url_text.insert(tk.END, data[4].replace(';', '\n'))
        self.live_var.set(data[5])
        self.end_date_var.set(data[6])
        self.business_unit_var.set(data[3])

        ttk.Button(self.popup, text="Update", command=lambda: self.update_entry(selected_item)).grid(row=8, column=0, columnspan=2, pady=10)
        
    def update_entry(self, item):
        title = self.title_var.get()
        activity_type = self.activity_var.get()
        geo_target = self.geo_target_var.get()
        business_unit = self.business_unit_var.get()
        urls = self.url_text.get("1.0", tk.END).strip().replace("\n", ";")
        live_status = self.live_var.get()
        environment = self.environment_var.get()
        end_date = 'NAN' if not self.has_end_date.get() else self.end_date_var.get()

        # Update the Treeview
        self.tree.item(item, values=(title, activity_type, geo_target, business_unit, urls, live_status, end_date))

        # Update the DataFrame
        index = self.tree.index(item)
        self.df.iloc[index] = [title, activity_type, geo_target, urls, live_status, end_date, business_unit]


        
        start_upload = messagebox.askyesno("Upload to Server", "Do you want to upload the new entry to the server?")
        if start_upload:
            self.start_upload()

        self.popup.destroy()


        
    def add_new_entry(self):
        title = self.title_var.get()
        
        # Fetching multiple URLs from the Text widget
        urls = self.url_text.get("1.0", tk.END).strip().replace("\n", ";")

        live_status = self.live_var.get()
        activity_type = self.activity_var.get()
        geo_target = self.geo_target_var.get()
        business_unit = self.business_unit_var.get()
        environment = self.environment_var.get()
        
        end_date = 'NAN' if not self.has_end_date.get() else self.end_date_var.get()

        # Adding to the DataFrame
        new_row = {'title': title, 'activity': activity_type, 'geo_target': geo_target, 'url': urls, 'live': live_status, 'end date': end_date, 'business_unit': business_unit, 'environment': environment}
        self.df.loc[len(self.df)] = new_row

        # Adding to the Treeview
        item = self.tree.insert('', tk.END, values=(title, activity_type, geo_target, business_unit, urls, live_status, end_date, environment))
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
        
        url = urlFileChecker.urlUpload
        headers = urlFileChecker.headers
        
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
            
    def check_and_update(self):
        update_available, download_url = is_update_available(currentVersion)
        if update_available:
            answer = messagebox.askyesno("Update Available", "An update is available. Do you want to download and install it?")
            if answer:
                download_success = download_update(download_url)  # Pass the download URL
                if download_success:
                    apply_update()
                    messagebox.showinfo("Update Successful", "The application was updated successfully. Please restart the application to use the new version.")
                    self.quit()
        else:
            messagebox.showinfo("No Update", "You are using the latest version.")
            
    def show_about(self):
        about_win = tk.Toplevel(self.root)
        about_win.title("About")
        def resource_path(relative_path):
            try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
                base_path = sys._MEIPASS
            except Exception:
                base_path = os.path.abspath(".")
                
            return os.path.join(base_path, relative_path)

        # Set the icon for the About window
        iconPath = resource_path('targetIcon.ico')
        about_win.iconbitmap(iconPath)

        # Load and display the image
        image_path = resource_path('targetIcon.png')
        logo_image = Image.open(image_path)
        # Resize the image
        desired_size = (500, 281)  # Set width and height as needed
        logo_image = logo_image.resize(desired_size, Image.Resampling.LANCZOS)
        logo_photo = ImageTk.PhotoImage(logo_image)
        logo_label = ttk.Label(about_win, image=logo_photo)
        logo_label.image = logo_photo  # Keep a reference to avoid garbage collection
        logo_label.pack(pady=10)

        # Create and pack widgets for the version, copyright, and link to GitHub
        ttk.Label(about_win, text="Version: " + currentVersion).pack(pady=5)
        copyright = ttk.Label(about_win, text="©2023 Matthew Thomas Stevens Studios LLC", cursor="hand2", foreground="white", font="TkDefaultFont 10 underline")
        copyright.pack(pady=5)
        copyright.bind("<Button-1>", lambda e: webbrowser.open("https://www.matthewstevens.me"))
        
        about_win.geometry('500x400')  # Adjusted the size for the image
        about_win.mainloop()
        
    def periodic_check_for_updates(self):
        # Check for updates
        self.update_available = self.check_for_updates_at_start()
        
        # Modify the hamburger menu button accordingly
        self.update_menu_button_text()
        
        # Schedule the next check for 24 hours from now
        self.after(15*60*60*1000, self.periodic_check_for_updates)
        
        
def download_update(download_url):
    try:
        # Download the .exe file
        response = requests.get(download_url, stream=True)
        with open('latest_app.exe', 'wb') as file:
            for chunk in response.iter_content(chunk_size=1024):
                file.write(chunk)
        return True
    except Exception as e:
        print(f"Error downloading update: {e}")
        return False

    
def apply_update():
    try:
        # Rename the downloaded exe to a temporary name
        os.rename('latest_app.exe', 'update_temp.exe')
        
        # Create the helper script
        with open('update_helper.bat', 'w') as bat_file:
            bat_content = """
@echo off
timeout /t 5 /nobreak
move /y update_temp.exe targetLookUp.exe
start targetLookUp.exe
del update_helper.bat
"""
            bat_file.write(bat_content)
        
        # Start the helper script to handle the replacement without showing the command prompt
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        subprocess.Popen(['update_helper.bat'], startupinfo=startupinfo)
        
        # Close the current application
        sys.exit(0)
        
    except Exception as e:
        print(f"Error applying update: {e}")
        return False

            
def is_update_available(current_version):
    try:
        # Generate headers with the token
        headers = {
            'User-Agent': 'targetLookUp/1.0'
        }
        
        response = requests.get(SERVER_URL, headers=headers)
        data = response.json()
        
        latest_version = data.get('version', "")
        download_url = data.get('download_url', "")
        
        return latest_version > current_version, download_url
    except Exception as e:
        print(f"Error checking for update: {e}")
        return False, ""


if __name__ == "__main__":
    root = tk.Tk()
    root.title("CSV Title Viewer")
    
    # Apply sv_ttk dark theme
    sv_ttk.set_theme("dark")
    
    app = CSVApp(root)
    root.mainloop()