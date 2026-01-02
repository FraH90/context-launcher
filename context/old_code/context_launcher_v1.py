import sys
import json
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QMessageBox

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'sessions.json')
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

class ContextLauncher(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Context Launcher')
        self.layout = QVBoxLayout()
        self.sessions = self.load_sessions()
        self.create_buttons()
        self.setLayout(self.layout)

    def load_sessions(self):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('sessions', [])
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to load config: {e}')
            return []

    def create_buttons(self):
        for session in self.sessions:
            btn = QPushButton(session['name'])
            btn.clicked.connect(lambda checked, s=session: self.launch_session(s))
            self.layout.addWidget(btn)

    def launch_session(self, session):
        import subprocess
        profile = session.get('profile', 'Default')
        tabs = session.get('tabs', [])
        if not tabs:
            QMessageBox.warning(self, 'Warning', 'No tabs defined for this session.')
            return
        args = [CHROME_PATH, f'--profile-directory={profile}', '--new-window'] + tabs
        try:
            subprocess.Popen(args)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to launch Chrome: {e}')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    launcher = ContextLauncher()
    launcher.show()
    sys.exit(app.exec_())
