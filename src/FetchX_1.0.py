import os
import sys
import time
import json
import random
import string
import threading
from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidgetAction, QLabel, QGraphicsDropShadowEffect, QPushButton, QFileDialog, QListWidgetItem
from PIL import Image as PILImage

CONFIG_FILE = "fetchx_config.json"
APP_VERSION = "Release 1.0"

SUPPORTED_FORMATS = ['png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff']

class Task:
    def __init__(self, name, watch_folder, output_folder, width, height, fmt='png', enabled=True):
        self.name = name
        self.watch_folder = watch_folder
        self.output_folder = output_folder
        self.width = width
        self.height = height
        self.format = fmt if fmt else 'png'
        self.enabled = enabled
        self.thread = None
        self.running = False

# Config handling

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
            tasks = []
            for t in data.get("tasks", []):
                fmt = t.get('format', t.get('fmt', 'png'))
                tasks.append(Task(
                    name=t.get('name', ''),
                    watch_folder=t.get('watch_folder', ''),
                    output_folder=t.get('output_folder', ''),
                    width=int(t.get('width', 1366)),
                    height=int(t.get('height', 768)),
                    fmt=fmt,
                    enabled=bool(t.get('enabled', True))
                ))
            return tasks
    return []


def save_config(tasks):
    data = {"tasks": [{
        "name": t.name,
        "watch_folder": t.watch_folder,
        "output_folder": t.output_folder,
        "width": t.width,
        "height": t.height,
        "enabled": t.enabled,
        "format": t.format
    } for t in tasks]}
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Startup registration
def set_startup_enabled(enabled):
    if os.name != 'nt':
        return False
        
    try:
        import winreg
        key = winreg.HKEY_CURRENT_USER
        subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
        
        with winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE) as reg_key:
            if enabled:
                # Register for startup
                exe_path = os.path.abspath(sys.executable)
                script_path = os.path.abspath(__file__)
                # If running as compiled executable
                if getattr(sys, 'frozen', False):
                    command = f'"{exe_path}"'
                else:
                    command = f'"{exe_path}" "{script_path}"'
                
                winreg.SetValueEx(reg_key, "FetchX", 0, winreg.REG_SZ, command)
            else:
                # Remove from startup
                try:
                    winreg.DeleteValue(reg_key, "FetchX")
                except FileNotFoundError:
                    pass  # Key doesn't exist, which is fine
        return True
    except Exception as e:
        print(f"Startup registration failed: {e}")
        return False

def is_startup_enabled():
    if os.name != 'nt':
        return False
        
    try:
        import winreg
        key = winreg.HKEY_CURRENT_USER
        subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
        
        with winreg.OpenKey(key, subkey, 0, winreg.KEY_READ) as reg_key:
            try:
                winreg.QueryValueEx(reg_key, "FetchX")
                return True
            except FileNotFoundError:
                return False
    except Exception:
        return False

# Utilities

def random_name(ext='png'):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8)) + f".{ext}"


def short_path(path):
    parts = os.path.normpath(path).split(os.sep)
    return "/".join(parts[-2:]) + "/" if len(parts) >= 2 else path

# Watcher function

def watcher(task, log_callback, task_index):
    processed_files = set()
    logged_warnings = set()
    task.running = True
    log_callback(f"[Task {task_index}] Watcher started (enabled={task.enabled})")
    try:
        while task.running:
            if not task.enabled:
                time.sleep(0.5)
                continue
            try:
                if not os.path.exists(task.watch_folder):
                    if "watch_folder_missing" not in logged_warnings:
                        log_callback(f"[Task {task_index}] Watch folder is missing: {task.watch_folder}")
                        logged_warnings.add("watch_folder_missing")
                    time.sleep(1)
                    continue
                else:
                    logged_warnings.discard("watch_folder_missing")

                if not os.path.exists(task.output_folder):
                    try:
                        os.makedirs(task.output_folder, exist_ok=True)
                    except Exception as e:
                        if "output_folder_missing" not in logged_warnings:
                            log_callback(f"[Task {task_index}] Output folder is missing and cannot be created: {task.output_folder} ({e})")
                            logged_warnings.add("output_folder_missing")
                        time.sleep(1)
                        continue
                else:
                    logged_warnings.discard("output_folder_missing")

                for filename in os.listdir(task.watch_folder):
                    src_path = os.path.join(task.watch_folder, filename)
                    if not os.path.isfile(src_path):
                        continue
                    lower = filename.lower()
                    if lower.endswith(('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff')) and filename not in processed_files:
                        try:
                            img = PILImage.open(src_path)
                            img = img.resize((task.width, task.height))
                            ext = task.format.lower()
                            if ext == 'jpg':
                                save_ext = 'JPEG'
                            elif ext == 'png':
                                save_ext = 'PNG'
                            elif ext == 'webp':
                                save_ext = 'WEBP'
                            elif ext == 'bmp':
                                save_ext = 'BMP'
                            elif ext == 'tiff':
                                save_ext = 'TIFF'
                            else:
                                save_ext = 'JPEG'

                            rand_name = random_name(ext)
                            save_path = os.path.join(task.output_folder, rand_name)
                            # Ensure RGB if saving JPEG
                            if save_ext == 'JPEG' and img.mode in ('RGBA', 'LA'):
                                bg = PILImage.new("RGB", img.size, (255,255,255))
                                bg.paste(img, mask=img.split()[3])
                                bg.save(save_path, save_ext)
                            else:
                                img.save(save_path, save_ext)

                            if os.path.exists(save_path):
                                try:
                                    os.remove(src_path)
                                except Exception:
                                    pass
                                processed_files.add(filename)
                                log_callback(f"[Task {task_index}] ✔ {filename} → {rand_name}")
                            else:
                                log_callback(f"[Task {task_index}] Failed to save {filename}, original not deleted")
                        except Exception as e:
                            log_callback(f"[Task {task_index}] Error processing {filename}: {e}")
            except Exception as e:
                log_callback(f"[Task {task_index}] Unexpected Error: {e} n/ Sowwy idk what happened :<")
            time.sleep(1)
    finally:
        task.running = False
        log_callback(f"[Task {task_index}] Stopped watching")

# Simple painted switch widget for a smooth rounded toggle
class Switch(QtWidgets.QAbstractButton):
    def __init__(self, checked=False, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self.setCursor(QtGui.QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedSize(48, 26)

    def paintEvent(self, e):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        # background
        rect = QtCore.QRect(0, 0, self.width(), self.height())
        radius = rect.height() / 2
        if self.isChecked():
            bg_brush = QtGui.QBrush(QtGui.QColor('#7a4dff'))
        else:
            bg_brush = QtGui.QBrush(QtGui.QColor('#444'))
        p.setBrush(bg_brush)
        p.setPen(QtGui.QPen(QtGui.QColor('#00000000')))
        p.drawRoundedRect(rect, radius, radius)
        # knob
        knob_radius = self.height() - 6
        if self.isChecked():
            knob_x = self.width() - knob_radius - 3
        else:
            knob_x = 3
        knob_rect = QtCore.QRect(knob_x, 3, knob_radius, knob_radius)
        p.setBrush(QtGui.QBrush(QtGui.QColor('#ffffff')))
        p.drawEllipse(knob_rect)
        p.end()

# Task dialog
class TaskDialog(QtWidgets.QDialog):
    def __init__(self, parent, task=None, is_edit_mode=False):
        super().__init__(parent)
        self.is_edit_mode = is_edit_mode
        self.task_to_delete = task if is_edit_mode else None
        
        if is_edit_mode:
            self.setWindowTitle(f"Edit Task: {task.name}")
        else:
            self.setWindowTitle("Add New Task")
            
        self.setFixedSize(560, 420)
        self.task = task
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(25, 25, 25, 25)

        self.name_edit = QtWidgets.QLineEdit(task.name if task else "")
        self.watch_edit = QtWidgets.QLineEdit(task.watch_folder if task else "")
        self.output_edit = QtWidgets.QLineEdit(task.output_folder if task else "")
        self.width_edit = QtWidgets.QLineEdit(str(task.width if task else 1366))
        self.height_edit = QtWidgets.QLineEdit(str(task.height if task else 768))
        self.enable_checkbox = QtWidgets.QCheckBox("Enabled")
        self.enable_checkbox.setChecked(task.enabled if task else True)

        # Format combobox
        self.format_combo = QtWidgets.QComboBox()
        for f in SUPPORTED_FORMATS:
            self.format_combo.addItem(f".{f}", f)
        current_fmt = task.format if task else 'png'
        idx = SUPPORTED_FORMATS.index(current_fmt) if current_fmt in SUPPORTED_FORMATS else 0
        self.format_combo.setCurrentIndex(idx)

        # Form layout for better organization
        form_layout = QtWidgets.QGridLayout()
        form_layout.setVerticalSpacing(12)
        form_layout.setHorizontalSpacing(20)
        
        form_layout.addWidget(QtWidgets.QLabel("Task Name:"), 0, 0)
        form_layout.addWidget(self.name_edit, 0, 1, 1, 2)
        
        form_layout.addWidget(QtWidgets.QLabel("Watch Folder:"), 1, 0)
        form_layout.addWidget(self.watch_edit, 1, 1)
        watch_btn = QPushButton("Browse")
        watch_btn.clicked.connect(self.browse_watch)
        form_layout.addWidget(watch_btn, 1, 2)
        
        form_layout.addWidget(QtWidgets.QLabel("Output Folder:"), 2, 0)
        form_layout.addWidget(self.output_edit, 2, 1)
        output_btn = QPushButton("Browse")
        output_btn.clicked.connect(self.browse_output)
        form_layout.addWidget(output_btn, 2, 2)
        
        form_layout.addWidget(QtWidgets.QLabel("Width:"), 3, 0)
        form_layout.addWidget(self.width_edit, 3, 1)
        form_layout.addWidget(QtWidgets.QLabel("Height:"), 3, 2)
        form_layout.addWidget(self.height_edit, 3, 3)
        
        form_layout.addWidget(QtWidgets.QLabel("Output Format:"), 4, 0)
        form_layout.addWidget(self.format_combo, 4, 1)
        
        form_layout.addWidget(self.enable_checkbox, 5, 0, 1, 2)
        
        layout.addLayout(form_layout)
        layout.addSpacing(10)

        btn_layout = QtWidgets.QHBoxLayout()
        
        if is_edit_mode:
            delete_btn = QtWidgets.QPushButton("Delete Task")
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #d32f2f;
                    border-radius: 8px;
                    color: white;
                    font-weight: bold;
                    padding: 10px 16px;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background-color: #f44336;
                }
            """)
            delete_btn.clicked.connect(self.delete_task)
            btn_layout.addWidget(delete_btn)
        
        btn_layout.addStretch()
        
        ok_btn = QtWidgets.QPushButton("Save")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self.save_task)
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def browse_watch(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Watch Folder")
        if folder:
            self.watch_edit.setText(folder)

    def browse_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_edit.setText(folder)

    def save_task(self):
        if not self.name_edit.text():
            QtWidgets.QMessageBox.critical(self, "Error", "You must set a task name!")
            return
        if not os.path.exists(self.watch_edit.text()):
            QtWidgets.QMessageBox.critical(self, "Error", "Watch folder does not exist!")
            return
        if not os.path.exists(self.output_edit.text()):
            QtWidgets.QMessageBox.critical(self, "Error", "Output folder does not exist!")
            return
        if self.watch_edit.text() == self.output_edit.text():
            QtWidgets.QMessageBox.critical(self, "Error", "Watch and Output folders cannot be the same!")
            return
        # ensure width/height ints
        try:
            int(self.width_edit.text())
            int(self.height_edit.text())
        except Exception:
            QtWidgets.QMessageBox.critical(self, "Error", "Width and Height must be integers!")
            return
        self.accept()

    def delete_task(self):
        reply = QtWidgets.QMessageBox.question(
            self, 
            "Delete Task", 
            f"Are you sure you want to delete task '{self.task.name}'?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No
        )
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            self.task_to_delete = self.task
            self.accept()

    def get_task_data(self):
        return Task(
            name=self.name_edit.text(),
            watch_folder=self.watch_edit.text(),
            output_folder=self.output_edit.text(),
            width=int(self.width_edit.text()),
            height=int(self.height_edit.text()),
            fmt=self.format_combo.currentData(),
            enabled=self.enable_checkbox.isChecked()
        )

# Custom widget for task list items
class TaskListItemWidget(QtWidgets.QWidget):
    def __init__(self, parent, task: Task, toggle_callback):
        super().__init__(parent)
        self.task = task
        self.toggle_callback = toggle_callback
        self.init_ui()

    def init_ui(self):
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        name_label = QtWidgets.QLabel(self.task.name if self.task.name else "Unnamed Task")
        name_label.setStyleSheet('font-weight:600; font-size:11pt; color: #f0f0f0;')
        name_label.setMinimumWidth(150)
        layout.addWidget(name_label)

        layout.addStretch()

        # Add resolution info
        res_label = QtWidgets.QLabel(f"{self.task.width}×{self.task.height}")
        res_label.setStyleSheet('color:#aaa; padding-right:8px; font-size:9pt;')
        layout.addWidget(res_label)

        fmt_label = QtWidgets.QLabel(f".{self.task.format}")
        fmt_label.setStyleSheet('color:#7a4dff; padding-right:8px; font-weight:bold;')
        layout.addWidget(fmt_label)

        self.switch = Switch(self.task.enabled)
        self.switch.toggled.connect(self.on_toggle)
        layout.addWidget(self.switch)

    def on_toggle(self, checked):
        # call parent callback with the task object
        self.toggle_callback(self.task, checked)

# Animated Button with glow effect
class GlowButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self._animation = QtCore.QVariantAnimation()
        self._animation.valueChanged.connect(self._on_animation_changed)
        self._animation.setDuration(200)
        self._glow_effect = QGraphicsDropShadowEffect()
        self._glow_effect.setBlurRadius(0)
        self._glow_effect.setColor(QtGui.QColor(122, 77, 255, 0))
        self._glow_effect.setOffset(0, 0)
        self.setGraphicsEffect(self._glow_effect)

    def enterEvent(self, event):
        self._animation.setStartValue(0)
        self._animation.setEndValue(15)
        self._animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._animation.setStartValue(15)
        self._animation.setEndValue(0)
        self._animation.start()
        super().leaveEvent(event)

    def _on_animation_changed(self, value):
        self._glow_effect.setBlurRadius(value)
        self._glow_effect.setColor(QtGui.QColor(122, 77, 255, 100))

# Main window
class FetchXWindow(QtWidgets.QWidget):
    def __init__(self, tray_app):
        super().__init__()
        self.tray_app = tray_app
        self.setWindowTitle("FetchX Tasks")
        self.setWindowIcon(QtGui.QIcon("assets/icon.png"))
        self.setFixedSize(700, 600)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.drag_position = None

        self.tasks = load_config()
        self.last_enabled_states = {}
        self.paused = False
        self.init_ui()
        QtCore.QTimer.singleShot(100, self.auto_start_watchers)

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.main_widget = QtWidgets.QWidget(self)
        self.main_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(30,30,30,240); 
                border-radius: 15px;
            }
            QLabel { 
                color: #f0f0f0; 
                font-family: 'Segoe UI Variable'; 
                font-weight: bold; 
                font-size: 12pt;
                background: transparent;
            }
            QPushButton { 
                background-color: #7a4dff; 
                border-radius: 8px; 
                color: white; 
                font-weight: bold;
                padding: 10px 16px;
                min-width: 90px;
                border: none;
            }
            QPushButton:hover { 
                background-color: #8c5eff; 
            }
            QPushButton:disabled {
                background-color: #444;
                color: #888;
            }
            QLineEdit, QComboBox {
                padding: 10px;
                border-radius: 6px;
                background: #252525;
                border: 1px solid #444;
                color: white;
                font-size: 10pt;
            }
            QListWidget{ 
                background: transparent; 
                border: 1px solid #444;
                border-radius: 8px;
                padding: 4px;
                outline: none;
            }
            QListWidget::item {
                background: transparent;
                border-bottom: 1px solid #333;
                border-radius: 6px;
                margin: 2px;
            }
            QListWidget::item:selected {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 rgba(122, 77, 255, 0.4),
                    stop: 1 rgba(122, 77, 255, 0.2));
                border: 1px solid rgba(122, 77, 255, 0.6);
                border-radius: 8px;
            }
            QListWidget::item:hover {
                background: rgba(122, 77, 255, 0.15);
                border-radius: 8px;
            }
            /* Modern Scrollbar Styling */
            QScrollBar:vertical {
                background: transparent;
                width: 12px;
                margin: 0px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background: #7a4dff;
                border-radius: 6px;
                min-height: 30px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: #8c5eff;
            }
            QScrollBar::handle:vertical:pressed {
                background: #6a3dff;
            }
            QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            QScrollBar:horizontal {
                background: transparent;
                height: 12px;
                margin: 0px;
                border: none;
            }
            QScrollBar::handle:horizontal {
                background: #7a4dff;
                border-radius: 6px;
                min-width: 30px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #8c5eff;
            }
            QScrollBar::handle:horizontal:pressed {
                background: #6a3dff;
            }
            QScrollBar::sub-line:horizontal, QScrollBar::add-line:horizontal {
                border: none;
                background: none;
                width: 0px;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
        """)
        layout.addWidget(self.main_widget)
        main_layout = QtWidgets.QVBoxLayout(self.main_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header
        header_layout = QtWidgets.QHBoxLayout()
        header_label = QtWidgets.QLabel("FetchX")
        header_label.setStyleSheet('font-size: 18pt; font-weight: bold; color: #7a4dff; background: transparent;')
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        
        # Status indicator
        self.status_label = QtWidgets.QLabel("● Running")
        self.status_label.setStyleSheet('color: #4CAF50; font-size: 10pt; background: transparent;')
        header_layout.addWidget(self.status_label)
        header_layout.addSpacing(10)
        
        self.exit_btn = GlowButton("✕")
        self.exit_btn.setFixedSize(32, 32)
        self.exit_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(150, 50, 50, 160);
                border: none;
                border-radius: 10px;
                font-size: 14px;
                color: white;
            }
            QPushButton:hover {
                background-color: rgba(200, 80, 80, 200);
            }
        """)
        self.exit_btn.clicked.connect(self.hide_to_tray)
        header_layout.addWidget(self.exit_btn)
        main_layout.addLayout(header_layout)
        main_layout.addSpacing(10)

        # Tasks list header
        tasks_header = QtWidgets.QLabel("Active Tasks")
        tasks_header.setStyleSheet('font-size: 14pt; color: #f0f0f0; padding-bottom: 5px; background: transparent;')
        main_layout.addWidget(tasks_header)

        # Tasks list
        self.task_list = QtWidgets.QListWidget()
        self.task_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.task_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.task_list.currentRowChanged.connect(self.update_buttons)
        self.task_list.itemDoubleClicked.connect(self.edit_task_double_click)
        self.refresh_task_list()
        self.task_list.setFixedHeight(200)
        main_layout.addWidget(self.task_list)

        # Task management buttons
        btn_layout = QtWidgets.QHBoxLayout()
        self.add_btn = GlowButton("Add Task")
        self.add_btn.clicked.connect(self.add_task)
        self.pause_btn = GlowButton("Pause All")
        self.pause_btn.clicked.connect(self.toggle_pause_all)
        
        btn_layout.addWidget(self.add_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.pause_btn)
        main_layout.addLayout(btn_layout)

        # Export / Import
        imp_layout = QtWidgets.QHBoxLayout()
        self.export_btn = GlowButton("Export Config")
        self.export_btn.clicked.connect(self.export_config)
        self.import_btn = GlowButton("Import Config")
        self.import_btn.clicked.connect(self.import_config)
        imp_layout.addWidget(self.export_btn)
        imp_layout.addWidget(self.import_btn)
        main_layout.addLayout(imp_layout)

        self.update_buttons()

        # Log box header
        log_header = QtWidgets.QLabel("Activity Log")
        log_header.setStyleSheet('font-size: 14pt; color: #f0f0f0; padding-bottom: 5px; background: transparent;')
        main_layout.addWidget(log_header)

        # Log box
        self.log_box = QtWidgets.QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMaximumHeight(150)
        self.log_box.setStyleSheet("""
            QTextEdit {
                background: #252525;
                border: 1px solid #444;
                border-radius: 8px;
                padding: 8px;
                color: #e0e0e0;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 9pt;
            }
        """)
        main_layout.addWidget(self.log_box)

        # Footer
        footer_layout = QtWidgets.QHBoxLayout()
        github_label = QLabel("<a href='https://github.com/wyv9/fetchx' style='color:#7a4dff; text-decoration:none;'>Github</a>")
        github_label.setOpenExternalLinks(True)
        github_label.setStyleSheet("background: transparent;")
        footer_layout.addWidget(github_label, alignment=Qt.AlignmentFlag.AlignLeft)
        
        footer_layout.addStretch()
        
        center_label = QLabel("Made by wyv <3")
        center_label.setStyleSheet("color:#f0f0f0; font-weight:bold; background: transparent;")
        footer_layout.addWidget(center_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        footer_layout.addStretch()
        
        version_label = QLabel(APP_VERSION)
        version_label.setStyleSheet("color:#888; font-size:9pt; background: transparent;")
        footer_layout.addWidget(version_label, alignment=Qt.AlignmentFlag.AlignRight)
        
        main_layout.addLayout(footer_layout)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def log(self, msg):
        self.log_box.append(msg)
        # Auto-scroll to bottom and ensure cursor is at end
        cursor = self.log_box.textCursor()
        cursor.movePosition(QtGui.QTextCursor.MoveOperation.End)
        self.log_box.setTextCursor(cursor)
        self.log_box.ensureCursorVisible()

    def refresh_task_list(self):
        self.task_list.clear()
        for t in self.tasks:
            item = QListWidgetItem()
            item.setSizeHint(QtCore.QSize(0, 60))
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            widget = TaskListItemWidget(self, t, self.on_task_toggle)
            self.task_list.addItem(item)
            self.task_list.setItemWidget(item, widget)

    def update_buttons(self):
        pass

    def add_task(self):
        dlg = TaskDialog(self)
        if dlg.exec():
            new_task = dlg.get_task_data()
            self.tasks.append(new_task)
            save_config(self.tasks)
            self.refresh_task_list()
            if new_task.enabled:
                self.start_task(new_task, len(self.tasks))

    def edit_task_double_click(self, item):
        idx = self.task_list.row(item)
        if idx < 0: 
            return
        task = self.tasks[idx]
        dlg = TaskDialog(self, task, is_edit_mode=True)
        if dlg.exec():
            if dlg.task_to_delete:
                self.tasks.remove(dlg.task_to_delete)
                self.stop_task(dlg.task_to_delete)
                save_config(self.tasks)
                self.refresh_task_list()
            else:
                self.stop_task(task)
                self.tasks[idx] = dlg.get_task_data()
                save_config(self.tasks)
                self.refresh_task_list()
                if self.tasks[idx].enabled:
                    self.start_task(self.tasks[idx], idx+1)

    def start_task(self, task, index):
        if not os.path.exists(task.output_folder):
            try:
                os.makedirs(task.output_folder, exist_ok=True)
            except Exception as e:
                self.log(f"[Task {index}] Could not create output folder: {e}")
                return
        if task.thread and task.running:
            return
        task.running = True
        task.enabled = bool(task.enabled)
        task.thread = threading.Thread(target=watcher, args=(task, self.log, index), daemon=True)
        task.thread.start()

    def stop_task(self, task):
        try:
            task.running = False
            if task.thread:
                task.thread.join(timeout=1)
        except Exception:
            pass

    def auto_start_watchers(self):
        for i, t in enumerate(self.tasks):
            if t.enabled:
                self.start_task(t, i+1)

    def hide_to_tray(self):
        self.hide()
        self.tray_app.tray_icon.showMessage(
            "FetchX",
            "App minimized to tray",
            QtWidgets.QSystemTrayIcon.MessageIcon.Information
        )

    def on_task_toggle(self, task_obj, enabled):
        try:
            index = self.tasks.index(task_obj)
        except ValueError:
            return
        task = self.tasks[index]
        task.enabled = enabled
        save_config(self.tasks)
        if enabled:
            if not task.running:
                self.start_task(task, index+1)
            else:
                self.log(f"[Task {index+1}] Enabled")
        else:
            if task.running:
                self.stop_task(task)
            self.log(f"[Task {index+1}] Disabled")

    def export_config(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Config", "fetchx_config_export.json", "JSON Files (*.json)")
        if not path:
            return
        try:
            data = {"tasks": [{
                "name": t.name,
                "watch_folder": t.watch_folder,
                "output_folder": t.output_folder,
                "width": t.width,
                "height": t.height,
                "enabled": t.enabled,
                "format": t.format
            } for t in self.tasks]}
            with open(path, 'w') as f:
                json.dump(data, f, indent=4)
            self.tray_app.tray_icon.showMessage("FetchX", "Config exported successfully", QtWidgets.QSystemTrayIcon.MessageIcon.Information)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to export config: {e}")

    def import_config(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import Config", "", "JSON Files (*.json)")
        if not path:
            return
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            new_tasks = []
            for t in data.get('tasks', []):
                fmt = t.get('format', 'png')
                new_tasks.append(Task(
                    name=t.get('name', ''),
                    watch_folder=t.get('watch_folder', ''),
                    output_folder=t.get('output_folder', ''),
                    width=int(t.get('width', 1366)),
                    height=int(t.get('height', 768)),
                    fmt=fmt,
                    enabled=bool(t.get('enabled', True))
                ))
            for t in self.tasks:
                self.stop_task(t)
            self.tasks = new_tasks
            save_config(self.tasks)
            self.refresh_task_list()
            self.auto_start_watchers()
            self.tray_app.tray_icon.showMessage("FetchX", "Config imported", QtWidgets.QSystemTrayIcon.MessageIcon.Information)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to import config: {e}")

    def toggle_pause_all(self):
        if not self.paused:
            self.last_enabled_states = {i: t.enabled for i, t in enumerate(self.tasks)}
            for t in list(self.tasks):
                if t.enabled:
                    self.on_task_toggle(t, False)
            self.paused = True
            self.pause_btn.setText('Resume All')
            self.status_label.setText("● Paused")
            self.status_label.setStyleSheet('color: #FF9800; font-size: 10pt; background: transparent;')
            self.tray_app.tray_icon.showMessage('FetchX', 'All tasks paused', QtWidgets.QSystemTrayIcon.MessageIcon.Information)
        else:
            for i, t in enumerate(self.tasks):
                was_enabled = self.last_enabled_states.get(i, False)
                if was_enabled:
                    self.on_task_toggle(t, True)
            self.paused = False
            self.pause_btn.setText('Pause All')
            self.status_label.setText("● Running")
            self.status_label.setStyleSheet('color: #4CAF50; font-size: 10pt; background: transparent;')
            self.tray_app.tray_icon.showMessage('FetchX', 'All tasks resumed', QtWidgets.QSystemTrayIcon.MessageIcon.Information)

# Tray app
class FetchXApp(QtWidgets.QApplication):
    def __init__(self, sys_argv):
        super().__init__(sys_argv)
        self.settings_window = FetchXWindow(self)
        
        # Create tray icon with proper icon
        self.tray_icon = QtWidgets.QSystemTrayIcon(self.get_icon())
        self.tray_icon.setVisible(True)
        self.tray_icon.setToolTip("FetchX")
        
        # Create context menu
        self.create_tray_menu()
        
        # Connect signals
        self.tray_icon.activated.connect(self.on_tray_activated)
    
    def get_icon(self):
        try:
            # Method 1: Load from assets folder
            base_dir = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(base_dir, "..", "assets", "assets/icon.png")
            
            if os.path.exists(icon_path):
                return QtGui.QIcon(icon_path)
            
            # Method 2: Load from same directory as script
            icon_path2 = os.path.join(base_dir, "assets/icon.png")
            if os.path.exists(icon_path2):
                return QtGui.QIcon(icon_path2)
                
        except Exception as e:
            print(f"Could not load custom icon: {e}")
        
        # Method 3: System fallback icon
        return QtGui.QIcon.fromTheme("image-file") or QtGui.QIcon.fromTheme("folder")
    
    def create_tray_menu(self):
        menu = QtWidgets.QMenu()
        
        # Header
        top_widget_action = QWidgetAction(menu)
        label = QLabel(f"   FetchX {APP_VERSION}")
        label.setStyleSheet("color: gray; padding: 2px 10px; background: transparent;")
        top_widget_action.setDefaultWidget(label)
        menu.addAction(top_widget_action)
        menu.addSeparator()
        
        # Menu items
        menu.addAction("Settings", self.show_settings)
        menu.addSeparator()
        
        # Startup option
        self.startup_action = QtGui.QAction("Run on Windows Startup", self)
        self.startup_action.setCheckable(True)
        self.startup_action.setChecked(is_startup_enabled())
        self.startup_action.triggered.connect(self.toggle_startup)
        menu.addAction(self.startup_action)
        menu.addSeparator()
        
        menu.addAction("Quit", self.quit)
        
        self.tray_icon.setContextMenu(menu)

    def toggle_startup(self, enabled):
        success = set_startup_enabled(enabled)
        if success:
            self.startup_enabled = enabled
            self.tray_icon.showMessage(
                "FetchX", 
                f"Run on startup {'enabled' if enabled else 'disabled'}", 
                QtWidgets.QSystemTrayIcon.MessageIcon.Information
            )
        else:
            self.startup_action.setChecked(not enabled)  # Revert the checkbox
            self.tray_icon.showMessage(
                "FetchX", 
                "Failed to change startup setting", 
                QtWidgets.QSystemTrayIcon.MessageIcon.Warning
            )

    def on_tray_activated(self, reason):
        if reason == QtWidgets.QSystemTrayIcon.ActivationReason.Trigger:
            self.show_settings()

    def show_settings(self):
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

if __name__ == "__main__":
    if os.name == 'nt':
        import ctypes
        ctypes.windll.kernel32.FreeConsole()
    app = FetchXApp(sys.argv)
    sys.exit(app.exec())