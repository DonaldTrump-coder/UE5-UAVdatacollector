from UI.Application import Datacollection
import sys
from PyQt6.QtWidgets import QApplication

UE_url = "http://127.0.0.1:80"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Datacollection(UE_url)
    window.show()
    sys.exit(app.exec())