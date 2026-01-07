import json
import os
from datetime import datetime, timedelta

from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.entry import Entry
from fabric.widgets.label import Label
from fabric.widgets.scrolledwindow import ScrolledWindow
from gi.repository import GLib, Gtk

import config.data as data
import modules.icons as icons


class TimersAlarms(Box):
    def __init__(self, **kwargs):
        super().__init__(
            name="timers-alarms",
            orientation="v",
            spacing=8,
            h_expand=True,
            v_expand=True,
        )
        
        self.timers_file = os.path.join(data.CACHE_DIR, "timers.json")
        self.alarms_file = os.path.join(data.CACHE_DIR, "alarms.json")
        
        # Load saved timers and alarms
        self.timers = self._load_data(self.timers_file)
        self.alarms = self._load_data(self.alarms_file)
        
        # Active timer IDs for GLib timeout tracking
        self.active_timers = {}
        
        # Header with mode toggle
        self.mode_stack = Gtk.Stack(
            transition_type=Gtk.StackTransitionType.SLIDE_LEFT_RIGHT,
            transition_duration=250,
        )
        
        # Timer view
        self.timer_view = self._create_timer_view()
        self.mode_stack.add_named(self.timer_view, "timers")
        
        # Alarm view
        self.alarm_view = self._create_alarm_view()
        self.mode_stack.add_named(self.alarm_view, "alarms")
        
        # Mode switcher
        self.switcher = Gtk.StackSwitcher(
            name="timer-alarm-switcher",
            spacing=8,
        )
        self.switcher.set_stack(self.mode_stack)
        self.switcher.set_hexpand(True)
        self.switcher.set_homogeneous(True)
        
        self.add(self.switcher)
        self.add(self.mode_stack)
        
        # Start checking for alarms
        GLib.timeout_add_seconds(1, self._check_alarms)
    
    def _create_timer_view(self):
        """Create the timer interface"""
        view = Box(orientation="v", spacing=8, h_expand=True, v_expand=True)
        
        # Timer input
        input_box = Box(orientation="h", spacing=4)
        
        self.timer_hours = Entry(
            name="timer-input",
            placeholder_text="HH",
            max_length=2,
            width_chars=2,
        )
        self.timer_minutes = Entry(
            name="timer-input",
            placeholder_text="MM",
            max_length=2,
            width_chars=2,
        )
        self.timer_seconds = Entry(
            name="timer-input",
            placeholder_text="SS",
            max_length=2,
            width_chars=2,
        )
        
        self.timer_label_entry = Entry(
            name="timer-label-input",
            placeholder_text="Timer label (optional)",
            h_expand=True,
        )
        
        add_timer_btn = Button(
            name="add-timer-button",
            child=Label(markup=icons.plus),
            on_clicked=self._add_timer,
        )
        
        input_box.add(self.timer_hours)
        input_box.add(Label(label=":"))
        input_box.add(self.timer_minutes)
        input_box.add(Label(label=":"))
        input_box.add(self.timer_seconds)
        input_box.add(self.timer_label_entry)
        input_box.add(add_timer_btn)
        
        view.add(input_box)
        
        # Timer list
        self.timer_list = Box(
            name="timer-list",
            orientation="v",
            spacing=4,
        )
        
        timer_scroll = ScrolledWindow(
            name="timer-scroll",
            min_content_height=200,
            child=self.timer_list,
        )
        
        view.add(timer_scroll)
        
        # Restore saved timers
        self._restore_timers()
        
        return view
    
    def _create_alarm_view(self):
        """Create the alarm interface"""
        view = Box(orientation="v", spacing=8, h_expand=True, v_expand=True)
        
        # Alarm input
        input_box = Box(orientation="h", spacing=4)
        
        self.alarm_hours = Entry(
            name="alarm-input",
            placeholder_text="HH",
            max_length=2,
            width_chars=2,
        )
        self.alarm_minutes = Entry(
            name="alarm-input",
            placeholder_text="MM",
            max_length=2,
            width_chars=2,
        )
        
        self.alarm_label_entry = Entry(
            name="alarm-label-input",
            placeholder_text="Alarm label (optional)",
            h_expand=True,
        )
        
        add_alarm_btn = Button(
            name="add-alarm-button",
            child=Label(markup=icons.plus),
            on_clicked=self._add_alarm,
        )
        
        input_box.add(self.alarm_hours)
        input_box.add(Label(label=":"))
        input_box.add(self.alarm_minutes)
        input_box.add(self.alarm_label_entry)
        input_box.add(add_alarm_btn)
        
        view.add(input_box)
        
        # Alarm list
        self.alarm_list = Box(
            name="alarm-list",
            orientation="v",
            spacing=4,
        )
        
        alarm_scroll = ScrolledWindow(
            name="alarm-scroll",
            min_content_height=200,
            child=self.alarm_list,
        )
        
        view.add(alarm_scroll)
        
        # Restore saved alarms
        self._restore_alarms()
        
        return view
    
    def _add_timer(self, *args):
        """Add a new timer"""
        try:
            hours = int(self.timer_hours.get_text() or 0)
            minutes = int(self.timer_minutes.get_text() or 0)
            seconds = int(self.timer_seconds.get_text() or 0)
            
            total_seconds = hours * 3600 + minutes * 60 + seconds
            
            if total_seconds <= 0:
                return
            
            label = self.timer_label_entry.get_text() or f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            timer_id = str(len(self.timers))
            timer_data = {
                "id": timer_id,
                "label": label,
                "total_seconds": total_seconds,
                "remaining_seconds": total_seconds,
                "active": False,
            }
            
            self.timers.append(timer_data)
            self._save_data(self.timers_file, self.timers)
            self._add_timer_widget(timer_data)
            
            # Clear inputs
            self.timer_hours.set_text("")
            self.timer_minutes.set_text("")
            self.timer_seconds.set_text("")
            self.timer_label_entry.set_text("")
            
        except ValueError:
            pass
    
    def _add_timer_widget(self, timer_data):
        """Add a timer widget to the list"""
        timer_box = Box(
            name="timer-item",
            orientation="h",
            spacing=8,
        )
        
        # Timer label and time
        info_box = Box(orientation="v", spacing=2, h_expand=True)
        
        timer_label = Label(
            name="timer-item-label",
            label=timer_data["label"],
            h_align="start",
        )
        
        time_label = Label(
            name="timer-item-time",
            label=self._format_time(timer_data["remaining_seconds"]),
            h_align="start",
        )
        
        info_box.add(timer_label)
        info_box.add(time_label)
        
        # Control buttons
        start_pause_btn = Button(
            name="timer-control-button",
            child=Label(markup=icons.play if not timer_data["active"] else icons.pause),
            on_clicked=lambda *_: self._toggle_timer(timer_data, timer_box),
        )
        
        reset_btn = Button(
            name="timer-control-button",
            child=Label(markup=icons.refresh),
            on_clicked=lambda *_: self._reset_timer(timer_data, timer_box),
        )
        
        delete_btn = Button(
            name="timer-control-button",
            child=Label(markup=icons.trash),
            on_clicked=lambda *_: self._delete_timer(timer_data, timer_box),
        )
        
        timer_box.add(info_box)
        timer_box.add(start_pause_btn)
        timer_box.add(reset_btn)
        timer_box.add(delete_btn)
        
        timer_box.timer_data = timer_data
        timer_box.time_label = time_label
        timer_box.start_pause_btn = start_pause_btn
        
        self.timer_list.add(timer_box)
        timer_box.show_all()
    
    def _toggle_timer(self, timer_data, timer_box):
        """Start or pause a timer"""
        timer_data["active"] = not timer_data["active"]
        
        if timer_data["active"]:
            # Start timer
            timer_box.start_pause_btn.get_child().set_markup(icons.pause)
            self.active_timers[timer_data["id"]] = GLib.timeout_add_seconds(
                1, self._update_timer, timer_data, timer_box
            )
        else:
            # Pause timer
            timer_box.start_pause_btn.get_child().set_markup(icons.play)
            if timer_data["id"] in self.active_timers:
                GLib.source_remove(self.active_timers[timer_data["id"]])
                del self.active_timers[timer_data["id"]]
        
        self._save_data(self.timers_file, self.timers)
    
    def _update_timer(self, timer_data, timer_box):
        """Update timer countdown"""
        if not timer_data["active"]:
            return False
        
        timer_data["remaining_seconds"] -= 1
        
        if timer_data["remaining_seconds"] <= 0:
            # Timer finished
            self._timer_finished(timer_data, timer_box)
            return False
        
        timer_box.time_label.set_label(self._format_time(timer_data["remaining_seconds"]))
        self._save_data(self.timers_file, self.timers)
        
        return True
    
    def _timer_finished(self, timer_data, timer_box):
        """Handle timer completion"""
        timer_data["active"] = False
        timer_data["remaining_seconds"] = 0
        
        timer_box.time_label.set_label("00:00:00")
        timer_box.start_pause_btn.get_child().set_markup(icons.play)
        
        # Send notification
        from fabric.utils.helpers import exec_shell_command_async
        exec_shell_command_async(
            f'notify-send "Timer Complete" "{timer_data["label"]}" -i alarm-symbolic -u critical'
        )
        
        self._save_data(self.timers_file, self.timers)
    
    def _reset_timer(self, timer_data, timer_box):
        """Reset timer to original time"""
        # Stop if running
        if timer_data["active"]:
            self._toggle_timer(timer_data, timer_box)
        
        timer_data["remaining_seconds"] = timer_data["total_seconds"]
        timer_box.time_label.set_label(self._format_time(timer_data["remaining_seconds"]))
        
        self._save_data(self.timers_file, self.timers)
    
    def _delete_timer(self, timer_data, timer_box):
        """Delete a timer"""
        # Stop if running
        if timer_data["active"]:
            if timer_data["id"] in self.active_timers:
                GLib.source_remove(self.active_timers[timer_data["id"]])
                del self.active_timers[timer_data["id"]]
        
        self.timers = [t for t in self.timers if t["id"] != timer_data["id"]]
        self.timer_list.remove(timer_box)
        
        self._save_data(self.timers_file, self.timers)
    
    def _add_alarm(self, *args):
        """Add a new alarm"""
        try:
            hours = int(self.alarm_hours.get_text() or 0)
            minutes = int(self.alarm_minutes.get_text() or 0)
            
            if hours > 23 or minutes > 59:
                return
            
            label = self.alarm_label_entry.get_text() or f"{hours:02d}:{minutes:02d}"
            
            alarm_data = {
                "id": str(len(self.alarms)),
                "label": label,
                "hours": hours,
                "minutes": minutes,
                "enabled": True,
            }
            
            self.alarms.append(alarm_data)
            self._save_data(self.alarms_file, self.alarms)
            self._add_alarm_widget(alarm_data)
            
            # Clear inputs
            self.alarm_hours.set_text("")
            self.alarm_minutes.set_text("")
            self.alarm_label_entry.set_text("")
            
        except ValueError:
            pass
    
    def _add_alarm_widget(self, alarm_data):
        """Add an alarm widget to the list"""
        alarm_box = Box(
            name="alarm-item",
            orientation="h",
            spacing=8,
        )
        
        # Alarm label and time
        info_box = Box(orientation="v", spacing=2, h_expand=True)
        
        alarm_label = Label(
            name="alarm-item-label",
            label=alarm_data["label"],
            h_align="start",
        )
        
        time_label = Label(
            name="alarm-item-time",
            label=f"{alarm_data['hours']:02d}:{alarm_data['minutes']:02d}",
            h_align="start",
        )
        
        info_box.add(alarm_label)
        info_box.add(time_label)
        
        # Enable/disable switch
        enable_switch = Gtk.Switch(
            active=alarm_data["enabled"],
        )
        enable_switch.connect(
            "notify::active",
            lambda switch, *_: self._toggle_alarm(alarm_data, switch.get_active())
        )
        
        delete_btn = Button(
            name="alarm-control-button",
            child=Label(markup=icons.trash),
            on_clicked=lambda *_: self._delete_alarm(alarm_data, alarm_box),
        )
        
        alarm_box.add(info_box)
        alarm_box.add(enable_switch)
        alarm_box.add(delete_btn)
        
        alarm_box.alarm_data = alarm_data
        
        self.alarm_list.add(alarm_box)
        alarm_box.show_all()
    
    def _toggle_alarm(self, alarm_data, enabled):
        """Enable or disable an alarm"""
        alarm_data["enabled"] = enabled
        self._save_data(self.alarms_file, self.alarms)
    
    def _delete_alarm(self, alarm_data, alarm_box):
        """Delete an alarm"""
        self.alarms = [a for a in self.alarms if a["id"] != alarm_data["id"]]
        self.alarm_list.remove(alarm_box)
        
        self._save_data(self.alarms_file, self.alarms)
    
    def _check_alarms(self):
        """Check if any alarms should trigger"""
        now = datetime.now()
        current_hour = now.hour
        current_minute = now.minute
        
        for alarm in self.alarms:
            if alarm["enabled"] and alarm["hours"] == current_hour and alarm["minutes"] == current_minute:
                # Trigger alarm
                from fabric.utils.helpers import exec_shell_command_async
                exec_shell_command_async(
                    f'notify-send "Alarm" "{alarm["label"]}" -i alarm-symbolic -u critical'
                )
        
        return True
    
    def _restore_timers(self):
        """Restore saved timers"""
        for timer_data in self.timers:
            timer_data["active"] = False  # Don't auto-start on restore
            self._add_timer_widget(timer_data)
    
    def _restore_alarms(self):
        """Restore saved alarms"""
        for alarm_data in self.alarms:
            self._add_alarm_widget(alarm_data)
    
    def _format_time(self, seconds):
        """Format seconds as HH:MM:SS"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def _load_data(self, filepath):
        """Load data from JSON file"""
        if os.path.exists(filepath):
            try:
                with open(filepath, "r") as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _save_data(self, filepath, data):
        """Save data to JSON file"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)