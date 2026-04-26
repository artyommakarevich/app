import tkinter as tk
from core import Core
from gui import GUI

def main():
    # Инициализируем логику работы с БД
    core = Core()
    
    # Инициализируем UI и передаем ему объект core
    root = tk.Tk()
    app = GUI(root, core)
    
    root.mainloop()

if __name__ == "__main__":
    main()