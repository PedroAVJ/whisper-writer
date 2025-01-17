import subprocess
import os
import signal
import time
from pynput.keyboard import Controller as PynputController
from pynput.keyboard import Key
import pyperclip
import platform

from utils import ConfigManager

def run_command_or_exit_on_failure(command):
    """
    Run a shell command and exit if it fails.

    Args:
        command (list): The command to run as a list of strings.
    """
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        exit(1)

class InputSimulator:
    """
    A class to simulate keyboard input using various methods.
    """

    def __init__(self):
        """
        Initialize the InputSimulator with the specified configuration.
        """
        self.input_method = ConfigManager.get_config_value('post_processing', 'input_method')
        self.dotool_process = None

        # We’ll just initialize Pynput here for cross-platform usage
        self.keyboard = PynputController()
        
        # If there's any platform-specific initialization needed:
        if self.input_method == 'dotool':
            self._initialize_dotool()

    def _initialize_dotool(self):
        """
        Initialize the dotool process for input simulation.
        """
        self.dotool_process = subprocess.Popen("dotool", stdin=subprocess.PIPE, text=True)
        assert self.dotool_process.stdin is not None

    def _terminate_dotool(self):
        """
        Terminate the dotool process if it's running.
        """
        if self.dotool_process:
            os.kill(self.dotool_process.pid, signal.SIGINT)
            self.dotool_process = None

    def typewrite(self, text):
        """
        Simulate typing the given text. On Windows, this now copies to the clipboard
        and pastes it once, restoring the original clipboard contents afterwards.
        """
        # If you're specifically on Windows, do the clipboard-based approach:
        if platform.system().lower().startswith("win"):
            self._typewrite_windows_clipboard(text)
        else:
            # Fallback to existing logic (optional; remove or keep as needed):
            interval = ConfigManager.get_config_value('post_processing', 'writing_key_press_delay')
            if self.input_method == 'pynput':
                self._typewrite_pynput(text, interval)
            elif self.input_method == 'ydotool':
                self._typewrite_ydotool(text, interval)
            elif self.input_method == 'dotool':
                self._typewrite_dotool(text, interval)

    def _typewrite_windows_clipboard(self, text):
        """
        On Windows: copy text to the clipboard in one go, paste it, then restore the original clipboard state.
        """
        # Save the original clipboard content
        original_clip = pyperclip.paste()

        # Copy our desired text
        pyperclip.copy(text)

        # Simulate Ctrl+V
        with self.keyboard.pressed(Key.ctrl):
            self.keyboard.press('v')
            self.keyboard.release('v')

        # Optionally, add a small delay
        time.sleep(0.1)

        # Restore the original clipboard content
        pyperclip.copy(original_clip)

    def _typewrite_pynput(self, text, interval):
        """
        Simulate typing using pynput.
        """
        for char in text:
            self.keyboard.press(char)
            self.keyboard.release(char)
            time.sleep(interval)

    def _typewrite_ydotool(self, text, interval):
        """
        Simulate typing using ydotool.
        """
        cmd = "ydotool"
        run_command_or_exit_on_failure([
            cmd,
            "type",
            "--key-delay",
            str(interval * 1000),
            "--",
            text,
        ])

    def _typewrite_dotool(self, text, interval):
        """
        Simulate typing using dotool.
        """
        assert self.dotool_process and self.dotool_process.stdin
        self.dotool_process.stdin.write(f"typedelay {interval * 1000}\n")
        self.dotool_process.stdin.write(f"type {text}\n")
        self.dotool_process.stdin.flush()

    def cleanup(self):
        """
        Perform cleanup operations, such as terminating the dotool process.
        """
        if self.input_method == 'dotool':
            self._terminate_dotool()
