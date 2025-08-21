from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel
import sys

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("测试GUI")
        self.setGeometry(100, 100, 300, 200)
        # 添加一个标签
        label = QLabel("GUI能正常运行！", self)
        label.move(50, 80)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())