import os
import json
import ctypes
import datetime
import subprocess
import struct
from ctypes import wintypes

# Constants for Win32 API
LVM_FIRST = 0x1000
LVM_GETITEMCOUNT = LVM_FIRST + 4
LVM_GETITEMTEXTW = LVM_FIRST + 115
LVM_GETITEMPOSITION = LVM_FIRST + 16
LVM_SETITEMPOSITION = LVM_FIRST + 15
PROCESS_ALL_ACCESS = 0x1F0FFF
MEM_COMMIT = 0x1000
MEM_RELEASE = 0x8000
PAGE_READWRITE = 0x04
LVIF_TEXT = 0x0001

# 64-bit architecture handling
is_64bit = struct.calcsize("P") * 8 == 64

class LVITEMW(ctypes.Structure):
    _fields_ = [
        ("mask", wintypes.UINT),
        ("iItem", ctypes.c_int),
        ("iSubItem", ctypes.c_int),
        ("state", wintypes.UINT),
        ("stateMask", wintypes.UINT),
        ("pszText", ctypes.c_void_p), # Pointer to string
        ("cchTextMax", ctypes.c_int),
        ("iImage", ctypes.c_int),
        ("lParam", wintypes.LPARAM),
        ("iIndent", ctypes.c_int),
        ("iGroupId", ctypes.c_int),
        ("cColumns", wintypes.UINT),
        ("puColumns", ctypes.POINTER(wintypes.UINT)),
        ("piColFmt", ctypes.POINTER(ctypes.c_int)),
        ("iGroup", ctypes.c_int),
    ]

class IconManager:
    def __init__(self, backup_dir="backups"):
        self.backup_dir = backup_dir
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

    def get_desktop_listview_handle(self):
        """Find the handle of the Desktop SysListView32 control."""
        progman = ctypes.windll.user32.FindWindowW("Progman", "Program Manager")
        shell_dll_defview = ctypes.windll.user32.FindWindowExW(progman, 0, "SHELLDLL_DefView", None)
        
        if not shell_dll_defview:
            # Sometimes it's under WorkerW
            workerw = 0
            while True:
                workerw = ctypes.windll.user32.FindWindowExW(0, workerw, "WorkerW", None)
                if not workerw:
                    break
                shell_dll_defview = ctypes.windll.user32.FindWindowExW(workerw, 0, "SHELLDLL_DefView", None)
                if shell_dll_defview:
                    break
        
        if shell_dll_defview:
            return ctypes.windll.user32.FindWindowExW(shell_dll_defview, 0, "SysListView32", None)
        return None

    def save_icons(self, filename=None):
        """Save current icon positions to a JSON file."""
        hwnd = self.get_desktop_listview_handle()
        if not hwnd:
            print("Could not find Desktop ListView handle")
            return None

        # Get number of icons
        count = ctypes.windll.user32.SendMessageW(hwnd, LVM_GETITEMCOUNT, 0, 0)
        
        # Get process ID of the desktop window
        pid = wintypes.DWORD()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        
        # Open the process to read memory
        process = ctypes.windll.kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
        if not process:
            print("Could not open Desktop process")
            return None

        # Allocate memory in the desktop process for:
        # 1. The POINT struct (for position)
        # 2. The LVITEM struct (for text)
        # 3. The buffer for the text itself
        mem_point = ctypes.windll.kernel32.VirtualAllocEx(process, 0, ctypes.sizeof(wintypes.POINT), MEM_COMMIT, PAGE_READWRITE)
        mem_lvitem = ctypes.windll.kernel32.VirtualAllocEx(process, 0, ctypes.sizeof(LVITEMW), MEM_COMMIT, PAGE_READWRITE)
        text_buffer_size = 512 # Max path usually 260, 512 is safe
        mem_text = ctypes.windll.kernel32.VirtualAllocEx(process, 0, text_buffer_size, MEM_COMMIT, PAGE_READWRITE)

        icons = []

        try:
            for i in range(count):
                # --- Get Position ---
                ctypes.windll.user32.SendMessageW(hwnd, LVM_GETITEMPOSITION, i, mem_point)
                point = wintypes.POINT()
                ctypes.windll.kernel32.ReadProcessMemory(process, mem_point, ctypes.byref(point), ctypes.sizeof(point), None)
                
                # --- Get Text ---
                # Prepare LVITEM struct locally
                lvitem = LVITEMW()
                lvitem.mask = LVIF_TEXT
                lvitem.iItem = i
                lvitem.iSubItem = 0
                lvitem.pszText = mem_text # Point to remote buffer
                lvitem.cchTextMax = text_buffer_size // 2 # WCHARs

                # Write struct to remote memory
                ctypes.windll.kernel32.WriteProcessMemory(process, mem_lvitem, ctypes.byref(lvitem), ctypes.sizeof(lvitem), None)

                # Send message to fill the buffer
                ctypes.windll.user32.SendMessageW(hwnd, LVM_GETITEMTEXTW, i, mem_lvitem)

                # Read the text back
                text_buffer = ctypes.create_unicode_buffer(text_buffer_size // 2)
                ctypes.windll.kernel32.ReadProcessMemory(process, mem_text, ctypes.byref(text_buffer), ctypes.sizeof(text_buffer), None)
                
                icon_name = text_buffer.value
                
                icons.append({
                    "name": icon_name,
                    "x": point.x,
                    "y": point.y
                })
                
        except Exception as e:
            print(f"Error reading memory: {e}")
        finally:
            ctypes.windll.kernel32.VirtualFreeEx(process, mem_point, 0, MEM_RELEASE)
            ctypes.windll.kernel32.VirtualFreeEx(process, mem_lvitem, 0, MEM_RELEASE)
            ctypes.windll.kernel32.VirtualFreeEx(process, mem_text, 0, MEM_RELEASE)
            ctypes.windll.kernel32.CloseHandle(process)

        if filename is None:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = os.path.join(self.backup_dir, f"icons_{timestamp}.json")
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(icons, f, indent=4)
            
        return filename

    def restore_icons(self, filename):
        """Restore icon positions from a JSON file."""
        if not os.path.exists(filename):
            print(f"File not found: {filename}")
            return False

        with open(filename, 'r', encoding='utf-8') as f:
            saved_icons = json.load(f)

        hwnd = self.get_desktop_listview_handle()
        if not hwnd:
            print("Could not find Desktop ListView handle")
            return False

        # Get current icons to map names to indices
        # Re-scan because indices might have changed
        current_icons = self._get_current_icon_indices(hwnd)

        for saved_icon in saved_icons:
            name = saved_icon['name']
            if name in current_icons:
                index = current_icons[name]
                x = saved_icon['x']
                y = saved_icon['y']
                
                # LVM_SETITEMPOSITION: wParam = index, lParam = MAKELPARAM(x, y)
                lparam = (y << 16) | (x & 0xFFFF)
                ctypes.windll.user32.SendMessageW(hwnd, LVM_SETITEMPOSITION, index, lparam)
        
        # Force refresh
        ctypes.windll.user32.InvalidateRect(hwnd, None, True)
        return True

    def _get_current_icon_indices(self, hwnd):
        """Helper to get a map of 'Icon Name' -> Index."""
        count = ctypes.windll.user32.SendMessageW(hwnd, LVM_GETITEMCOUNT, 0, 0)
        pid = wintypes.DWORD()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        process = ctypes.windll.kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
        
        mem_lvitem = ctypes.windll.kernel32.VirtualAllocEx(process, 0, ctypes.sizeof(LVITEMW), MEM_COMMIT, PAGE_READWRITE)
        text_buffer_size = 512
        mem_text = ctypes.windll.kernel32.VirtualAllocEx(process, 0, text_buffer_size, MEM_COMMIT, PAGE_READWRITE)
        
        icon_map = {}
        
        try:
            for i in range(count):
                lvitem = LVITEMW()
                lvitem.mask = LVIF_TEXT
                lvitem.iItem = i
                lvitem.iSubItem = 0
                lvitem.pszText = mem_text
                lvitem.cchTextMax = text_buffer_size // 2

                ctypes.windll.kernel32.WriteProcessMemory(process, mem_lvitem, ctypes.byref(lvitem), ctypes.sizeof(lvitem), None)
                ctypes.windll.user32.SendMessageW(hwnd, LVM_GETITEMTEXTW, i, mem_lvitem)
                
                text_buffer = ctypes.create_unicode_buffer(text_buffer_size // 2)
                ctypes.windll.kernel32.ReadProcessMemory(process, mem_text, ctypes.byref(text_buffer), ctypes.sizeof(text_buffer), None)
                
                icon_map[text_buffer.value] = i
                
        finally:
            ctypes.windll.kernel32.VirtualFreeEx(process, mem_lvitem, 0, MEM_RELEASE)
            ctypes.windll.kernel32.VirtualFreeEx(process, mem_text, 0, MEM_RELEASE)
            ctypes.windll.kernel32.CloseHandle(process)
            
        return icon_map

    def export_registry(self):
        """Export the relevant registry key to a .reg file."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = os.path.join(self.backup_dir, f"registry_backup_{timestamp}.reg")
        key = r"HKEY_CURRENT_USER\Software\Microsoft\Windows\Shell\Bags\1\Desktop"
        
        try:
            subprocess.run(["reg", "export", key, filename, "/y"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return filename
        except subprocess.CalledProcessError as e:
            print(f"Error exporting registry: {e}")
            return None

if __name__ == "__main__":
    # Test run
    manager = IconManager()
    print("Saving icons...")
    saved_file = manager.save_icons()
    print(f"Saved to {saved_file}")
