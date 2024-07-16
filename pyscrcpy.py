import tkinter as tk
from tkinter import ttk, messagebox, Menu, Toplevel, Label, Entry, Button
import subprocess
import threading
import json
import os
import time
import sys

class AdbManager:
    def __init__(self, root):
        self.root = root
        self.root.title("PyScrcpy")

        # Create Menu
        self.menubar = Menu(self.root)
        self.root.config(menu=self.menubar)

        filemenu = Menu(self.menubar, tearoff=0)
        filemenu.add_command(label="New", command=self.add_device)
        filemenu.add_command(label="Save", command=self.save_data)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.root.quit)
        self.menubar.add_cascade(label="File", menu=filemenu)

        # Create Tools Menu
        toolsmenu = Menu(self.menubar, tearoff=0)
        toolsmenu.add_command(label="adb devices", command=self.show_adb_devices)
        self.menubar.add_cascade(label="Tools", menu=toolsmenu)

        # Create Help Menu
        helpmenu = Menu(self.menubar, tearoff=0)
        helpmenu.add_command(label="Help", command=self.show_help)
        helpmenu.add_command(label="About", command=self.show_about)
        self.menubar.add_cascade(label="Help", menu=helpmenu)

        # 创建表格标题
        columns = ("DeviceId", "Name", "Status")
        self.tree = ttk.Treeview(root, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor=tk.CENTER)

        # 配置文件路径
        self.config_file = "pyscrcpy.json"
        self.config = {"devices":[]}

        # 加载数据
        self.load_data()
        self.refresh_devices()
        
        self.shutdown = False  # 添加一个标志来跟踪应用程序是否正在关闭+
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        # self.status_thread = threading.Thread(target=self.update_device_status)
        # self.status_thread.start()

        # 表格添加到滚动条中
        vsb = ttk.Scrollbar(root, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")

        self.tree.pack(fill="both", expand=True)

        button_frame = ttk.Frame(self.root)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)
        add_button = ttk.Button(button_frame, text="Add Device", command=self.add_device)
        add_button.pack(side=tk.LEFT, padx=5, pady=5)
        refresh_button = ttk.Button(button_frame, text="Refresh", command=self.refresh_devices)
        refresh_button.pack(side=tk.RIGHT, padx=5, pady=5)


        # 绑定表格的popup菜单
        self.tree.bind("<Button-3>", self.show_right_click_menu)
        
        self.right_click_menu = tk.Menu(self.root, tearoff=False)
        self.right_click_menu.add_command(label="Connect", command=lambda: self.on_right_menu_button_click(f"Connect"))
        self.right_click_menu.add_command(label="Disconnect", command=lambda: self.on_right_menu_button_click(f"Disconnect"))
        self.right_click_menu.add_command(label="Scrcpy", command=lambda: self.on_right_menu_button_click(f"Scrcpy"))

        # self.right_click_menu.add_command(label="Move Up", command=self.move_up)
        # self.right_click_menu.add_command(label="Move Down", command=self.move_down)

        self.right_click_menu.add_command(label="Delete", command=lambda: self.on_right_menu_button_click(f"Delete"))


    def on_close(self):
        self.shutdown = True  # 设置标志，告诉线程是时候退出了
        # 如果有多个线程，这里可以使用join()等待它们结束
        # self.status_thread.join()
        self.root.destroy()

    def show_adb_devices(self):
        adb_devices = self.get_adb_devices()
        str = ''
        for d in adb_devices:
            deviceId = d['DeviceId']
            status = d['Status']
            str += (deviceId + " " + status + "\n")
        messagebox.showinfo("adb devices", str)


    def show_help(self):
        messagebox.showinfo("Help", "This is a simple device manager.\n"
                            "1. Use 'New' to add a new device.\n"
                            "2. Right click device to connect/scrcpy and so on .")
        
    def show_about(self):
        messagebox.showinfo("Version", "v4.7.11")

    def load_data(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as f:
                self.config = json.load(f)
                if "devices" in self.config:
                    self.config["devices"].sort(key=lambda x: x['Order'])
                    for device in self.config["devices"]:
                        row = [device["DeviceId"], device["Name"]]
                        self.tree.insert("", "end", values=row)

    def save_data(self):
        self.config["devices"] = [device for device in self.config["devices"] if device['Order'] != 999]
        with open(self.config_file, "w") as f:
            json.dump(self.config, f, indent=4)

    def refresh_devices(self):
        adb_devices = self.get_adb_devices()
        # print('adb_devices:',adb_devices)

        # clear 
        for d in self.config["devices"]:
            d['Status'] = ''

        for device in adb_devices:
            got = False
            for d in self.config["devices"]:
                if d['DeviceId'] == device['DeviceId']:
                    d['Status'] = device['Status']
                    got = True
                    break
            if not got:
                device["Order"]=999
                self.config["devices"].append(device)   
        self.update_tree()

    def update_device_status(self):
        while not self.shutdown:
            self.refresh_devices()
            time.sleep(10)  # 10秒更新一次

    def add_device(self):
        # 创建一个顶层窗口作为输入对话框
        top = Toplevel(self.root)
        top.title("Add Device")

        # 设备ID输入
        dev_id_label = Label(top, text="DeviceId:")
        dev_id_label.grid(row=0, column=0, padx=5, pady=5)
        self.dev_id_entry = Entry(top)
        self.dev_id_entry.grid(row=0, column=1, padx=5, pady=5)

        # 名称输入
        name_label = Label(top, text="Name (optional):")
        name_label.grid(row=1, column=0, padx=5, pady=5)
        self.name_entry = Entry(top)
        self.name_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # 添加按钮
        add_button = Button(top, text="Add", command=self.add_device_confirm)
        add_button.grid(row=2, column=0, columnspan=2, pady=5)

        top.transient(self.root)

        # root_geometry = self.root.geometry()
        # _, _, root_x, root_y = root_geometry.split('+')
        # top.geometry(f'+{int(root_x)}+{int(root_y)}')

        top.grab_set()
        top.wait_window()

    def add_device_confirm(self):
        device_id = self.dev_id_entry.get()
        name = self.name_entry.get()
        if not device_id:
            messagebox.showerror("Error", "DeviceId cannot be empty")
            return

        # 添加设备到列表和Treeview
        new_device = {'DeviceId': device_id, 'Name': name if name else 'Unnamed', 'Status': 'Unknown', "Order":  len(self.config["devices"])}
        self.config["devices"].append(new_device)
        self.update_tree()
        self.save_data()
        self.root.wait_window()  # 解锁主窗口
        

    def update_tree(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for device in self.config["devices"]:
            self.tree.insert('', 'end', values=(device['DeviceId'], device['Name'], device['Status']))

    def show_right_click_menu(self, event):
        print("right click:", event, self.tree.selection())
        selected_item = self.tree.selection()[0] if self.tree.selection() else None
        if selected_item:
            self.right_click_menu.post(event.x_root, event.y_root)

    def on_right_menu_button_click(self, operation):
        selected = self.tree.selection()[0] if self.tree.selection() else None
        if not selected:
            return
        selected_iterm = self.tree.item(selected, 'values')
        device_id = selected_iterm[0]
        name = selected_iterm[1]
        print("on_right_menu_button_click:", self.tree.selection(), device_id, name)
        result = self.on_button_click(device_id, operation)
        if len(result) >0:
            messagebox.showinfo(operation, result)


    def move_up(self):
        print("move_up:", self.tree.selection())
        selected = self.tree.selection()[0]
        self.tree.move(selected, "", tk.INSERT)

    def move_down(self):
        selected = self.tree.selection()[0]
        next_item = self.tree.next(selected)
        if next_item:
            self.tree.move(selected, "", next_item)

    def run_command(self, command):
        try:
            result = subprocess.run(command, check=True, shell=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"Error executing command: {e}")
            return f"Error executing {command}: {e}"
        

    def async_run_command(self, cmd):
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return ""
        # stdout, stderr = process.communicate()
        # return_code = process.returncode
        # if return_code == 0:
        #     # print(f"Command executed successfully: {cmd}")
        #     # print("Output:\n", stdout)
        #     return stdout
        # else:
        #     # print(f"Command failed with return code {return_code}: {cmd}")
        #     # print("Error:\n", stderr)
        #     return stderr

    def on_button_click(self, device_id, operation):
        if operation == "Connect":
            return self.run_command(f"adb connect {device_id}")
        elif operation == "Disconnect":
            return self.run_command(f"adb disconnect {device_id}")
        elif operation == "Scrcpy":
            return self.async_run_command(f"scrcpy -s {device_id}")
        elif operation == "Delete":
            self.tree.delete(self.tree.selection()[0])
            self.config["devices"] = [device for device in self.config["devices"] if device['DeviceId'] != device_id]
            self.save_data()
            return "delete succ"            

    def get_adb_devices(self):
        try:
            result = subprocess.run(['adb', 'devices'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            if result.returncode == 0:
                devices_output = result.stdout
                lines = devices_output.strip().split('\n')
                header = lines[0].split()  # 通常是列标题："List of devices attached"
                devices_list = []

                for line in lines[1:]:
                    device_info = line.split()
                    if device_info:
                        device_id, device_status = device_info[0], device_info[1]
                        devices_list.append({'DeviceId': device_id, 'Name': '', 'Status': device_status, 'Order':999})
                return devices_list
            else:
                print(f"Error executing 'adb devices': {result.stderr}")
                return []
        except subprocess.CalledProcessError as e:
            print(f"An error occurred while executing 'adb devices': {e}")
            return []
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return []


def center_window(root):
    root.geometry(f'{480}x{320}')

def main():
    root = tk.Tk()
    app = AdbManager(root)
    center_window(root)
    root.mainloop()

if __name__ == "__main__":
    main()