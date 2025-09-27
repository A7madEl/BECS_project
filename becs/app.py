import sys, argparse
from PyQt6 import QtWidgets
from .ui import LoginWindow, MainWindow

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="becs.db")
    args = ap.parse_args()

    app = QtWidgets.QApplication(sys.argv)
    login = LoginWindow(args.db)
    mainw = {"win": None}

    def on_authed(username: str , role: str):
        w = MainWindow(args.db, username, role)
        mainw["win"] = w
        w.show()
        login.close()

    login.authed.connect(on_authed)
    login.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
