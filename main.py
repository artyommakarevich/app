import tkinter as tk
from core import Core
from gui import GUI


def main():
    core = Core()

    root = tk.Tk()
    app = GUI(root, core)

    root.mainloop()


if __name__ == "__main__":
    main()
