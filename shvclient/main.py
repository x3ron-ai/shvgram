import os
import sys
import json
from shvclient import get_config
from shvclient import Client
from PyQt6.QtCore import QThread, pyqtSignal, QSize, Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget

class ListenerThread(QThread):
    message_received = pyqtSignal(dict)

    def __init__(self, client):
        super().__init__()
        self.client = client
        self.running = True

    def run(self):
        try:
            while self.running:
                event = self.client.receive()
                if event:
                    self.message_received.emit(event)
        except KeyboardInterrupt:
            self.running = False
            print("\nListener thread stopped.")

class MainWindow(QMainWindow):
    def __init__(self, client):
        super().__init__()
        self.setWindowTitle("eperesete")
        self.setMinimumSize(QSize(400, 300))

        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)

        layout = QVBoxLayout()
        layout.addWidget(self.text_area)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.listener_thread = ListenerThread(client)
        self.listener_thread.message_received.connect(self.display_message)
        self.listener_thread.start()

    def display_message(self, event):
        if event.get("@extra") or event["@type"] == "updateNewMessage":
            message_text = json.dumps(event, indent=2, ensure_ascii=False)
            self.text_area.append(message_text + "\n" + "-"*50)

    def closeEvent(self, event):
        self.listener_thread.running = False
        self.listener_thread.quit()
        self.listener_thread.wait()
        event.accept()

def main():
    config = get_config()
    client = Client(config['API_ID'], config['API_HASH'])

    client.login()

    print("Запуск слушателя событий в отдельном потоке...")

    app = QApplication(sys.argv)
    window = MainWindow(client)
    window.show()

    client.get_chats(1)

    app.exec()

if __name__ == "__main__":
    main()