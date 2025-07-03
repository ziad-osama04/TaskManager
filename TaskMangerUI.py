
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QPushButton, QListWidget, QListWidgetItem, 
                             QLineEdit, QSpinBox, QLabel, QMessageBox, QDialog,
                             QDialogButtonBox, QFormLayout, QTextEdit, QMenu,
                             QFrame, QSplitter, QGroupBox, QComboBox, QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon, QPainter, QPixmap, QIntValidator
from datetime import datetime
import heapq
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import re
from typing import List, Dict
import os
from email.header import decode_header
import json

# Import your existing TaskManager class (assuming it's in the same file or imported)
# For this example, I'll include a simplified version of the necessary classes

class Task:
    def __init__(self, task_id, title, priority=1):
        self.task_id = task_id
        self.title = title
        self.priority = priority
        self.completed = False
        self.created_at = datetime.now()

    def __lt__(self, other):
        return self.priority > other.priority

class TaskManager:
    def __init__(self):
        self.tasks = {}
        self.priority_queue = []
        self.history = []
        
    def add_task(self, task_id, title, priority=1):
        if task_id in self.tasks.keys():
            return False
        task = Task(task_id, title, priority)
        self.tasks[task_id] = task
        heapq.heappush(self.priority_queue, (-task.priority, task_id))
        self._save_to_history("add", task_id)
        return True

    def get_task(self, task_id):
        return self.tasks.get(task_id, None)

    def remove_task(self, task_id):
        if task_id in self.tasks:
            task_copy = self.tasks[task_id]
            del self.tasks[task_id]
            self._save_to_history("remove", (task_id, task_copy))
            return True
        return False

    def complete_task(self, task_id):
        if task_id in self.tasks:
            current_task = self.tasks[task_id]
            current_task.completed = True
            self._save_to_history("complete", task_id)
            return True
        return False

    def get_all_tasks(self):
        return list(self.tasks.values())

    def get_stats(self):
        total = len(self.tasks)
        completed = sum(1 for task in self.tasks.values() if task.completed)
        pending = total - completed
        return {"total": total, "completed": completed, "pending": pending}

    def linear_search(self, title):
        results = []
        search_term = title.lower()
        for task in self.tasks.values():
            if search_term in task.title.lower():
                results.append(task)
        return results

    def sort_by_priority(self):
        task_list = list(self.tasks.values())
        task_list.sort(key=lambda x: x.priority, reverse=True)
        return task_list

    def sort_by_date(self):
        task_list = list(self.tasks.values())
        task_list.sort(key=lambda x: x.created_at, reverse=True)
        return task_list

    def undo(self):
        if not self.history:
            return False
        last_operation = self.history.pop()
        if last_operation[0] == "add":
            task_id = last_operation[1]
            self.tasks.pop(task_id, None)
            self.priority_queue = [
                item for item in self.priority_queue if item[1] != task_id
            ]
            heapq.heapify(self.priority_queue)
            return True
        elif last_operation[0] == "remove":
            task_id, task = last_operation[1]
            self.tasks[task_id] = task
            heapq.heappush(self.priority_queue, (-task.priority, task_id))
            return True
        elif last_operation[0] == "complete":
            task_id = last_operation[1]
            if task_id in self.tasks:
                self.tasks[task_id].completed = False
                return True
        return False

    def _save_to_history(self, operation, data):
        self.history.append((operation, data))
        if len(self.history) > 10:
            self.history.pop(0)

class TaskWidget(QWidget):
    """Custom widget for displaying individual tasks"""
    task_action = pyqtSignal(str, str)  # task_id, action
    
    def __init__(self, task, parent=None):
        super().__init__(parent)
        self.task = task
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Task info
        task_info = QLabel(f"#{self.task.task_id}: {self.task.title}")
        task_info.setFont(QFont("Arial", 10, QFont.Bold))
        
        # Priority indicator
        priority_label = QLabel(f"Priority: {self.task.priority}")
        priority_label.setStyleSheet(self.get_priority_style())
        
        # Status indicator
        status_label = QLabel("✓ Completed" if self.task.completed else "⏳ Pending")
        status_label.setStyleSheet("color: green;" if self.task.completed else "color: orange;")
        
        # Date
        date_label = QLabel(self.task.created_at.strftime("%Y-%m-%d %H:%M"))
        date_label.setStyleSheet("color: gray; font-size: 9px;")
        
        layout.addWidget(task_info)
        layout.addStretch()
        layout.addWidget(priority_label)
        layout.addWidget(status_label)
        layout.addWidget(date_label)
        
        self.setLayout(layout)
        self.setStyleSheet("""
            TaskWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                margin: 2px;
            }
            TaskWidget:hover {
                background-color: #f0f8ff;
                border-color: #4a90e2;
            }
        """)
        
    def get_priority_style(self):
        colors = {
            1: "background-color: #e3f2fd; color: #1976d2; padding: 2px 6px; border-radius: 10px;",
            2: "background-color: #f3e5f5; color: #7b1fa2; padding: 2px 6px; border-radius: 10px;",
            3: "background-color: #fff3e0; color: #f57c00; padding: 2px 6px; border-radius: 10px;",
            4: "background-color: #ffebee; color: #d32f2f; padding: 2px 6px; border-radius: 10px;",
            5: "background-color: #ffcdd2; color: #b71c1c; padding: 2px 6px; border-radius: 10px; font-weight: bold;"
        }
        return colors.get(self.task.priority, colors[1])
        
    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.show_context_menu(event.globalPos())
        super().mousePressEvent(event)
        
    def show_context_menu(self, position):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 6px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 16px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #4a90e2;
                color: white;
            }
        """)
        
        if not self.task.completed:
            complete_action = menu.addAction("✓ Mark as Completed")
            complete_action.triggered.connect(lambda: self.task_action.emit(self.task.task_id, "complete"))
        else:
            uncomplete_action = menu.addAction("↺ Mark as Incomplete")
            uncomplete_action.triggered.connect(lambda: self.task_action.emit(self.task.task_id, "uncomplete"))
            
        menu.addSeparator()
        edit_action = menu.addAction("✏️ Edit Task")
        edit_action.triggered.connect(lambda: self.task_action.emit(self.task.task_id, "edit"))
        
        delete_action = menu.addAction("🗑️ Delete Task")
        delete_action.triggered.connect(lambda: self.task_action.emit(self.task.task_id, "delete"))
        
        menu.exec_(position)

class AddTaskDialog(QDialog):
    def __init__(self, parent=None, task=None):
        super().__init__(parent)
        self.task = task
        self.setWindowTitle("Edit Task" if task else "Add New Task")
        self.setFixedSize(400, 200)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QFormLayout()
        
        # Task ID - Modified to only accept numbers
        self.task_id_input = QLineEdit()
        # Set validator to only accept positive integers
        validator = QIntValidator(1, 999999)  # Allow numbers from 1 to 999999
        self.task_id_input.setValidator(validator)
        self.task_id_input.setPlaceholderText("Enter numeric task ID (e.g., 1, 123, 5678)")
        if self.task:
            self.task_id_input.setText(str(self.task.task_id))
            self.task_id_input.setEnabled(False)
        
        # Title
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Enter task description...")
        if self.task:
            self.title_input.setText(self.task.title)
        
        # Priority
        self.priority_input = QSpinBox()
        self.priority_input.setRange(1, 5)
        if self.task:
            self.priority_input.setValue(self.task.priority)
        else:
            self.priority_input.setValue(1)
            
        layout.addRow("Task ID (numbers only):", self.task_id_input)
        layout.addRow("Title:", self.title_input)
        layout.addRow("Priority (1-5):", self.priority_input)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        layout.addRow(buttons)
        self.setLayout(layout)
        
        # Styling
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
            QLineEdit, QSpinBox {
                padding: 8px;
                border: 2px solid #e9ecef;
                border-radius: 6px;
                font-size: 12px;
            }
            QLineEdit:focus, QSpinBox:focus {
                border-color: #4a90e2;
            }
            QPushButton {
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
        """)
        
    def get_data(self):
        return {
            'task_id': self.task_id_input.text(),
            'title': self.title_input.text(),
            'priority': self.priority_input.value()
        }

class EmailTaskExtractor:
    def __init__(self):
        self.imap_server = None
        self.smtp_server = None
        
    def connect_to_email(self, email_address, password, imap_server="imap.gmail.com", smtp_server="smtp.gmail.com"):
        """Connect to email account"""
        try:
            # Connect to IMAP server
            self.imap_server = imaplib.IMAP4_SSL(imap_server)
            self.imap_server.login(email_address, password)
            return True
        except Exception as e:
            print(f"Failed to connect to email: {e}")
            return False
    
    def extract_tasks_from_emails(self, folder="INBOX", days_back=7):
        """Extract potential tasks from emails"""
        if not self.imap_server:
            return []
            
        try:
            self.imap_server.select(folder)
            
            # Search for emails from the last N days
            date_since = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")
            _, message_ids = self.imap_server.search(None, f'SINCE {date_since}')
            
            tasks = []
            task_keywords = ['todo', 'task', 'deadline', 'urgent', 'action required', 'follow up', 'reminder']
            
            for msg_id in message_ids[0].split()[:20]:  # Limit to 20 most recent emails
                _, msg_data = self.imap_server.fetch(msg_id, '(RFC822)')
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)
                
                # Get email details
                subject = self.decode_header_value(email_message['Subject'])
                sender = email_message['From']
                date_received = email_message['Date']
                
                # Extract body text
                body = self.get_email_body(email_message)
                
                # Check if email contains task-related keywords
                combined_text = f"{subject} {body}".lower()
                if any(keyword in combined_text for keyword in task_keywords):
                    # Extract potential task from subject or body
                    task_text = self.extract_task_text(subject, body)
                    if task_text:
                        tasks.append({
                            'title': task_text,
                            'source': f"Email from {sender}",
                            'date': date_received,
                            'priority': self.determine_priority(combined_text)
                        })
            
            return tasks
            
        except Exception as e:
            print(f"Error extracting tasks from emails: {e}")
            return []
    
    def decode_header_value(self, header_value):
        """Decode email header value"""
        if header_value is None:
            return ""
        
        decoded_parts = decode_header(header_value)
        decoded_string = ""
        
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                decoded_string += part.decode(encoding or 'utf-8', errors='ignore')
            else:
                decoded_string += part
                
        return decoded_string
    
    def get_email_body(self, email_message):
        """Extract email body text"""
        body = ""
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
                    except:
                        continue
        else:
            try:
                body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
            except:
                body = str(email_message.get_payload())
        
        return body[:500]  # Limit body length
    
    def extract_task_text(self, subject, body):
        """Extract meaningful task text from email"""
        # Priority to subject line for task extraction
        if subject and len(subject.strip()) > 5:
            return subject.strip()[:100]  # Limit length
        
        # If subject is not useful, try to extract from body
        lines = body.split('\n')
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if len(line) > 10 and len(line) < 100:
                return line
        
        return subject.strip()[:50] if subject else "Email task"
    
    def determine_priority(self, text):
        """Determine priority based on email content"""
        urgent_words = ['urgent', 'asap', 'immediate', 'critical', 'deadline']
        high_words = ['important', 'priority', 'soon', 'action required']
        
        text_lower = text.lower()
        
        if any(word in text_lower for word in urgent_words):
            return 5
        elif any(word in text_lower for word in high_words):
            return 3
        else:
            return 2
    
    def disconnect(self):
        """Disconnect from email server"""
        if self.imap_server:
            try:
                self.imap_server.close()
                self.imap_server.logout()
            except:
                pass

class EmailConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Email Configuration")
        self.setFixedSize(400, 300)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QFormLayout()
        
        # Email address
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("your.email@gmail.com")
        
        # Password (or app password for Gmail)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Your email password or app password")
        
        # IMAP Server
        self.imap_input = QLineEdit()
        self.imap_input.setText("imap.gmail.com")
        self.imap_input.setPlaceholderText("imap.gmail.com")
        
        # Days back
        self.days_input = QSpinBox()
        self.days_input.setRange(1, 30)
        self.days_input.setValue(7)
        
        # Folder
        self.folder_input = QLineEdit()
        self.folder_input.setText("INBOX")
        self.folder_input.setPlaceholderText("INBOX")
        
        layout.addRow("Email Address:", self.email_input)
        layout.addRow("Password:", self.password_input)
        layout.addRow("IMAP Server:", self.imap_input)
        layout.addRow("Days to look back:", self.days_input)
        layout.addRow("Email Folder:", self.folder_input)
        
        # Info label
        info_label = QLabel("Note: For Gmail, use an App Password instead of your regular password.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-size: 10px; margin: 10px;")
        layout.addRow(info_label)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        layout.addRow(buttons)
        self.setLayout(layout)
        
        # Styling
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
            QLineEdit, QSpinBox {
                padding: 8px;
                border: 2px solid #e9ecef;
                border-radius: 6px;
                font-size: 12px;
            }
            QLineEdit:focus, QSpinBox:focus {
                border-color: #4a90e2;
            }
            QPushButton {
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
        """)
        
    def get_config(self):
        return {
            'email': self.email_input.text(),
            'password': self.password_input.text(),
            'imap_server': self.imap_input.text(),
            'days_back': self.days_input.value(),
            'folder': self.folder_input.text()
        }

class TaskManagerUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.task_manager = TaskManager()
        self.email_extractor = EmailTaskExtractor()
        self.current_filter = "all"
        self.setup_ui()
        self.refresh_task_list()
        
    def setup_ui(self):
        self.setWindowTitle("Task Manager Pro")
        self.setGeometry(100, 100, 1000, 700)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Left panel (controls)
        left_panel = self.create_left_panel()
        
        # Right panel (task list)
        right_panel = self.create_right_panel()
        
        # Splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 700])
        
        main_layout.addWidget(splitter)
        
        # Styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
            QPushButton:pressed {
                background-color: #2a5d94;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #495057;
            }
        """)
        
    def create_left_panel(self):
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Add Task Group
        add_group = QGroupBox("Add New Task")
        add_layout = QVBoxLayout()
        
        add_btn = QPushButton("➕ Add Task")
        add_btn.clicked.connect(self.add_task)
        add_layout.addWidget(add_btn)
        add_group.setLayout(add_layout)
        
        # Search Group
        search_group = QGroupBox("Search & Filter")
        search_layout = QVBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search tasks...")
        self.search_input.textChanged.connect(self.search_tasks)
        
        # Filter buttons
        filter_layout = QHBoxLayout()
        self.all_btn = QPushButton("All")
        self.pending_btn = QPushButton("Pending")
        self.completed_btn = QPushButton("Completed")
        
        self.all_btn.clicked.connect(lambda: self.set_filter("all"))
        self.pending_btn.clicked.connect(lambda: self.set_filter("pending"))
        self.completed_btn.clicked.connect(lambda: self.set_filter("completed"))
        
        filter_layout.addWidget(self.all_btn)
        filter_layout.addWidget(self.pending_btn)
        filter_layout.addWidget(self.completed_btn)
        
        search_layout.addWidget(self.search_input)
        search_layout.addLayout(filter_layout)
        search_group.setLayout(search_layout)
        
        # Sort Group
        sort_group = QGroupBox("Sort Options")
        sort_layout = QVBoxLayout()
        
        sort_priority_btn = QPushButton("📊 Sort by Priority")
        sort_date_btn = QPushButton("📅 Sort by Date")
        
        sort_priority_btn.clicked.connect(self.sort_by_priority)
        sort_date_btn.clicked.connect(self.sort_by_date)
        
        sort_layout.addWidget(sort_priority_btn)
        sort_layout.addWidget(sort_date_btn)
        sort_group.setLayout(sort_layout)
        
        # Email Group
        email_group = QGroupBox("Email Integration")
        email_layout = QVBoxLayout()
        
        extract_email_btn = QPushButton("📧 Extract Tasks from Email")
        extract_email_btn.clicked.connect(self.extract_email_tasks)
        email_layout.addWidget(extract_email_btn)
        email_group.setLayout(email_layout)
        
        # Actions Group
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout()
        
        undo_btn = QPushButton("↺ Undo")
        stats_btn = QPushButton("📈 View Stats")
        
        undo_btn.clicked.connect(self.undo_action)
        stats_btn.clicked.connect(self.show_stats)
        
        actions_layout.addWidget(undo_btn)
        actions_layout.addWidget(stats_btn)
        actions_group.setLayout(actions_layout)
        
        # Add all groups to layout
        layout.addWidget(add_group)
        layout.addWidget(search_group)
        layout.addWidget(sort_group)
        layout.addWidget(email_group)
        layout.addWidget(actions_group)
        layout.addStretch()
        
        panel.setLayout(layout)
        return panel
        
    def create_right_panel(self):
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("Task List")
        header.setFont(QFont("Arial", 16, QFont.Bold))
        header.setStyleSheet("color: #495057; margin: 10px;")
        
        # Task list (scroll area)
        self.scroll_area = QScrollArea()
        self.task_list_widget = QWidget()
        self.task_layout = QVBoxLayout()
        self.task_list_widget.setLayout(self.task_layout)
        
        self.scroll_area.setWidget(self.task_list_widget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f8f9fa;
            }
        """)
        
        layout.addWidget(header)
        layout.addWidget(self.scroll_area)
        
        panel.setLayout(layout)
        return panel
        
    def refresh_task_list(self):
        # Clear existing widgets
        for i in reversed(range(self.task_layout.count())):
            child = self.task_layout.itemAt(i)
            if child is not None:
                widget = child.widget()
                if widget is not None:
                    widget.setParent(None)
            
        # Get tasks based on current filter
        tasks = self.get_filtered_tasks()
        
        if not tasks:
            empty_label = QLabel("No tasks found")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("color: #6c757d; font-size: 14px; margin: 50px;")
            self.task_layout.addWidget(empty_label)
        else:
            for task in tasks:
                task_widget = TaskWidget(task)
                task_widget.task_action.connect(self.handle_task_action)
                self.task_layout.addWidget(task_widget)
                
        self.task_layout.addStretch()
        
    def get_filtered_tasks(self):
        tasks = self.task_manager.get_all_tasks()
        
        if self.current_filter == "pending":
            tasks = [t for t in tasks if not t.completed]
        elif self.current_filter == "completed":
            tasks = [t for t in tasks if t.completed]
            
        # Apply search filter if search text exists
        search_text = getattr(self, 'search_input', None)
        if search_text and search_text.text():
            search_term = search_text.text().lower()
            tasks = [t for t in tasks if search_term in t.title.lower()]
            
        return tasks
        
    def set_filter(self, filter_type):
        self.current_filter = filter_type
        self.refresh_task_list()
        
        # Update button styles
        buttons = [self.all_btn, self.pending_btn, self.completed_btn]
        for btn in buttons:
            btn.setStyleSheet("background-color: #6c757d;")
            
        if filter_type == "all":
            self.all_btn.setStyleSheet("background-color: #4a90e2;")
        elif filter_type == "pending":
            self.pending_btn.setStyleSheet("background-color: #4a90e2;")
        elif filter_type == "completed":
            self.completed_btn.setStyleSheet("background-color: #4a90e2;")
            
    def add_task(self):
        dialog = AddTaskDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            if data['task_id'] and data['title']:
                # Validate that task_id is numeric (additional check)
                if not data['task_id'].isdigit():
                    QMessageBox.warning(self, "Error", "Task ID must be a number!")
                    return
                    
                success = self.task_manager.add_task(data['task_id'], data['title'], data['priority'])
                if success:
                    self.refresh_task_list()
                    QMessageBox.information(self, "Success", "Task added successfully!")
                else:
                    QMessageBox.warning(self, "Error", "Task ID already exists!")
            else:
                QMessageBox.warning(self, "Error", "Please fill all fields!")
                
    def handle_task_action(self, task_id, action):
        try:
            if action == "complete":
                self.task_manager.complete_task(task_id)
                self.refresh_task_list()
                QMessageBox.information(self, "Success", "Task marked as completed!")
            elif action == "uncomplete":
                task = self.task_manager.get_task(task_id)
                if task:
                    task.completed = False
                    self.refresh_task_list()
                    QMessageBox.information(self, "Success", "Task marked as incomplete!")
            elif action == "edit":
                task = self.task_manager.get_task(task_id)
                if task:
                    dialog = AddTaskDialog(self, task)
                    if dialog.exec_() == QDialog.Accepted:
                        data = dialog.get_data()
                        if data['title']:  # Only title can be edited for existing tasks
                            task.title = data['title']
                            task.priority = data['priority']
                            self.refresh_task_list()
                            QMessageBox.information(self, "Success", "Task updated successfully!")
                        else:
                            QMessageBox.warning(self, "Error", "Title cannot be empty!")
            elif action == "delete":
                reply = QMessageBox.question(self, "Confirm Delete", 
                                           f"Are you sure you want to delete task '{task_id}'?",
                                           QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.Yes:
                    if self.task_manager.remove_task(task_id):
                        self.refresh_task_list()
                        QMessageBox.information(self, "Success", "Task deleted successfully!")
                    else:
                        QMessageBox.warning(self, "Error", "Failed to delete task!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
                
    def search_tasks(self):
        self.refresh_task_list()
        
    def sort_by_priority(self):
        # This will be handled by refresh_task_list if we modify get_filtered_tasks
        tasks = self.task_manager.sort_by_priority()
        self.display_sorted_tasks(tasks)
        
    def sort_by_date(self):
        tasks = self.task_manager.sort_by_date()
        self.display_sorted_tasks(tasks)
        
    def display_sorted_tasks(self, tasks):
        # Clear existing widgets
        for i in reversed(range(self.task_layout.count())):
            child = self.task_layout.itemAt(i)
            if child is not None:
                widget = child.widget()
                if widget is not None:
                    widget.setParent(None)
            
        for task in tasks:
            task_widget = TaskWidget(task)
            task_widget.task_action.connect(self.handle_task_action)
            self.task_layout.addWidget(task_widget)
            
        self.task_layout.addStretch()
        
    def undo_action(self):
        if self.task_manager.undo():
            self.refresh_task_list()
            QMessageBox.information(self, "Success", "Undo successful!")
        else:
            QMessageBox.information(self, "Info", "Nothing to undo!")
            
    def extract_email_tasks(self):
        """Extract tasks from email"""
        dialog = EmailConfigDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            config = dialog.get_config()
            
            if not config['email'] or not config['password']:
                QMessageBox.warning(self, "Error", "Please provide email and password!")
                return
            
            # Show progress
            progress = QMessageBox(self)
            progress.setWindowTitle("Processing")
            progress.setText("Connecting to email and extracting tasks...\nThis may take a moment.")
            progress.setStandardButtons(QMessageBox.NoButton)
            progress.show()
            
            # Process in a separate thread (simplified version)
            try:
                # Connect to email
                if self.email_extractor.connect_to_email(
                    config['email'], 
                    config['password'], 
                    config['imap_server']
                ):
                    # Extract tasks
                    email_tasks = self.email_extractor.extract_tasks_from_emails(
                        config['folder'], 
                        config['days_back']
                    )
                    
                    progress.close()
                    
                    if email_tasks:
                        # Show extracted tasks for user selection
                        self.show_extracted_tasks(email_tasks)
                    else:
                        QMessageBox.information(self, "No Tasks Found", 
                                              "No task-related emails found in the specified timeframe.")
                else:
                    progress.close()
                    QMessageBox.critical(self, "Connection Error", 
                                       "Failed to connect to email. Please check your credentials and try again.")
                
            except Exception as e:
                progress.close()
                QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
            finally:
                self.email_extractor.disconnect()
    
    def show_extracted_tasks(self, email_tasks):
        """Show extracted email tasks for user selection"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Tasks to Import")
        dialog.setFixedSize(600, 400)
        
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel("Select the tasks you want to import:")
        instructions.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(instructions)
        
        # Task list with checkboxes
        scroll_area = QScrollArea()
        task_widget = QWidget()
        task_layout = QVBoxLayout()
        
        checkboxes = []
        next_task_id = self.get_next_available_task_id()
        
        for i, task_data in enumerate(email_tasks):
            frame = QFrame()
            frame.setFrameStyle(QFrame.Box)
            frame.setStyleSheet("QFrame { border: 1px solid #ddd; border-radius: 5px; margin: 2px; padding: 5px; }")
            
            frame_layout = QVBoxLayout()
            
            # Checkbox with task title
            checkbox = QCheckBox(f"Task #{next_task_id + i}: {task_data['title']}")
            checkbox.setChecked(True)  # Default to checked
            checkbox.setFont(QFont("Arial", 10, QFont.Bold))
            
            # Additional info
            info_label = QLabel(f"Priority: {task_data['priority']} | Source: {task_data['source']}")
            info_label.setStyleSheet("color: #666; font-size: 9px;")
            
            frame_layout.addWidget(checkbox)
            frame_layout.addWidget(info_label)
            frame.setLayout(frame_layout)
            
            task_layout.addWidget(frame)
            checkboxes.append((checkbox, task_data, next_task_id + i))
        
        task_widget.setLayout(task_layout)
        scroll_area.setWidget(task_widget)
        scroll_area.setWidgetResizable(True)
        
        layout.addWidget(scroll_area)
        
        # Buttons
        button_layout = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        deselect_all_btn = QPushButton("Deselect All")
        import_btn = QPushButton("Import Selected")
        cancel_btn = QPushButton("Cancel")
        
        select_all_btn.clicked.connect(lambda: self.toggle_all_checkboxes(checkboxes, True))
        deselect_all_btn.clicked.connect(lambda: self.toggle_all_checkboxes(checkboxes, False))
        import_btn.clicked.connect(lambda: self.import_selected_tasks(dialog, checkboxes))
        cancel_btn.clicked.connect(dialog.reject)
        
        button_layout.addWidget(select_all_btn)
        button_layout.addWidget(deselect_all_btn)
        button_layout.addStretch()
        button_layout.addWidget(import_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        
        # Styling
        dialog.setStyleSheet("""
            QDialog { background-color: #f8f9fa; }
            QPushButton { 
                padding: 8px 16px; 
                border-radius: 6px; 
                font-weight: bold;
                background-color: #4a90e2;
                color: white;
                border: none;
            }
            QPushButton:hover { background-color: #357abd; }
        """)
        
        dialog.exec_()
    
    def get_next_available_task_id(self):
        """Get the next available numeric task ID"""
        if not self.task_manager.tasks:
            return 1
        
        # Convert existing task IDs to integers and find the maximum
        existing_ids = []
        for task_id in self.task_manager.tasks.keys():
            try:
                existing_ids.append(int(task_id))
            except ValueError:
                continue
        
        return max(existing_ids) + 1 if existing_ids else 1
    
    def toggle_all_checkboxes(self, checkboxes, checked):
        """Toggle all checkboxes"""
        for checkbox, _, _ in checkboxes:
            checkbox.setChecked(checked)
    
    def import_selected_tasks(self, dialog, checkboxes):
        """Import selected tasks"""
        imported_count = 0
        
        for checkbox, task_data, task_id in checkboxes:
            if checkbox.isChecked():
                success = self.task_manager.add_task(
                    str(task_id), 
                    task_data['title'], 
                    task_data['priority']
                )
                if success:
                    imported_count += 1
        
        dialog.accept()
        
        if imported_count > 0:
            self.refresh_task_list()
            QMessageBox.information(self, "Success", f"Successfully imported {imported_count} tasks from email!")
        else:
            QMessageBox.information(self, "No Tasks Imported", "No tasks were selected for import.")
    
    def show_stats(self):
        stats = self.task_manager.get_stats()
        QMessageBox.information(self, "Task Statistics", 
                              f"Total Tasks: {stats['total']}\n"
                              f"Completed: {stats['completed']}\n"
                              f"Pending: {stats['pending']}")

def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = TaskManagerUI()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
