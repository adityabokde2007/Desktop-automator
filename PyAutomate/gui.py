import customtkinter as ctk
from file_organizer import FileOrganizer
from task_automator import TaskAutomator
from system_commander import SystemCommander
from config import ASSISTANT_NAME
from profile_store import load_profile, save_profile
import threading
import os
from datetime import datetime

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class PyAutomateGUI:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title('PyAutomate')
        self.root.geometry('680x600')
        self.root.resizable(False, False)
        self.root.configure(bg='#1a1a1a')

        # profile / identity
        self.profile = load_profile()
        self.user_name = self.profile.get('user_name', '')
        self.assistant_name = self.profile.get('assistant_name', ASSISTANT_NAME)

        # modules
        self.file_org = FileOrganizer(log_callback=self.add_log)
        self.task_auto = TaskAutomator(log_callback=self.add_log)
        self.voice_commander = None
        self.voice_thread = None

        # counters
        self.files_organized = 0
        self.tasks_run = 0

        # UI
        self._build_ui()

        # ask once on first run if no saved name exists
        self.root.after(150, self._prompt_for_name_if_needed)

        # periodic updates
        self.update_stats()

    def _build_ui(self):
        # HEADER BAR
        header = ctk.CTkFrame(self.root, fg_color='#111111', height=50, corner_radius=0)
        header.pack(fill='x')
        header.pack_propagate(False)
        # left (icon + title)
        h_left = ctk.CTkFrame(header, fg_color='#111111')
        h_left.pack(side='left', padx=12)
        h_left.pack_propagate(False)
        icon = ctk.CTkLabel(h_left, text='🤖', font=ctk.CTkFont(size=18))
        icon.pack(side='left', padx=(0,8))
        title_frame = ctk.CTkFrame(h_left, fg_color='#111111')
        title_frame.pack(side='left')
        title = ctk.CTkLabel(title_frame, text='PyAutomate', font=ctk.CTkFont(size=18, weight='bold'), text_color='#f37626')
        title.pack(anchor='w')
        subtitle = ctk.CTkLabel(title_frame, text='Windows Automation Suite', font=ctk.CTkFont(size=10), text_color='#9a9a9a')
        subtitle.pack(anchor='w')
        # right (controls) - Warning message
        h_right = ctk.CTkFrame(header, fg_color='#111111')
        h_right.pack(expand=True, padx=50)
        warning_label = ctk.CTkLabel(
            h_right,
            text='Note: For optimal stability, run one module at a time.',
            font=ctk.CTkFont(size=12),
            text_color='#f44747'
        )
        warning_label.pack()
        # bottom border
        header_border = ctk.CTkFrame(self.root, fg_color='#333333', height=1, corner_radius=0)
        header_border.pack(fill='x')

        # STATS ROW (3 cards in grid)
        stats_row = ctk.CTkFrame(self.root, fg_color='#1a1a1a')
        stats_row.pack(fill='x', padx=(16,16), pady=(12,0))
        cards_frame = ctk.CTkFrame(stats_row, fg_color='#1a1a1a')
        cards_frame.pack(fill='x')
        # ensure 3 columns equal width
        cards_frame.grid_columnconfigure((0,1,2), weight=1, uniform='cards')

        def make_card(parent, col, top_color):
            card = ctk.CTkFrame(parent, fg_color='#252526', corner_radius=8)
            card.grid(row=0, column=col, padx=5, pady=0, sticky='nsew')
            # top colored border
            top_border = ctk.CTkFrame(card, fg_color=top_color, height=4, corner_radius=0)
            top_border.pack(fill='x', side='top')
            content = ctk.CTkFrame(card, fg_color='#252526')
            content.pack(fill='both', expand=True, padx=14, pady=14)
            return card, content

        # File Organizer card
        fo_card, fo_content = make_card(cards_frame, 0, '#f37626')
        # top row inside card
        fo_top = ctk.CTkFrame(fo_content, fg_color='#252526')
        fo_top.pack(fill='x')
        fo_icon = ctk.CTkLabel(fo_top, text='📁', font=ctk.CTkFont(size=18))
        fo_icon.pack(side='left')
        self.fo_switch_var = ctk.BooleanVar(value=False)
        self.fo_switch = ctk.CTkSwitch(fo_top, text='', variable=self.fo_switch_var, command=self.toggle_file_organizer, progress_color='#f37626', button_color='#555', width=52, height=28)
        self.fo_switch.pack(side='right')
        # title/status
        fo_title = ctk.CTkLabel(fo_content, text='File Organizer', font=ctk.CTkFont(size=14, weight='bold'))
        fo_title.pack(anchor='w', pady=(8,0))
        self.fo_status = ctk.CTkLabel(fo_content, text='Inactive', text_color='#9a9a9a')
        self.fo_status.pack(anchor='w', pady=(4,8))
        # stat row
        fo_stat_frame = ctk.CTkFrame(fo_content, fg_color='#252526')
        fo_stat_frame.pack(fill='x')
        fo_stat_label = ctk.CTkLabel(fo_stat_frame, text='Files organized', font=ctk.CTkFont(size=10), text_color='#9a9a9a')
        fo_stat_label.pack(side='left')
        self.fo_count_label = ctk.CTkLabel(fo_stat_frame, text='0', font=ctk.CTkFont(size=20, weight='bold'), text_color='#f37626')
        self.fo_count_label.pack(side='right')
        fo_btn = ctk.CTkButton(fo_content, text='Organize Now', command=self.organize_now, width=120, fg_color='#2d6ea6')
        fo_btn.pack(anchor='w', pady=(10,0))

        # Screen Capture card
        ta_card, ta_content = make_card(cards_frame, 1, '#4ec9b0')
        ta_top = ctk.CTkFrame(ta_content, fg_color='#252526')
        ta_top.pack(fill='x')
        ta_icon = ctk.CTkLabel(ta_top, text='⚡', font=ctk.CTkFont(size=18))
        ta_icon.pack(side='left')
        self.ta_switch_var = ctk.BooleanVar(value=False)
        self.ta_switch = ctk.CTkSwitch(ta_top, text='', variable=self.ta_switch_var, command=self.toggle_task_automator, progress_color='#4ec9b0', button_color='#555', width=52, height=28)
        self.ta_switch.pack(side='right')
        ta_title = ctk.CTkLabel(ta_content, text='Screen Capture', font=ctk.CTkFont(size=14, weight='bold'))
        ta_title.pack(anchor='w', pady=(8,0))
        self.ta_status = ctk.CTkLabel(ta_content, text='Inactive', text_color='#9a9a9a')
        self.ta_status.pack(anchor='w', pady=(4,8))
        ta_stat_frame = ctk.CTkFrame(ta_content, fg_color='#252526')
        ta_stat_frame.pack(fill='x')
        ta_stat_label = ctk.CTkLabel(ta_stat_frame, text='Tasks run', font=ctk.CTkFont(size=10), text_color='#9a9a9a')
        ta_stat_label.pack(side='left')
        self.ta_count_label = ctk.CTkLabel(ta_stat_frame, text='0', font=ctk.CTkFont(size=20, weight='bold'), text_color='#4ec9b0')
        self.ta_count_label.pack(side='right')
        # alias used by existing logic
        self.task_switch = self.ta_switch
        self.task_status = self.ta_status

        # Voice Identity card
        pi_card, pi_content = make_card(cards_frame, 2, '#608b4e')
        pi_top = ctk.CTkFrame(pi_content, fg_color='#252526')
        pi_top.pack(fill='x')
        self.pi_icon = ctk.CTkLabel(pi_top, text='👤', font=ctk.CTkFont(size=18))
        self.pi_icon.pack(side='left')
        self.va_switch_var = ctk.BooleanVar(value=False)
        self.va_switch = ctk.CTkSwitch(pi_top, text='', variable=self.va_switch_var, command=self.toggle_voice_assistant, progress_color='#608b4e', button_color='#555', width=52, height=28)
        self.va_switch.pack(side='right')
        pi_title = ctk.CTkLabel(pi_content, text='Voice Assistant', font=ctk.CTkFont(size=14, weight='bold'))
        pi_title.pack(anchor='w', pady=(8,0))
        self.profile_status = ctk.CTkLabel(pi_content, text='Inactive', text_color='#9a9a9a')
        self.profile_status.pack(anchor='w', pady=(4,8))
        pi_stat_frame = ctk.CTkFrame(pi_content, fg_color='#252526')
        pi_stat_frame.pack(fill='x')
        pi_stat_label = ctk.CTkLabel(pi_stat_frame, text='User', font=ctk.CTkFont(size=10), text_color='#9a9a9a')
        pi_stat_label.pack(side='left')
        self.pi_count_label = ctk.CTkLabel(pi_stat_frame, text=self.user_name or 'Not set', font=ctk.CTkFont(size=16, weight='bold'), text_color='#608b4e')
        self.pi_count_label.pack(side='right')
        pi_btn = ctk.CTkButton(pi_content, text='Set Name', command=self.open_name_setup, width=100, fg_color='#2d6ea6')
        pi_btn.pack(anchor='w', pady=(10,0))

        # ACTIVITY LOG label
        log_label = ctk.CTkLabel(self.root, text='Activity Log', text_color='#858585', font=ctk.CTkFont(size=11))
        log_label.pack(anchor='w', padx=16, pady=(12,0))

        # ACTIVITY LOG box (fixed height 180px) with scrollbar
        log_container = ctk.CTkFrame(self.root, fg_color='#1a1a1a')
        log_container.pack(fill='x', padx=(16,16), pady=(6,0))
        self.log_box = ctk.CTkTextbox(log_container, width=648, height=180, corner_radius=8, fg_color='#111111', text_color='#4ec9b0', wrap='none')
        self.log_box.configure(font=('Courier New', 11), state='disabled')
        # scrollbar
        log_scroll = ctk.CTkScrollbar(log_container, orientation='vertical', command=self._on_log_scroll)
        log_scroll.pack(side='right', fill='y')
        try:
            self.log_box.configure(yscrollcommand=log_scroll.set)
        except Exception:
            pass
        self.log_box.pack(fill='x', side='left')
        # tag colors
        try:
            self.log_box.tag_config('info', foreground='#4ec9b0')
            self.log_box.tag_config('file', foreground='#f37626')
            self.log_box.tag_config('success', foreground='#608b4e')
            self.log_box.tag_config('error', foreground='#f44747')
        except Exception:
            pass

        # BOTTOM BAR
        bottom_bar = ctk.CTkFrame(self.root, fg_color='#111111', height=36, corner_radius=0)
        bottom_bar.pack(fill='x', side='bottom')
        bottom_bar.pack_propagate(False)
        self.bottom_label = ctk.CTkLabel(bottom_bar, text=f'Files: 0   Tasks: 0   Name: {self.user_name or "Not set"}', font=ctk.CTkFont(size=11), text_color='#858585')
        self.bottom_label.pack(side='left', padx=12)
        clear_btn = ctk.CTkButton(bottom_bar, text='Clear Log', command=self.clear_log, width=100)
        clear_btn.pack(side='right', padx=12)

    def _prompt_for_name_if_needed(self):
        if not str(self.user_name).strip():
            self.open_name_setup(first_run=True)

    # Logging helper (thread-safe)
    def add_log(self, message):
        timestamp = datetime.now().strftime('%H:%M:%S')

        def insert():
            try:
                self.log_box.configure(state='normal')
                # choose tag based on message content
                tag = 'info'
                low = message.lower()
                if 'error' in low or 'failed' in low:
                    tag = 'error'
                elif message.startswith('✓') or '→' in message:
                    tag = 'file'
                elif message.startswith('✅') or 'replied' in low or 'started' in low:
                    tag = 'success'

                self.log_box.insert('end', f'[{timestamp}] {message}\n', tag)
                # keep view at bottom
                self.log_box.see('end')
                self.log_box.configure(state='disabled')
            except Exception:
                pass

            # update counters based on message content
            if message.startswith('✓') or 'Screenshot saved' in message or 'Deleted' in message:
                if message.startswith('✓'):
                    self.files_organized += 1
                if 'Screenshot saved' in message or 'Deleted' in message:
                    self.tasks_run += 1
                # update labels immediately
                try:
                    self.update_stats_labels()
                except Exception:
                    pass

        # schedule on main thread
        try:
            self.root.after(0, insert)
        except Exception:
            pass

    # File Organizer controls
    def toggle_file_organizer(self):
        if self.fo_switch_var.get():
            try:
                self.file_org.start()
                self.fo_status.configure(text='Ready', text_color='#f37626')
                self.add_log('File Organizer ready — Click "Organize Now" to start')
            except Exception as e:
                self.add_log(f'Error starting File Organizer: {e}')
        else:
            try:
                self.file_org.stop()
                self.fo_status.configure(text='Inactive', text_color='#9a9a9a')
                self.add_log('File Organizer stopped')
            except Exception as e:
                self.add_log(f'Error stopping File Organizer: {e}')

    def organize_now(self):
        # Check if toggle is ON before organizing
        if not self.fo_switch_var.get():
            self.add_log('❌ Error: Please start the toggle first')
            return
        
        def worker():
            try:
                # Step 1: show organizing status
                try:
                    self.root.after(0, lambda: self.fo_status.configure(text='Organizing...', text_color='#f37626'))
                except Exception:
                    pass

                # Step 2: organize all files
                stats = self.file_org.organize_existing()

                # Step 3: show success popup
                try:
                    self.root.after(0, lambda: self._show_organize_popup(stats))
                except Exception:
                    pass

                # Step 4: toggle off automatically
                try:
                    self.root.after(0, self._turn_off_file_organizer)
                except Exception:
                    pass
            except Exception as e:
                self.add_log(f'Error running organize now: {e}')

        threading.Thread(target=worker, daemon=True).start()

    def _turn_off_file_organizer(self):
        try:
            self.fo_switch.deselect()
            self.fo_status.configure(text='Inactive', text_color='#9a9a9a')
        except Exception:
            pass
        self.add_log('✅ Organization complete — Toggle OFF')

    def _show_organize_popup(self, stats):
        try:
            win = ctk.CTkToplevel(self.root)
            win.title('Organization Complete!')
            win.resizable(False, False)
            # window style
            win.configure(fg_color='#1e1e1e')

            # size and center
            win_width = 380
            win_height = 240
            screen_width = win.winfo_screenwidth()
            screen_height = win.winfo_screenheight()
            x = int((screen_width / 2) - (win_width / 2))
            y = int((screen_height / 2) - (win_height / 2))
            win.geometry(f"{win_width}x{win_height}+{x}+{y}")

            # content
            frame = ctk.CTkFrame(win, fg_color='#1e1e1e')
            frame.pack(fill='both', expand=True, padx=18, pady=18)

            total = stats.get('total', 0) if isinstance(stats, dict) else 0
            cats = stats.get('categories', {}) if isinstance(stats, dict) else {}

            header = ctk.CTkLabel(frame, text='✓ Files organized: ' + str(total), font=ctk.CTkFont(size=14, weight='bold'), text_color='#4ec9b0')
            header.pack(anchor='w', pady=(0,8))

            def make_row(text, count):
                row = ctk.CTkFrame(frame, fg_color='#1e1e1e')
                row.pack(fill='x', pady=2)
                chk = ctk.CTkLabel(row, text='✓', text_color='#4ec9b0', font=ctk.CTkFont(size=14))
                chk.pack(side='left')
                lbl = ctk.CTkLabel(row, text=f"{text}: {count}")
                lbl.pack(side='left', padx=8)

            make_row('Documents', cats.get('Documents', 0))
            make_row('Images', cats.get('Images', 0))
            make_row('Music', cats.get('Music', 0))
            make_row('Software', cats.get('Software', 0))
            make_row('Archives', cats.get('Archives', 0))

            btn = ctk.CTkButton(frame, text='OK', width=80, command=win.destroy)
            btn.pack(side='bottom', pady=(12,0))

            # ensure it's on top and focused
            win.lift()
            win.focus_force()
            win.grab_set()

            # auto close after 5 seconds
            try:
                win.after(5000, win.destroy)
            except Exception:
                pass

            # update GUI counters from organizer logs
            try:
                self.files_organized = sum(1 for m in self.file_org.logs if m.startswith('✓'))
                self.update_stats_labels()
            except Exception:
                pass
        except Exception as e:
            self.add_log(f'Failed to show organization popup: {e}')

    def _show_screenshot_popup(self, filename):
        try:
            win = ctk.CTkToplevel(self.root)
            win.title('Screenshot Complete!')
            win.resizable(False, False)
            # window style
            win.configure(fg_color='#1e1e1e')

            # size and center
            win_width = 380
            win_height = 200
            screen_width = win.winfo_screenwidth()
            screen_height = win.winfo_screenheight()
            x = int((screen_width / 2) - (win_width / 2))
            y = int((screen_height / 2) - (win_height / 2))
            win.geometry(f"{win_width}x{win_height}+{x}+{y}")

            # content
            frame = ctk.CTkFrame(win, fg_color='#1e1e1e')
            frame.pack(fill='both', expand=True, padx=18, pady=18)

            header = ctk.CTkLabel(frame, text='✓ Screenshot saved', font=ctk.CTkFont(size=14, weight='bold'), text_color='#4ec9b0')
            header.pack(anchor='w', pady=(0,8))

            # filename
            file_row = ctk.CTkFrame(frame, fg_color='#1e1e1e')
            file_row.pack(fill='x', pady=2)
            chk = ctk.CTkLabel(file_row, text='📸', font=ctk.CTkFont(size=14))
            chk.pack(side='left')
            lbl = ctk.CTkLabel(file_row, text=f"{filename}", text_color='#9a9a9a')
            lbl.pack(side='left', padx=8)

            btn = ctk.CTkButton(frame, text='OK', width=80, command=win.destroy)
            btn.pack(side='bottom', pady=(12,0))

            # ensure it's on top and focused
            win.lift()
            win.focus_force()
            win.grab_set()

            # auto close after 5 seconds
            try:
                win.after(5000, win.destroy)
            except Exception:
                pass
        except Exception as e:
            self.add_log(f'Failed to show screenshot popup: {e}')

    # Screen Capture controls
    def toggle_task_automator(self):
        if self.task_switch.get():
            try:
                self.task_status.configure(text='Taking screenshot...', text_color='#4ec9b0')
                self.task_automator = TaskAutomator(
                    log_callback=self.add_log,
                    main_window=self.root,
                    on_complete=self.task_complete,
                    screenshot_popup=self._show_screenshot_popup
                )
                self.task_auto = self.task_automator
                self.task_automator.start()
            except Exception as e:
                self.add_log(f'Error starting Screen Capture: {e}')
        else:
            try:
                self.task_status.configure(text='Inactive', text_color='#9a9a9a')
                if hasattr(self, 'task_automator') and self.task_automator:
                    self.task_automator.stop()
            except Exception as e:
                self.add_log(f'Error stopping Screen Capture: {e}')

    def task_complete(self):
        self.root.after(100, self._turn_off_task)

    def _turn_off_task(self):
        self.task_switch.deselect()
        self.task_status.configure(
            text='Inactive', text_color='#9a9a9a'
        )
        self.add_log(
            '✅ Screenshot done — Toggle OFF'
        )
        if hasattr(self, 'task_automator') and self.task_automator:
            self.task_automator.is_running = False

    # Voice assistant toggle
    def toggle_voice_assistant(self):
        if self.va_switch_var.get():
            # Check if name is set first
            if not self.user_name or not self.user_name.strip():
                self.add_log('Please set your name first before starting voice assistant')
                self.va_switch.deselect()
                self.open_name_setup(first_run=True)
                return
            try:
                self.profile_status.configure(text='Starting...', text_color='#608b4e')
                self.add_log('Starting Nova voice assistant...')
                self.voice_commander = SystemCommander()
                self.voice_commander.is_listening = True

                def voice_loop():
                    try:
                        self.add_log(f'Nova is listening for {self.user_name}')
                        self.add_log("🎤 Speak to your microphone!")
                        self.add_log("Available Commands:")
                        self.add_log("- 'Please open notepad' | 'Close notepad'")
                        self.add_log("- 'Please open chrome' | 'Close chrome'")
                        self.add_log("- 'Please open whatsapp' | 'Close whatsapp'")
                        self.add_log("- 'Please open youtube' | 'Close youtube'")
                        self.add_log("- 'Please lock the screen' | 'Please tell me the time'")
                        self.add_log("- 'Please mute the mic' | 'Please unmute the mic'")
                        self.add_log("- 'Increase the volume to [number]'")
                        self.add_log("- 'Decrease the volume to [number]'")
                        self.add_log("- 'How are you Nova' | 'Thank you Nova see you later'")
                        try:
                            self.root.after(0, lambda: self.profile_status.configure(text='Listening...', text_color='#608b4e'))
                        except Exception:
                            pass
                        while self.voice_commander and self.voice_commander.is_listening:
                            try:
                                command = self.voice_commander.listen(timeout=8, phrase_time_limit=6, silent=False)
                                if command:
                                    self.add_log(f'Heard: {command}')
                                    if command.lower() == 'thank you nova see you later':
                                        self.voice_commander.speak(f'Goodbye {self.voice_commander.user_name}!')
                                        self.add_log('Voice assistant stopped by voice command')
                                        break
                                    elif 'help' in command.lower():
                                        self.add_log('Say: please open notepad, close whatsapp, please tell me the time, how are you nova')
                                    else:
                                        result = self.voice_commander.process_command(command)
                                        if result:
                                            self.add_log('Command executed successfully')
                            except Exception as e:
                                self.add_log(f'Voice error: {e}')
                    except Exception as e:
                        self.add_log(f'Voice assistant error: {e}')
                    finally:
                        try:
                            self.root.after(0, self._turn_off_voice_assistant)
                        except Exception:
                            pass

                self.voice_thread = threading.Thread(target=voice_loop, daemon=True)
                self.voice_thread.start()
            except Exception as e:
                self.add_log(f'Error starting voice assistant: {e}')
                self.va_switch.deselect()
                self.profile_status.configure(text='Error', text_color='#f44747')
        else:
            self._stop_voice_assistant()

    def _stop_voice_assistant(self):
        try:
            if self.voice_commander:
                self.voice_commander.is_listening = False
                self.voice_commander = None
            self.profile_status.configure(text='Inactive', text_color='#9a9a9a')
            self.add_log('Nova voice assistant stopped')
        except Exception as e:
            self.add_log(f'Error stopping voice assistant: {e}')

    def _turn_off_voice_assistant(self):
        try:
            self.va_switch.deselect()
            self.profile_status.configure(text='Inactive', text_color='#9a9a9a')
        except Exception:
            pass

    # Voice identity controls
    def open_name_setup(self, first_run=False):
        try:
            def create_window():
                win = ctk.CTkToplevel(self.root)
                win.title('Voice Identity')
                win.resizable(False, False)

                # Window size and position
                win_width = 400
                win_height = 320
                screen_width = win.winfo_screenwidth()
                screen_height = win.winfo_screenheight()
                x = int((screen_width / 2) - (win_width / 2))
                y = int((screen_height / 2) - (win_height / 2))
                win.geometry(f"{win_width}x{win_height}+{x}+{y}")

                # Bring to front and focus
                win.lift()
                win.focus_force()
                win.grab_set()

                # Main content frame with padding
                main_frame = ctk.CTkFrame(win, fg_color='#212121')
                main_frame.pack(fill='both', expand=True, padx=30, pady=30)

                title_text = 'Tell me your name' if first_run else 'Update your name'
                title_label = ctk.CTkLabel(main_frame, text=title_text, font=ctk.CTkFont(size=16, weight='bold'))
                title_label.pack(anchor='w', pady=(0, 8))
                hint_label = ctk.CTkLabel(main_frame, text='Nova will use this name for voice replies.', text_color='#9a9a9a', wraplength=320, justify='left')
                hint_label.pack(anchor='w', pady=(0, 12))

                name_label = ctk.CTkLabel(main_frame, text='Your name', font=ctk.CTkFont(size=14))
                name_label.pack(anchor='w', pady=(0, 8))
                name_var = ctk.StringVar(value=self.user_name if self.user_name and self.user_name != ASSISTANT_NAME else '')
                name_entry = ctk.CTkEntry(main_frame, textvariable=name_var, height=35)
                name_entry.pack(fill='x', pady=(0, 16))

                # Buttons frame
                btn_frame = ctk.CTkFrame(main_frame, fg_color='#212121')
                btn_frame.pack(fill='x', pady=(12, 0))
                
                def save_settings():
                    entered_name = name_var.get().strip()
                    if not entered_name:
                        self.add_log('Please enter a name first')
                        return
                    profile = save_profile(user_name=entered_name, assistant_name=self.assistant_name)
                    self.profile = profile
                    self.user_name = profile.get('user_name', entered_name)
                    self.assistant_name = profile.get('assistant_name', ASSISTANT_NAME)
                    
                    # If voice assistant is already running, update its name in real-time
                    if self.voice_commander:
                        self.voice_commander.user_name = self.user_name
                        
                    self._refresh_profile_labels()
                    self.add_log(f'Name saved as {self.user_name}')
                    win.destroy()

                save_btn = ctk.CTkButton(btn_frame, text='Save', command=save_settings, height=35, fg_color='#f37626', hover_color='#e06925')
                save_btn.pack(fill='x', pady=(0, 10))

                if first_run:
                    name_entry.focus_force()

            # ensure window creation happens on the main GUI thread
            self.root.after(0, create_window)
        except Exception as e:
            self.add_log(f'Failed to open Voice Identity setup: {e}')

    def _refresh_profile_labels(self):
        try:
            if hasattr(self, 'pi_count_label'):
                self.pi_count_label.configure(text=self.user_name or 'Not set')
            if hasattr(self, 'profile_status'):
                # Don't overwrite status if voice assistant is actively listening
                if self.voice_commander and self.voice_commander.is_listening:
                    self.profile_status.configure(text='Listening...', text_color='#608b4e')
                    if hasattr(self, 'pi_icon'):
                        self.pi_icon.configure(text='🎤', text_color='#f37626')
                elif self.user_name:
                    self.profile_status.configure(text='Inactive', text_color='#9a9a9a')
                    if hasattr(self, 'pi_icon'):
                        self.pi_icon.configure(text='👤', text_color='#dce4ee')
                else:
                    self.profile_status.configure(text='Set name first', text_color='#9a9a9a')
                    if hasattr(self, 'pi_icon'):
                        self.pi_icon.configure(text='👤', text_color='#dce4ee')
        except Exception:
            pass

    def clear_log(self):
        # clear textbox fully
        try:
            self.log_box.configure(state='normal')
            self.log_box.delete('1.0', 'end')
            self.log_box.configure(state='disabled')
        except Exception:
            pass

        # reset counters
        self.files_organized = 0
        self.tasks_run = 0

        # clear FileOrganizer internal logs
        try:
            if hasattr(self.file_org, 'logs') and isinstance(self.file_org.logs, list):
                self.file_org.logs.clear()
        except Exception:
            pass

        # update UI labels and bottom stats
        try:
            # Clear identity as requested
            self.user_name = ""
            self.assistant_name = ASSISTANT_NAME
            save_profile(user_name="", assistant_name=ASSISTANT_NAME)
            if hasattr(self, 'voice_commander') and self.voice_commander:
                self.voice_commander.user_name = ""
                
            self._refresh_profile_labels()
            self.update_stats_labels()
        except Exception:
            pass

        # write a cleared entry to the log
        self.add_log('🗑️ Log and identity cleared')

    def update_stats(self):
        # sync counters with module state occasionally
        try:
            # task_auto exposes tasks_run
            if hasattr(self.task_auto, 'tasks_run'):
                self.tasks_run = self.task_auto.tasks_run
        except Exception:
            pass

        self.update_stats_labels()
        # schedule next update in 5 seconds
        self.root.after(5000, self.update_stats)

    def update_stats_labels(self):
        # update bottom summary
        try:
            self.bottom_label.configure(text=f'Files: {self.files_organized}   Tasks: {self.tasks_run}   Name: {self.user_name or "Not set"}')
        except Exception:
            pass

        # update per-card counts
        try:
            if hasattr(self, 'fo_count_label'):
                self.fo_count_label.configure(text=str(self.files_organized))
            if hasattr(self, 'ta_count_label'):
                self.ta_count_label.configure(text=str(self.tasks_run))
            if hasattr(self, 'pi_count_label'):
                self.pi_count_label.configure(text=self.assistant_name)
            self._refresh_profile_labels()
        except Exception:
            pass

    def _on_log_scroll(self, *args):
        try:
            # forward scrollbar commands to the textbox
            self.log_box.yview(*args)
        except Exception:
            pass

    def run(self):
        self.root.mainloop()


if __name__ == '__main__':
    app = PyAutomateGUI()
    app.run()
