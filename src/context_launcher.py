# Chrome Session Launcher - Simple UI
# Save as: chrome_launcher.py

import sys
import json
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QListWidget,
                             QDialog, QLineEdit, QComboBox, QMessageBox, 
                             QFileDialog, QGroupBox, QListWidgetItem)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options


class ChromeLauncher:
    def __init__(self, chrome_profile_path=None, chromedriver_path=None):
        self.chrome_profile_path = chrome_profile_path
        self.chromedriver_path = chromedriver_path
    
    def launch_session(self, session):
        """Launch Chrome with the specified session tabs"""
        chrome_options = Options()
        
        if self.chrome_profile_path:
            chrome_options.add_argument(f"user-data-dir={self.chrome_profile_path}")
        
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(self.chromedriver_path) if self.chromedriver_path else None
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        for i, tab in enumerate(session['tabs']):
            if tab['type'] == 'url':
                if i == 0:
                    driver.get(tab['url'])
                else:
                    driver.execute_script(f"window.open('{tab['url']}', '_blank');")
                    driver.switch_to.window(driver.window_handles[-1])
            
            elif tab['type'] == 'youtube':
                self._switch_youtube_channel(driver, tab['channelHandle'], is_first=(i == 0))
        
        return driver
    
    def _switch_youtube_channel(self, driver, channel_handle, is_first=False):
        """Switch to a specific YouTube channel"""
        try:
            if is_first:
                driver.get("https://www.youtube.com")
            else:
                driver.execute_script("window.open('https://www.youtube.com', '_blank');")
                driver.switch_to.window(driver.window_handles[-1])
            
            time.sleep(2)
            
            wait = WebDriverWait(driver, 10)
            profile_button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button#avatar-btn"))
            )
            profile_button.click()
            
            time.sleep(1)
            
            try:
                channel_items = driver.find_elements(By.CSS_SELECTOR, "ytd-compact-link-renderer")
                for item in channel_items:
                    if channel_handle in item.text:
                        item.click()
                        time.sleep(2)
                        break
            except Exception as e:
                print(f"Could not find channel in menu: {e}")
            
            driver.get(f"https://www.youtube.com/{channel_handle}")
            
        except Exception as e:
            print(f"Error switching to channel {channel_handle}: {e}")
            driver.get(f"https://www.youtube.com/{channel_handle}")


class LaunchWorker(QThread):
    finished = pyqtSignal(bool, str)
    
    def __init__(self, launcher, session):
        super().__init__()
        self.launcher = launcher
        self.session = session
    
    def run(self):
        try:
            self.launcher.launch_session(self.session)
            self.finished.emit(True, f"Session '{self.session['name']}' launched!")
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}")


class SessionDialog(QDialog):
    def __init__(self, parent=None, session=None):
        super().__init__(parent)
        self.session = session or {'name': '', 'icon': '🌐', 'tabs': []}
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Session Editor")
        self.setMinimumWidth(500)
        layout = QVBoxLayout()
        
        # Name
        layout.addWidget(QLabel("Session Name:"))
        self.name_input = QLineEdit(self.session['name'])
        layout.addWidget(self.name_input)
        
        # Icon
        layout.addWidget(QLabel("Icon:"))
        self.icon_input = QLineEdit(self.session['icon'])
        layout.addWidget(self.icon_input)
        
        # Tabs list
        layout.addWidget(QLabel("Tabs:"))
        self.tabs_list = QListWidget()
        for tab in self.session['tabs']:
            if tab['type'] == 'url':
                self.tabs_list.addItem(f"URL: {tab['url']}")
            else:
                self.tabs_list.addItem(f"YouTube: {tab['channelHandle']}")
        layout.addWidget(self.tabs_list)
        
        # Add tab
        add_group = QGroupBox("Add Tab")
        add_layout = QVBoxLayout()
        
        self.tab_type = QComboBox()
        self.tab_type.addItems(["URL", "YouTube Channel"])
        add_layout.addWidget(self.tab_type)
        
        self.tab_input = QLineEdit()
        self.tab_input.setPlaceholderText("Enter URL or @channel_handle")
        add_layout.addWidget(self.tab_input)
        
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_tab)
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self.remove_tab)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(remove_btn)
        add_layout.addLayout(btn_layout)
        
        add_group.setLayout(add_layout)
        layout.addWidget(add_group)
        
        # Save/Cancel
        buttons = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)
        
        self.setLayout(layout)
    
    def add_tab(self):
        tab_input = self.tab_input.text().strip()
        if not tab_input:
            return
        
        tab_type = "url" if self.tab_type.currentText() == "URL" else "youtube"
        
        if tab_type == "url":
            if not tab_input.startswith("http"):
                tab_input = "https://" + tab_input
            self.session['tabs'].append({'type': 'url', 'url': tab_input})
            self.tabs_list.addItem(f"URL: {tab_input}")
        else:
            if not tab_input.startswith("@"):
                tab_input = "@" + tab_input
            self.session['tabs'].append({'type': 'youtube', 'channelHandle': tab_input})
            self.tabs_list.addItem(f"YouTube: {tab_input}")
        
        self.tab_input.clear()
    
    def remove_tab(self):
        current_row = self.tabs_list.currentRow()
        if current_row >= 0:
            self.tabs_list.takeItem(current_row)
            del self.session['tabs'][current_row]
    
    def get_session(self):
        self.session['name'] = self.name_input.text()
        self.session['icon'] = self.icon_input.text()
        return self.session


class SettingsDialog(QDialog):
    def __init__(self, parent=None, chrome_path=None, chromedriver_path=None):
        super().__init__(parent)
        self.chrome_path = chrome_path
        self.chromedriver_path = chromedriver_path
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Chrome Profile Path:"))
        self.chrome_input = QLineEdit(self.chrome_path or "")
        layout.addWidget(self.chrome_input)
        
        chrome_btn = QPushButton("Browse...")
        chrome_btn.clicked.connect(self.browse_chrome)
        layout.addWidget(chrome_btn)
        
        layout.addWidget(QLabel("ChromeDriver Path:"))
        self.driver_input = QLineEdit(self.chromedriver_path or "")
        layout.addWidget(self.driver_input)
        
        driver_btn = QPushButton("Browse...")
        driver_btn.clicked.connect(self.browse_driver)
        layout.addWidget(driver_btn)
        
        buttons = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)
        
        self.setLayout(layout)
    
    def browse_chrome(self):
        path = QFileDialog.getExistingDirectory(self, "Select Chrome Profile Directory")
        if path:
            self.chrome_input.setText(path)
    
    def browse_driver(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select ChromeDriver")
        if path:
            self.driver_input.setText(path)
    
    def get_paths(self):
        return self.chrome_input.text(), self.driver_input.text()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.sessions = []
        self.chrome_profile_path = None
        self.chromedriver_path = None
        self.load_config()
        self.launcher = ChromeLauncher(self.chrome_profile_path, self.chromedriver_path)
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Chrome Session Launcher")
        self.setMinimumSize(600, 400)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Title
        title = QLabel("Chrome Session Launcher")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Sessions list
        layout.addWidget(QLabel("Sessions:"))
        self.sessions_list = QListWidget()
        self.sessions_list.itemDoubleClicked.connect(self.launch_selected)
        layout.addWidget(self.sessions_list)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        launch_btn = QPushButton("Launch")
        launch_btn.clicked.connect(self.launch_selected)
        btn_layout.addWidget(launch_btn)
        
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_session)
        btn_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self.edit_selected)
        btn_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self.delete_selected)
        btn_layout.addWidget(delete_btn)
        
        settings_btn = QPushButton("Settings")
        settings_btn.clicked.connect(self.show_settings)
        btn_layout.addWidget(settings_btn)
        
        layout.addLayout(btn_layout)
        
        self.refresh_list()
    
    def refresh_list(self):
        self.sessions_list.clear()
        for session in self.sessions:
            item = QListWidgetItem(f"{session['icon']} {session['name']} ({len(session['tabs'])} tabs)")
            item.setData(Qt.ItemDataRole.UserRole, session)
            self.sessions_list.addItem(item)
    
    def launch_selected(self):
        current = self.sessions_list.currentItem()
        if not current:
            QMessageBox.warning(self, "No Selection", "Please select a session to launch.")
            return
        
        session = current.data(Qt.ItemDataRole.UserRole)
        self.worker = LaunchWorker(self.launcher, session)
        self.worker.finished.connect(self.on_launch_finished)
        self.worker.start()
        QMessageBox.information(self, "Launching", f"Launching '{session['name']}'...")
    
    def on_launch_finished(self, success, message):
        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.critical(self, "Error", message)
    
    def add_session(self):
        dialog = SessionDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_session = dialog.get_session()
            if not new_session['name']:
                QMessageBox.warning(self, "Error", "Session name cannot be empty.")
                return
            new_session['id'] = max([s['id'] for s in self.sessions], default=0) + 1
            self.sessions.append(new_session)
            self.refresh_list()
            self.save_config()
    
    def edit_selected(self):
        current = self.sessions_list.currentItem()
        if not current:
            QMessageBox.warning(self, "No Selection", "Please select a session to edit.")
            return
        
        session = current.data(Qt.ItemDataRole.UserRole)
        dialog = SessionDialog(self, session.copy())
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated = dialog.get_session()
            for i, s in enumerate(self.sessions):
                if s['id'] == session['id']:
                    self.sessions[i] = updated
                    break
            self.refresh_list()
            self.save_config()
    
    def delete_selected(self):
        current = self.sessions_list.currentItem()
        if not current:
            QMessageBox.warning(self, "No Selection", "Please select a session to delete.")
            return
        
        session = current.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(
            self, "Confirm Delete", 
            f"Delete '{session['name']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.sessions = [s for s in self.sessions if s['id'] != session['id']]
            self.refresh_list()
            self.save_config()
    
    def show_settings(self):
        dialog = SettingsDialog(self, self.chrome_profile_path, self.chromedriver_path)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            chrome, driver = dialog.get_paths()
            self.chrome_profile_path = chrome if chrome else None
            self.chromedriver_path = driver if driver else None
            self.launcher = ChromeLauncher(self.chrome_profile_path, self.chromedriver_path)
            self.save_config()
    
    def save_config(self):
        config = {
            'chrome_profile_path': self.chrome_profile_path,
            'chromedriver_path': self.chromedriver_path,
            'sessions': self.sessions
        }
        try:
            with open('config.json', 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            QMessageBox.warning(self, "Save Error", f"Could not save: {e}")
    
    def load_config(self):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                self.chrome_profile_path = config.get('chrome_profile_path')
                self.chromedriver_path = config.get('chromedriver_path')
                self.sessions = config.get('sessions', [])
        except FileNotFoundError:
            self.load_default_sessions()
    
    def load_default_sessions(self):
        try:
            with open('sessions.json', 'r') as f:
                self.sessions = json.load(f)
        except FileNotFoundError:
            self.sessions = [
                {
                    "id": 1,
                    "name": "Entertainment",
                    "icon": "🎬",
                    "tabs": [
                        {"url": "https://netflix.com", "type": "url"},
                        {"url": "https://primevideo.com", "type": "url"},
                        {"url": "https://mubi.com", "type": "url"}
                    ]
                },
                {
                    "id": 2,
                    "name": "FraH Production",
                    "icon": "🎥",
                    "tabs": [
                        {"channelHandle": "@frah_production7608", "type": "youtube"}
                    ]
                },
                {
                    "id": 3,
                    "name": "FraH Music",
                    "icon": "🎵",
                    "tabs": [
                        {"channelHandle": "@FraH_Music-m9m", "type": "youtube"}
                    ]
                },
                {
                    "id": 4,
                    "name": "FraH Educational",
                    "icon": "📚",
                    "tabs": [
                        {"channelHandle": "@frah_educational9926", "type": "youtube"}
                    ]
                }
            ]


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())