import tkinter as tk


class GUI:
    def __init__(self, root):
        self.root = root

        root.title("Приложение для тестирования студентов")
        root.geometry("600x600")
        root.resizable(False, False)

        self.main_frame = tk.Frame(root, padx=30, pady=30)
        self.main_frame.pack(fill="both", expand=True)

        # Заголовок
        title_label = tk.Label(
            self.main_frame,
            text="Добро пожаловать!",
            font=("Arial", 20, "bold"),
            fg="#2c3e50",
        )
        title_label.pack(pady=(0, 30))

        role_frame = tk.LabelFrame(
            self.main_frame, text="Выберите роль", padx=20, pady=10, font=("Arial", 12)
        )
        role_frame.pack(fill="x", pady=(0, 20))

        self.role_var = tk.StringVar(value="student")

        self.student_radio = tk.Radiobutton(
            role_frame,
            text="👨‍🎓 Студент",
            variable=self.role_var,
            value="student",
            font=("Arial", 11),
            command=self.on_role_change,
        )
        self.student_radio.pack(side="left", padx=(0, 20))

        self.teacher_radio = tk.Radiobutton(
            role_frame,
            text="👨‍🏫 Преподаватель",
            variable=self.role_var,
            value="teacher",
            font=("Arial", 11),
            command=self.on_role_change,
        )
        self.teacher_radio.pack(side="left")

        self.dynamic_frame = tk.Frame(self.main_frame)
        self.dynamic_frame.pack(fill="x", pady=20)

        self.create_student_fields()

    def on_role_change(self):
        for widget in self.dynamic_frame.winfo_children():
            widget.destroy()

        if self.role_var.get() == "student":
            self.create_student_fields()
        else:
            self.create_teacher_fields()

        
    def create_student_fields(self):
        tk.Label(self.dynamic_frame, text="ФИО:", font=("Arial", 10)).pack(anchor="w")
        self.name_entry = tk.Entry(self.dynamic_frame, font=("Arial", 11))
        self.name_entry.pack(fill="x", pady=(0, 15))

        # Группа (видна для студента)
        tk.Label(self.dynamic_frame, text="Группа:", font=("Arial", 10)).pack(anchor="w")
        self.group_entry = tk.Entry(self.dynamic_frame, font=("Arial", 11))
        self.group_entry.pack(fill="x", pady=(0, 15))
    
        # Кнопка входа
        self.login_button = tk.Button(
            self.dynamic_frame,
            text="Войти",
            font=("Arial", 12, "bold"),
            bg="#3498db",
            fg="white",
            activebackground="#2980b9",
            cursor="hand2",
            command=self.student_login
        )
        self.login_button.pack(pady=(10, 0))

    def student_login(self):
        pass

    def create_teacher_fields(self):
        self.teacher_login_button = tk.Button(
            self.dynamic_frame,
            text="Войти как преподаватель",
            font=("Arial", 12, "bold"),
            bg="#e67e22",
            fg="white",
            activebackground="#d35400",
            cursor="hand2",
            command=self.teacher_login
        )
        self.teacher_login_button.pack(pady=10)

    def teacher_login(self):
        pass
