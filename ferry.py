

import customtkinter as ctk
import os
import qrcode
import datetime
from PIL import Image, ImageDraw, ImageFont, ImageTk
from tkinter import messagebox, Toplevel
import json

# Set appearance
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")

# Constants
QR_FOLDER = "qr_codes"
os.makedirs(QR_FOLDER, exist_ok=True)

class Traveler:
    def __init__(self, traveler_id, name, status, is_local, destination, fare, qr_filename, is_paid=False, is_pwd=False):
        self.traveler_id = traveler_id
        self.name = name
        self.status = status
        self.is_local = is_local
        self.destination = destination
        self.fare = fare
        self.qr_filename = qr_filename
        self.is_paid = is_paid
        self.is_pwd = is_pwd

class FerrySystem:
    def __init__(self):
        self.travelers = []
        self.is_summer = False
        self.next_id = 101
        self.departure_time = None

    def generate_unique_id(self):
        traveler_id = self.next_id
        self.next_id += 1
        return traveler_id

    def calculate_fare_by_status(self, status):
        status = status.lower()
        if status == "senior":
            fare = 104.00
        elif status == "student":
            fare = 116.00
        elif status == "child":
            fare = 72.00
        elif status == "infant":
            fare = 0.00
        else:
            fare = 160.00

        if self.is_summer:
            fare *= 0.90

        return fare

    def register_traveler(self, name, status, is_local, destination, is_pwd=False, departure_time=None):
        traveler_id = self.generate_unique_id()
        base_fare = self.calculate_fare_by_status(status)
        env_fee = 0.00 if is_local else 50.00
        
        if is_pwd:
            base_fare = base_fare * 0.80
        
        total_fare = base_fare + env_fee
        qr_filename = os.path.join(QR_FOLDER, f"traveler_{traveler_id}_ticket.png")
        
        traveler = Traveler(traveler_id, name, status, is_local, destination, total_fare, qr_filename, is_pwd=is_pwd)
        self.travelers.append(traveler)
        
        self.generate_qr_code(traveler, base_fare, env_fee, total_fare, departure_time)
        
        return traveler.traveler_id, traveler.qr_filename

    def generate_qr_code(self, t, base, env, total, departure_time=None):
        paid_status = "✓ PAID" if t.is_paid else "Not Paid"
        pwd_status = "PWD: Yes (20% Discount Applied)" if t.is_pwd else "PWD: No"
        
        if departure_time:
            try:
                hour, minute = map(int, departure_time.split(':'))
                ampm = 'PM' if hour >= 12 else 'AM'
                hour12 = hour % 12 or 12
                departure_display = f"{hour12}:{minute:02d} {ampm}"
            except:
                departure_display = "Not Set"
        else:
            departure_display = "Not Set"
        
        qr_data = (
            f"=== Montenegro Ferry Ticket ===\n"
            f"Traveler ID: {t.traveler_id}\n"
            f"Name: {t.name}\n"
            f"Status: {t.status.title()}\n"
            f"Local: {'Yes' if t.is_local else 'No'}\n"
            f"{pwd_status}\n"
            f"Destination: {t.destination.title()}\n"
            f"Departure Time: {departure_display}\n"
            f"Fare: ₱{int(base)}.00\n"
            f"Environmental Fee: ₱{int(env)}.00\n"
            f"Total Fare: ₱{int(total)}.00\n"
            f"Payment Status: {paid_status}\n"
            f"Issue Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")

        ticket_width = 1080
        ticket_height = 1920
        ticket = Image.new('RGB', (ticket_width, ticket_height), 'white')
        draw = ImageDraw.Draw(ticket)

        qr_size = 800
        qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)

        qr_x = (ticket_width - qr_size) // 2
        qr_y = 400
        ticket.paste(qr_img, (qr_x, qr_y))

        try:
            font = ImageFont.truetype("arial.ttf", 80)
        except:
            font = ImageFont.load_default()

        text = f"Traveler ID: {t.traveler_id}"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_x = (ticket_width - text_width) // 2
        text_y = qr_y + qr_size + 80

        draw.text((text_x, text_y), text, fill='black', font=font)
        ticket.save(t.qr_filename)

    def get_all_travelers(self):
        data = []
        for t in self.travelers:
            data.append({
                "traveler_id": t.traveler_id,
                "name": t.name,
                "status": t.status,
                "is_local": t.is_local,
                "destination": t.destination,
                "fare": t.fare,
                "qr_filename": t.qr_filename,
                "is_paid": t.is_paid,
                "is_pwd": t.is_pwd
            })
        return data

    def mark_as_paid(self, traveler_id, departure_time=None):
        for t in self.travelers:
            if t.traveler_id == traveler_id:
                t.is_paid = True
                base_fare = self.calculate_fare_by_status(t.status)
                if t.is_pwd:
                    base_fare = base_fare * 0.80
                env_fee = 0.00 if t.is_local else 50.00
                total_fare = t.fare
                self.generate_qr_code(t, base_fare, env_fee, total_fare, departure_time)
                return True
        return False

class FerryApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Montenegro Ferry E-Ticket System")
        self.geometry("1200x800")
        
        self.system = FerrySystem()
        self.departure_time = None
        
        # Colors
        self.green = "#00A83D"
        self.yellow = "#FFD700"
        
        self.show_main_menu()
    
    def clear_window(self):
        for widget in self.winfo_children():
            widget.destroy()
    
    def show_main_menu(self):
        self.clear_window()
        
        # Main frame
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(expand=True, fill="both", padx=50, pady=50)
        
        # Title
        title = ctk.CTkLabel(main_frame, text="Montenegro Ferry E-Ticket", 
                            font=("Arial", 36, "bold"), text_color=self.green)
        title.pack(pady=50)
        
        # Buttons
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(pady=30)
        
        traveler_btn = ctk.CTkButton(btn_frame, text="Traveler", width=200, height=50,
                                     font=("Arial", 18, "bold"), fg_color=self.green,
                                     hover_color="#008030", command=self.show_traveler_form)
        traveler_btn.pack(side="left", padx=20)
        
        admin_btn = ctk.CTkButton(btn_frame, text="Admin", width=200, height=50,
                                  font=("Arial", 18, "bold"), fg_color=self.green,
                                  hover_color="#008030", command=self.show_admin_login)
        admin_btn.pack(side="left", padx=20)
    
    def show_traveler_form(self):
        self.clear_window()
        
        # Scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(self, width=700, height=700)
        scroll_frame.pack(expand=True, padx=50, pady=20)
        
        # Title
        title = ctk.CTkLabel(scroll_frame, text="Traveler Registration", 
                            font=("Arial", 28, "bold"), text_color=self.green)
        title.pack(pady=20)
        
        # Show departure time if set
        if self.departure_time:
            dep_label = ctk.CTkLabel(scroll_frame, text=f"Departure Time: {self.format_time_12hr(self.departure_time)}", 
                                    font=("Arial", 14, "bold"), text_color=self.yellow)
            dep_label.pack(pady=5)
        
        # Name
        name_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        name_frame.pack(padx=20, pady=10, fill="x")
        ctk.CTkLabel(name_frame, text="Name:", font=("Arial", 16, "bold"), width=200).pack(side="left", padx=(0,10))
        name_entry = ctk.CTkEntry(name_frame, width=400, height=40, font=("Arial", 14))
        name_entry.pack(side="left")
        
        # Status
        status_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        status_frame.pack(padx=20, pady=10, fill="x")
        ctk.CTkLabel(status_frame, text="Status:", font=("Arial", 16, "bold"), width=200).pack(side="left", padx=(0,10))
        status_var = ctk.StringVar(value="Select Status")
        status_menu = ctk.CTkOptionMenu(status_frame, values=["Infant", "Child", "Student", "Regular", "Senior"],
                                       variable=status_var, width=400, height=40, font=("Arial", 14),
                                       fg_color=self.green, button_color=self.green)
        status_menu.pack(side="left")
        
        # Local
        local_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        local_frame.pack(padx=20, pady=10, fill="x")
        ctk.CTkLabel(local_frame, text="Local:", font=("Arial", 16, "bold"), width=200).pack(side="left", padx=(0,10))
        local_var = ctk.StringVar(value="Select Option")
        local_menu = ctk.CTkOptionMenu(local_frame, values=["Yes", "No"],
                                      variable=local_var, width=400, height=40, font=("Arial", 14),
                                      fg_color=self.green, button_color=self.green)
        local_menu.pack(side="left")
        
        # Destination
        dest_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        dest_frame.pack(padx=20, pady=10, fill="x")
        ctk.CTkLabel(dest_frame, text="Destination:", font=("Arial", 16, "bold"), width=200).pack(side="left", padx=(0,10))
        dest_var = ctk.StringVar(value="Select Destination")
        dest_menu = ctk.CTkOptionMenu(dest_frame, values=["Tingloy", "Mabini"],
                                     variable=dest_var, width=400, height=40, font=("Arial", 14),
                                     fg_color=self.green, button_color=self.green)
        dest_menu.pack(side="left")
        
        # PWD
        pwd_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        pwd_frame.pack(padx=20, pady=10, fill="x")
        ctk.CTkLabel(pwd_frame, text="PWD (Person with Disability):", font=("Arial", 16, "bold"), width=200).pack(side="left", padx=(0,10))
        pwd_var = ctk.StringVar(value="No")
        pwd_radio_frame = ctk.CTkFrame(pwd_frame, fg_color="transparent")
        pwd_radio_frame.pack(side="left")
        
        ctk.CTkRadioButton(pwd_radio_frame, text="Yes", variable=pwd_var, value="Yes", 
                          font=("Arial", 14)).pack(side="left", padx=10)
        ctk.CTkRadioButton(pwd_radio_frame, text="No", variable=pwd_var, value="No", 
                          font=("Arial", 14)).pack(side="left", padx=10)
        
        # Submit button
        def submit_traveler():
            name = name_entry.get()
            status = status_var.get()
            is_local = local_var.get() == "Yes"
            destination = dest_var.get()
            is_pwd = pwd_var.get() == "Yes"
            
            if not name or status == "Select Status" or local_var.get() == "Select Option" or dest_var.get() == "Select Destination":
                messagebox.showerror("Error", "Please fill in all fields!")
                return
            
            traveler_id, qr_filename = self.system.register_traveler(name, status, is_local, destination, is_pwd, self.departure_time)
            self.show_qr_page(traveler_id, qr_filename)
        
        submit_btn = ctk.CTkButton(scroll_frame, text="Submit & Generate QR", width=400, height=50,
                                  font=("Arial", 16, "bold"), fg_color=self.green,
                                  hover_color="#008030", command=submit_traveler)
        submit_btn.pack(pady=30)
        
        # Back button
        back_btn = ctk.CTkButton(scroll_frame, text="Back to Main Menu", width=400, height=40,
                                font=("Arial", 14), fg_color="gray", hover_color="darkgray",
                                command=self.show_main_menu)
        back_btn.pack(pady=10)
    
    def show_qr_page(self, traveler_id, qr_filename):
        self.clear_window()
        
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(expand=True, padx=50, pady=50)
        
        title = ctk.CTkLabel(main_frame, text="QR Code Generated!", 
                            font=("Arial", 28, "bold"), text_color=self.green)
        title.pack(pady=20)
        
        id_label = ctk.CTkLabel(main_frame, text=f"Traveler ID: {traveler_id}", 
                               font=("Arial", 20))
        id_label.pack(pady=10)
        
        # Display QR code
        try:
            qr_image = Image.open(qr_filename)
            qr_image = qr_image.resize((300, 300), Image.Resampling.LANCZOS)
            qr_photo = ImageTk.PhotoImage(qr_image)
            
            qr_label = ctk.CTkLabel(main_frame, image=qr_photo, text="")
            qr_label.image = qr_photo
            qr_label.pack(pady=20)
        except:
            ctk.CTkLabel(main_frame, text="QR Code saved successfully!", 
                        font=("Arial", 16)).pack(pady=20)
        
        # Buttons
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        def view_full_qr():
            qr_window = Toplevel(self)
            qr_window.title(f"Traveler {traveler_id} QR Code")
            qr_window.geometry("600x800")
            
            full_qr = Image.open(qr_filename)
            full_qr = full_qr.resize((550, 750), Image.Resampling.LANCZOS)
            full_photo = ImageTk.PhotoImage(full_qr)
            
            label = ctk.CTkLabel(qr_window, image=full_photo, text="")
            label.image = full_photo
            label.pack(pady=20)
        
        view_btn = ctk.CTkButton(btn_frame, text="View Full QR", width=200, height=40,
                                font=("Arial", 14), fg_color=self.green,
                                command=view_full_qr)
        view_btn.pack(side="left", padx=10)
        
        back_btn = ctk.CTkButton(btn_frame, text="Back to Main Menu", width=200, height=40,
                                font=("Arial", 14), fg_color="gray",
                                command=self.show_main_menu)
        back_btn.pack(side="left", padx=10)
    
    def show_admin_login(self):
        self.clear_window()
        
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(expand=True, padx=50, pady=50)
        
        title = ctk.CTkLabel(main_frame, text="Admin Access", 
                            font=("Arial", 32, "bold"), text_color=self.green)
        title.pack(pady=50)
        
        ctk.CTkLabel(main_frame, text="Password:", font=("Arial", 16, "bold")).pack(pady=10)
        password_entry = ctk.CTkEntry(main_frame, width=400, height=45, font=("Arial", 14), show="*")
        password_entry.pack(pady=10)
        
        def check_password():
            if password_entry.get() == "admin1234":
                self.show_admin_dashboard()
            else:
                messagebox.showerror("Error", "❌ Incorrect password!")
        
        login_btn = ctk.CTkButton(main_frame, text="Login", width=400, height=50,
                                 font=("Arial", 16, "bold"), fg_color=self.green,
                                 hover_color="#008030", command=check_password)
        login_btn.pack(pady=20)
        
        back_btn = ctk.CTkButton(main_frame, text="Back to Main Menu", width=400, height=40,
                                font=("Arial", 14), fg_color="gray",
                                command=self.show_main_menu)
        back_btn.pack(pady=10)
        
        password_entry.bind('<Return>', lambda e: check_password())
    
    def show_admin_dashboard(self):
        self.clear_window()
        
        # Main container
        container = ctk.CTkFrame(self)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        header = ctk.CTkFrame(container, fg_color=self.green, height=60)
        header.pack(fill="x", padx=10, pady=10)
        
        title = ctk.CTkLabel(header, text="Admin Dashboard", 
                            font=("Arial", 24, "bold"), text_color="white")
        title.pack(side="left", padx=20, pady=10)
        
        total_label = ctk.CTkLabel(header, text=f"Total Passengers: {len(self.system.travelers)}", 
                                  font=("Arial", 16), text_color="white")
        total_label.pack(side="right", padx=20, pady=10)
        
        # Controls frame
        controls = ctk.CTkFrame(container)
        controls.pack(fill="x", padx=10, pady=10)
        
        # Departure time
        left_controls = ctk.CTkFrame(controls, fg_color="transparent")
        left_controls.pack(side="left", fill="x", expand=True)
        
        ctk.CTkLabel(left_controls, text="Fastcraft Departure Time:", 
                    font=("Arial", 14, "bold")).pack(side="left", padx=5)
        
        time_entry = ctk.CTkEntry(left_controls, width=120, height=35, 
                                 placeholder_text="HH:MM (24hr)")
        time_entry.pack(side="left", padx=5)
        
        dep_time_label = ctk.CTkLabel(left_controls, text="", font=("Arial", 14, "bold"), 
                                     text_color=self.green)
        dep_time_label.pack(side="left", padx=10)
        
        def set_time():
            time_val = time_entry.get()
            if time_val:
                try:
                    # Validate time format
                    h, m = map(int, time_val.split(':'))
                    if 0 <= h <= 23 and 0 <= m <= 59:
                        self.departure_time = time_val
                        dep_time_label.configure(text=f"Departure: {self.format_time_12hr(time_val)}")
                        messagebox.showinfo("Success", f"Departure time set to: {self.format_time_12hr(time_val)}")
                    else:
                        messagebox.showerror("Error", "Invalid time! Use HH:MM format (00-23:00-59)")
                except:
                    messagebox.showerror("Error", "Invalid format! Use HH:MM (24-hour format)")
        
        set_btn = ctk.CTkButton(left_controls, text="Set Time", width=100, height=35,
                               fg_color=self.green, command=set_time)
        set_btn.pack(side="left", padx=5)
        
        # Search
        right_controls = ctk.CTkFrame(controls, fg_color="transparent")
        right_controls.pack(side="right")
        
        ctk.CTkLabel(right_controls, text="Search by ID:", 
                    font=("Arial", 14, "bold")).pack(side="left", padx=5)
        
        search_entry = ctk.CTkEntry(right_controls, width=150, height=35, 
                                   placeholder_text="Enter Traveler ID")
        search_entry.pack(side="left", padx=5)
        
        def search_traveler():
            search_id = search_entry.get()
            if not search_id:
                messagebox.showwarning("Warning", "Please enter a Traveler ID")
                return
            
            found = False
            for item in tree.get_children():
                values = tree.item(item)['values']
                if str(values[0]) == search_id:
                    tree.selection_set(item)
                    tree.see(item)
                    tree.focus(item)
                    found = True
                    break
            
            if not found:
                messagebox.showinfo("Not Found", f"Traveler ID {search_id} not found")
        
        def clear_search():
            search_entry.delete(0, 'end')
            if tree.selection():
                tree.selection_remove(tree.selection())
        
        search_btn = ctk.CTkButton(right_controls, text="Search", width=100, height=35,
                                  fg_color=self.green, command=search_traveler)
        search_btn.pack(side="left", padx=5)
        
        clear_btn = ctk.CTkButton(right_controls, text="Clear", width=100, height=35,
                                 fg_color="gray", command=clear_search)
        clear_btn.pack(side="left", padx=5)
        
        # Table frame
        import tkinter as tk
        from tkinter import ttk
        
        table_frame = ctk.CTkFrame(container)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create Treeview
        columns = ("ID", "Name", "Status", "Local", "PWD", "Destination", "Fare", "Paid")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        
        # Column headings
        for col in columns:
            tree.heading(col, text=col)
            if col == "Name":
                tree.column(col, width=150)
            elif col == "Destination":
                tree.column(col, width=100)
            else:
                tree.column(col, width=80)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Populate data
        for traveler in self.system.get_all_travelers():
            tree.insert("", "end", values=(
                traveler['traveler_id'],
                traveler['name'],
                traveler['status'].title(),
                "Yes" if traveler['is_local'] else "No",
                "Yes" if traveler['is_pwd'] else "No",
                traveler['destination'].title(),
                f"₱{traveler['fare']:.2f}",
                "✓ Paid" if traveler['is_paid'] else "Not Paid"
            ))
        
        # Action buttons
        action_frame = ctk.CTkFrame(container)
        action_frame.pack(fill="x", padx=10, pady=10)
        
        def mark_paid():
            selection = tree.selection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a traveler")
                return
            
            item = tree.item(selection[0])
            traveler_id = item['values'][0]
            
            if self.system.mark_as_paid(traveler_id, self.departure_time):
                messagebox.showinfo("Success", f"Traveler {traveler_id} marked as paid!")
                self.show_admin_dashboard()  # Refresh
        
        def view_qr():
            selection = tree.selection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a traveler")
                return
            
            item = tree.item(selection[0])
            traveler_id = item['values'][0]
            
            for t in self.system.travelers:
                if t.traveler_id == traveler_id:
                    qr_window = Toplevel(self)
                    qr_window.title(f"Traveler {traveler_id} QR Code")
                    qr_window.geometry("600x800")
                    
                    try:
                        qr_img = Image.open(t.qr_filename)
                        qr_img = qr_img.resize((550, 750), Image.Resampling.LANCZOS)
                        qr_photo = ImageTk.PhotoImage(qr_img)
                        
                        label = ctk.CTkLabel(qr_window, image=qr_photo, text="")
                        label.image = qr_photo
                        label.pack(pady=20)
                    except Exception as e:
                        ctk.CTkLabel(qr_window, text=f"Error loading QR: {e}").pack()
                    break
        
        mark_btn = ctk.CTkButton(action_frame, text="Mark as Paid", width=150, height=40,
                                fg_color=self.green, command=mark_paid)
        mark_btn.pack(side="left", padx=10)
        
        view_btn = ctk.CTkButton(action_frame, text="View QR Code", width=150, height=40,
                                fg_color=self.yellow, text_color="black", command=view_qr)
        view_btn.pack(side="left", padx=10)
        
        refresh_btn = ctk.CTkButton(action_frame, text="Refresh", width=150, height=40,
                                   fg_color="gray", command=self.show_admin_dashboard)
        refresh_btn.pack(side="left", padx=10)
        
        back_btn = ctk.CTkButton(action_frame, text="Back to Main Menu", width=150, height=40,
                                fg_color="darkgray", command=self.show_main_menu)
        back_btn.pack(side="right", padx=10)
        
        # Update departure time display if set
        if self.departure_time:
            dep_time_label.configure(text=f"Departure: {self.format_time_12hr(self.departure_time)}")
    
    def format_time_12hr(self, time_24):
        """Convert 24-hour time to 12-hour format with AM/PM"""
        try:
            h, m = map(int, time_24.split(':'))
            ampm = 'PM' if h >= 12 else 'AM'
            h12 = h % 12 or 12
            return f"{h12}:{m:02d} {ampm}"
        except:
            return time_24

if __name__ == "__main__":
    app = FerryApp()
    app.mainloop()
