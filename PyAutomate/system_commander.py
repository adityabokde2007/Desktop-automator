import speech_recognition as sr
import pyttsx3
import subprocess
import pyautogui
import os
import sys
import time
import threading
from datetime import datetime
from pathlib import Path

from config import ASSISTANT_NAME
from file_organizer import FileOrganizer
from profile_store import load_profile, save_profile


class SystemCommander:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.thread_local = threading.local()
        self.profile = load_profile()
        self.assistant_name = self.profile.get('assistant_name', ASSISTANT_NAME)
        self.user_name = self.load_or_setup_name()
        self.is_listening = False
        self.waiting_for_greeting_reply = False
        self.file_organizer = FileOrganizer()
        self.dashboard_script = Path(__file__).parent / 'main.py'

    def _get_engine(self):
        """Retrieve or initialize the thread-local pyttsx3 engine safely."""
        if not hasattr(self.thread_local, 'engine') or self.thread_local.engine is None:
            try:
                import pythoncom
                pythoncom.CoInitialize()
            except Exception:
                pass
            try:
                engine = pyttsx3.init()
                engine.setProperty('rate', 150)
                engine.setProperty('volume', 0.9)
                self.thread_local.engine = engine
            except Exception:
                self.thread_local.engine = None
        return self.thread_local.engine
        
    def load_or_setup_name(self):
        """Load user's name from the saved profile or ask once by mic."""
        saved_name = str(self.profile.get('user_name', '')).strip()
        if saved_name:
            return saved_name

        self.speak('Please say your name after the beep.')
        name = self.listen(timeout=8, phrase_time_limit=4, silent=True)
        if not name:
            name = input('Welcome! What\'s your name? ').strip()
        if not name:
            name = 'Aditya'

        cleaned_name = name.strip().title()
        self.profile = save_profile(user_name=cleaned_name, assistant_name=self.assistant_name)
        return cleaned_name
    
    def speak(self, text):
        """Convert text to speech using raw SAPI5 COM directly (very robust, thread-safe)."""
        try:
            import pythoncom
            import win32com.client
            pythoncom.CoInitialize()
            speaker = win32com.client.Dispatch("SAPI.SpVoice")
            speaker.Speak(text)
        except Exception as e:
            print(f"⚠️ Direct SAPI5 error: {e}")
    
    def listen(self, timeout=10, phrase_time_limit=6, silent=False):
        """Listen for voice commands"""
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.7)
                if not silent:
                    print("🎤 Listening...")
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
                command = self.recognizer.recognize_google(audio).lower()
                if not silent:
                    print(f"✅ You said: {command}")
                return command
        except sr.WaitTimeoutError:
            # No speech detected within the timeout — not an error
            if not silent:
                print("⏳ No speech detected, still listening...")
            return None
        except sr.UnknownValueError:
            if not silent:
                self.speak("Sorry, I did not catch that. Please try again.")
            return None
        except sr.RequestError:
            if not silent:
                self.speak("Network error. Please check your connection.")
            return None
        except Exception as e:
            if not silent:
                print(f"Error: {e}")
            return None

    def _open_dashboard(self):
        try:
            if self.dashboard_script.exists():
                subprocess.Popen([sys.executable, str(self.dashboard_script)])
                self.speak(f"Yes {self.user_name}, opening the project dashboard.")
                print("✅ Opening project dashboard")
                return True
            self.speak("I could not find the project dashboard.")
            return False
        except Exception as e:
            self.speak("Could not open the project dashboard.")
            print(f"❌ Error: {e}")
            return False

    def _toggle_project_panel(self):
        try:
            if self.dashboard_script.exists():
                subprocess.Popen([sys.executable, str(self.dashboard_script)])
                self.speak(f"Yes {self.user_name}, toggling the project panel.")
                print("✅ Project panel toggled")
                return True
            self.speak("I could not find the project panel.")
            return False
        except Exception as e:
            self.speak("Could not toggle the project panel.")
            print(f"❌ Error: {e}")
            return False
    
    def open_app(self, app_name):
        """Open an application"""
        apps = {
            "notepad": "notepad.exe",
            "chrome": "chrome.exe",
            "google chrome": "chrome.exe",
            "firefox": "firefox.exe",
            "calculator": "calc.exe",
            "vlc": "vlc.exe",
            "paint": "mspaint.exe",
            "word": "winword.exe",
            "excel": "excel.exe",
            "powerpoint": "powerpnt.exe",
            "file explorer": "explorer.exe",
            "settings": "ms-settings:",
            "vs code": "code",
            "whatsapp": "whatsapp:",
        }
        
        exe_name = apps.get(app_name.lower())
        if exe_name:
            try:
                # URI-style entries (e.g. ms-settings:) need os.startfile
                if exe_name.endswith(':'):
                    os.startfile(exe_name)
                else:
                    os.system(f"start {exe_name}")
                self.speak(f"Yes {self.user_name}, opening {app_name}.")
                print(f"✅ Opening {app_name}")
                return True
            except Exception as e:
                self.speak(f"Could not open {app_name}")
                print(f"❌ Error: {e}")
                return False
        else:
            self.speak(f"I don't know how to open {app_name}")
            return False

    def focus_window_containing(self, substring):
        """Find a window with substring in its title, restore it and bring it to foreground."""
        try:
            import win32gui
            import win32con
            
            def callback(hwnd, extra):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd).lower()
                    if substring.lower() in title:
                        try:
                            # Restore window if minimized
                            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                            # Bring to foreground
                            win32gui.SetForegroundWindow(hwnd)
                            # Short sleep to allow focus change
                            time.sleep(0.5)
                        except Exception:
                            pass
                        return False  # Stop enumerating
                return True
            win32gui.EnumWindows(callback, None)
        except Exception as e:
            print(f"Error focusing window: {e}")

    def close_app(self, app_name):
        """Close an application"""
        apps = {
            "notepad": "notepad",
            "chrome": "chrome",
            "google chrome": "chrome",
            "whatsapp": "whatsapp",
        }
        
        app_lower = app_name.lower()
        
        if app_lower == "youtube":
            try:
                self.speak(f"Yes {self.user_name}, closing {app_name}.")
                print(f"✅ Closing {app_name}")
                self.focus_window_containing("youtube")
                pyautogui.hotkey('ctrl', 'w')
                return True
            except Exception as e:
                self.speak(f"Could not close {app_name}")
                print(f"❌ Error: {e}")
                return False
                
        # Resolve target process name
        proc_name = apps.get(app_lower, app_lower)
        
        try:
            self.speak(f"Yes {self.user_name}, closing {app_name}.")
            print(f"✅ Closing {app_name}")
            # Use PowerShell stop-process which is extremely robust for Win11 store apps & standard win32 apps
            os.system(f"powershell -command \"Get-Process -Name '*{proc_name}*' -ErrorAction SilentlyContinue | Stop-Process -Force\"")
            return True
        except Exception as e:
            self.speak(f"Could not close {app_name}")
            print(f"❌ Error: {e}")
            return False
    
    def mute_audio(self):
        """Mute system audio"""
        try:
            self.speak("System audio muted.")
            print("✅ System audio muted")
            time.sleep(1) # wait for speech to finish before actually muting
            pyautogui.press('volumemute')
            return True
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
            
    def unmute_audio(self):
        """Unmute system audio"""
        try:
            pyautogui.press('volumemute')
            print("✅ System audio unmuted")
            self.speak("System audio unmuted.")
            return True
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
            
    def adjust_volume(self, direction, amount=None):
        """Adjust volume up or down"""
        try:
            if amount:
                try:
                    target = int(amount)
                    # To set absolute volume: go down 50 times (0%), then up target//2 times
                    pyautogui.press(['volumedown'] * 50)
                    time.sleep(0.1)
                    steps = target // 2
                    if steps > 0:
                        pyautogui.press(['volumeup'] * steps)
                    self.speak(f"Volume set to {target}.")
                    print(f"✅ Volume set to {target}")
                    return True
                except:
                    pass
            
            key = 'volumeup' if direction.lower() == 'up' else 'volumedown'
            for _ in range(3):
                pyautogui.press(key)
                time.sleep(0.05)
            action = "increased" if direction.lower() == 'up' else "decreased"
            self.speak(f"Volume {action}.")
            print(f"✅ Volume {action}")
            return True
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
            
    def lock_screen(self):
        """Lock the screen"""
        try:
            subprocess.run(['rundll32.exe', 'user32.dll,LockWorkStation'])
            self.speak("Locking the screen.")
            print("✅ Screen locked")
            return True
        except Exception as e:
            self.speak("Could not lock the screen")
            print(f"❌ Error: {e}")
            return False
    

    
    def close_window(self):
        """Close the active window"""
        try:
            pyautogui.hotkey('alt', 'F4')
            self.speak("Closing the window.")
            print("✅ Window closed")
            return True
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def get_time(self):
        """Tell the current time"""
        try:
            current_time = datetime.now().strftime("%I:%M %p")
            self.speak(f"The current time is {current_time}")
            print(f"✅ Current time: {current_time}")
            return True
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def shutdown_pc(self):
        """Shutdown the computer"""
        try:
            self.speak(f"Shutting down in 30 seconds. Say cancel to abort.")
            print("⚠️  Computer will shutdown in 30 seconds...")
            time.sleep(5)
            subprocess.run(['shutdown', '/s', '/t', '25'])
            print("✅ Shutdown initiated")
            return True
        except Exception as e:
            self.speak("Could not shutdown the computer")
            print(f"❌ Error: {e}")
            return False
    
    def personalized_greeting(self):
        """Respond to personalized greeting"""
        response = f"I am fine, how can I help you?"
        self.speak(response)
        print(f"✅ {response}")
        self.waiting_for_greeting_reply = True
        return True
    
    def process_command(self, command):
        """Process voice command and execute action"""
        if not command:
            return False
        
        command = command.lower().strip()

        if self.waiting_for_greeting_reply:
            if any(word in command for word in ['fine', 'good', 'great', 'ok', 'okay']):
                self.waiting_for_greeting_reply = False
                self.speak('What work should I do?')
                print('✅ Greeting reply handled')
                return True
            self.waiting_for_greeting_reply = False
        
        import re
        
        # Check for greetings
        if "how are you nova" in command:
            return self.personalized_greeting()
            

            
        if "tell me the time" in command or "what is the time" in command or "what's the time" in command or "current time" in command or "tell me time" in command:
            return self.get_time()
            
        if "lock the screen" in command or "lock screen" in command:
            return self.lock_screen()
            
        if "mute the mic" in command or "mute mic" in command or "mute audio" in command:
            return self.mute_audio()
            
        if "unmute the mic" in command or "unmute mic" in command or "unmute audio" in command:
            return self.unmute_audio()
            
        # Volume controls
        if "increase the volume to" in command:
            match = re.search(r'to (\d+)', command)
            amount = match.group(1) if match else None
            return self.adjust_volume("up", amount)
            
        if "decrease the volume to" in command:
            match = re.search(r'to (\d+)', command)
            amount = match.group(1) if match else None
            return self.adjust_volume("down", amount)
            
        # App controls
        if "open notepad" in command: return self.open_app("notepad")
        if "close notepad" in command: return self.close_app("notepad")
        
        if "open chrome" in command: return self.open_app("chrome")
        if "close chrome" in command: return self.close_app("chrome")
        
        if "open whatsapp" in command: return self.open_app("whatsapp")
        if "close whatsapp" in command: return self.close_app("whatsapp")
        
        if "open youtube" in command:
            self.speak(f"Yes {self.user_name}, opening YouTube.")
            print("✅ Opening YouTube")
            import webbrowser
            webbrowser.open("https://www.youtube.com")
            return True
            
        if "close youtube" in command: return self.close_app("youtube")
        
        if command == "close window" or command == "close this window":
            return self.close_window()
        
        if command == "shutdown" or command == "shut down":
            return self.shutdown_pc()
            
        if 'project dashboard' in command or 'dashboard' in command:
            return self._open_dashboard()
            
        if 'toggle project panel' in command or 'project panel' in command:
            return self._toggle_project_panel()
            
        # Try to open as a general app name
        if "please open" in command and command not in ["please open notepad", "please open chrome", "please open whatsapp"]:
            app_name = command.replace("please open", "").strip()
            if app_name:
                return self.open_app(app_name)
        
        # Unknown command
        self.speak("I didn't understand that command. Please try again.")
        print("❌ Unknown command")
        return False
    
    def display_commands(self):
        """Display available commands"""
        commands = [
            "🎤 Voice Commands Available:",
            "",
            "📱 Applications:",
            "  - 'Please open notepad', 'Close notepad'",
            "  - 'Please open chrome', 'Close chrome'",
            "  - 'Please open whatsapp', 'Close whatsapp'",
            "  - 'Please open youtube', 'Close youtube'",
            "",
            "🔊 Audio:",
            "  - 'Please mute the mic', 'Please unmute the mic'",
            "  - 'Increase the volume to [number]'",
            "  - 'Decrease the volume to [number]'",
            "",
            "💻 System:",
            "  - 'Please lock the screen'",
            "  - 'Please tell me the time'",
            "",
            f"👋 Personal & Other:",
            f"  - 'How are you Nova'",
            "  - 'Help'",
            "  - 'Thank you Nova see you later' (Stop listening)",
        ]
        for cmd in commands:
            print(cmd)
            
    def run(self):
        """Main loop for voice commands"""
        self.speak(f"Hello {self.user_name}. {self.assistant_name} is active.")
        print(f"\n{'='*50}")
        print(f"🎤 System Commander - {self.user_name}'s Voice Assistant")
        print(f"{'='*50}\n")
        self.display_commands()
        print(f"\n{'='*50}")
        print("Say a command to get started!\n")
        
        self.is_listening = True
        
        while self.is_listening:
            try:
                command = self.listen()
                
                if command:
                    if "help" in command:
                        self.display_commands()
                    elif command == "thank you nova see you later":
                        self.speak(f"Goodbye {self.user_name}!")
                        print("✅ Exiting System Commander")
                        break
                    else:
                        self.process_command(command)
                
                print()
            except KeyboardInterrupt:
                self.speak(f"Goodbye {self.user_name}!")
                print("\n✅ Exiting System Commander")
                break
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    commander = SystemCommander()
    commander.run()
