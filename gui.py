# gui.py (изменённый)
import tkinter as tk
from tkinter import ttk, messagebox

class GUI:
    def __init__(self, root, core):
        self.root = root
        self.core = core 
        self.current_student_id = None 
        self.questions = []
        self.saved_answers = {}  # {q_id: set(selected_options)}
        self.current_q_idx = 0

        self.root.title("Приложение для тестирования студентов")
        self.root.geometry("800x600") 
        self.root.resizable(True, True)

        self.build_login_screen()

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def build_login_screen(self):
        self.clear_window()
        
        main_frame = tk.Frame(self.root, padx=30, pady=30)
        main_frame.pack(fill="both", expand=True)

        title_label = tk.Label(main_frame, text="Добро пожаловать!", font=("Arial", 20, "bold"), fg="#2c3e50")
        title_label.pack(pady=(0, 30))

        role_frame = tk.LabelFrame(main_frame, text="Выберите роль", padx=20, pady=10, font=("Arial", 12))
        role_frame.pack(fill="x", pady=(0, 20))

        self.role_var = tk.StringVar(value="student")

        tk.Radiobutton(role_frame, text="👨‍🎓 Студент", variable=self.role_var, value="student", font=("Arial", 11), command=self.on_role_change).pack(side="left", padx=(0, 20))
        tk.Radiobutton(role_frame, text="👨‍🏫 Преподаватель", variable=self.role_var, value="teacher", font=("Arial", 11), command=self.on_role_change).pack(side="left")

        self.dynamic_frame = tk.Frame(main_frame)
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

        tk.Label(self.dynamic_frame, text="Группа:", font=("Arial", 10)).pack(anchor="w")
        self.group_entry = tk.Entry(self.dynamic_frame, font=("Arial", 11))
        self.group_entry.pack(fill="x", pady=(0, 15))
    
        tk.Button(self.dynamic_frame, text="Войти", font=("Arial", 12, "bold"), bg="#3498db", fg="white", activebackground="#2980b9", cursor="hand2", command=self.student_login).pack(pady=(10, 0))

    def create_teacher_fields(self):
        tk.Button(self.dynamic_frame, text="Войти как преподаватель", font=("Arial", 12, "bold"), bg="#e67e22", fg="white", activebackground="#d35400", cursor="hand2", command=self.teacher_login).pack(pady=10)

    # --- ЛОГИКА СТУДЕНТА ---

    def student_login(self):
        name = self.name_entry.get().strip()
        group = self.group_entry.get().strip()

        if not name or not group:
            messagebox.showwarning("Внимание", "Пожалуйста, заполните ФИО и группу.")
            return

        self.current_student_id = self.core.create_student(name, group)
        self.show_test_intro()

    def show_test_intro(self):
        self.clear_window()
        frame = tk.Frame(self.root)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(frame, text="Итоговое тестирование", font=("Arial", 24, "bold")).pack(pady=10)
        tk.Label(frame, text="243 вопроса, множественный и единичный выбор", font=("Arial", 14), fg="gray").pack(pady=20)
        tk.Button(frame, text="Начать", font=("Arial", 16, "bold"), bg="#2ecc71", fg="white", padx=30, pady=10, command=self.init_test).pack(pady=20)

    def init_test(self):
        self.questions = self.core.get_questions()
        if not self.questions:
            messagebox.showerror("Ошибка", "Не удалось загрузить вопросы из базы данных.")
            return

        self.current_q_idx = 0
        self.saved_answers = {}
        self.build_test_interface()
        self.render_current_question()

    def build_test_interface(self):
        self.clear_window()
        
        self.test_frame = tk.Frame(self.root, padx=30, pady=30)
        self.test_frame.pack(fill="both", expand=True)

        self.lbl_counter = tk.Label(self.test_frame, font=("Arial", 12, "italic"), fg="#7f8c8d")
        self.lbl_counter.pack(anchor="w", pady=(0, 10))

        self.lbl_question = tk.Label(self.test_frame, font=("Arial", 14, "bold"), wraplength=700, justify="left")
        self.lbl_question.pack(anchor="w", pady=(0, 20))

        self.options_frame = tk.Frame(self.test_frame)
        self.options_frame.pack(fill="both", expand=True)

        # Фрейм для кнопок навигации
        self.nav_frame = tk.Frame(self.test_frame, pady=20)
        self.nav_frame.pack(fill="x", side="bottom")

        # Только кнопки «Далее» и «Завершить тест» (кнопка «Назад» удалена)
        self.btn_next = tk.Button(self.nav_frame, text="Далее ►", font=("Arial", 12), width=10, bg="#3498db", fg="white", command=self.go_next)
        self.btn_finish = tk.Button(self.nav_frame, text="Завершить тест", font=("Arial", 12, "bold"), bg="#e74c3c", fg="white", command=self.finish_test)

    def save_current_answers(self):
        """Сохраняет выбранные ответы текущего вопроса"""
        q = self.questions[self.current_q_idx]
        q_id = q['id']
        is_multiple = len(q.get('correct', [])) > 1
        
        selected = set()
        if is_multiple:
            for opt_idx, var in self.current_vars:
                if var.get():
                    selected.add(opt_idx)
        else:
            val = self.current_var.get()
            if val != -1:
                selected.add(val)
        
        self.saved_answers[q_id] = selected

    def render_current_question(self):
        """Отрисовывает вопрос и варианты ответа"""
        q = self.questions[self.current_q_idx]
        
        self.lbl_counter.config(text=f"Вопрос {self.current_q_idx + 1} из {len(self.questions)}")
        self.lbl_question.config(text=q['text'])

        for widget in self.options_frame.winfo_children():
            widget.destroy()

        correct_answers = q.get('correct', [])
        is_multiple = len(correct_answers) > 1
        q_id = q['id']
        
        previously_selected = self.saved_answers.get(q_id, set())

        if is_multiple:
            self.current_vars = []
            for opt_idx, opt_text in enumerate(q['options']):
                var = tk.BooleanVar(value=(opt_idx in previously_selected))
                chk = tk.Checkbutton(self.options_frame, text=opt_text, variable=var, font=("Arial", 12), wraplength=700, justify="left")
                chk.pack(anchor="w", pady=5)
                self.current_vars.append((opt_idx, var))
        else:
            default_val = list(previously_selected)[0] if previously_selected else -1
            self.current_var = tk.IntVar(value=default_val)
            for opt_idx, opt_text in enumerate(q['options']):
                rad = tk.Radiobutton(self.options_frame, text=opt_text, variable=self.current_var, value=opt_idx, font=("Arial", 12), wraplength=700, justify="left")
                rad.pack(anchor="w", pady=5)

        # Управляем кнопками: всегда показываем «Завершить тест», «Далее» – только если не последний вопрос
        self.btn_next.pack_forget()
        self.btn_finish.pack_forget()

        self.btn_finish.pack(side="left")  # досрочное завершение всегда доступно

        if self.current_q_idx < len(self.questions) - 1:
            self.btn_next.pack(side="right")

    def go_next(self):
        self.save_current_answers()
        self.current_q_idx += 1
        self.render_current_question()

    # Метод go_prev больше не используется, можно удалить

    def finish_test(self):
        self.save_current_answers()  # сохраняем ответ на текущий вопрос
        
        correct_count = 0
        total_count = len(self.questions)

        for q in self.questions:
            q_id = q['id']
            correct_answers = set(q.get('correct', []))
            user_selected = self.saved_answers.get(q_id, set())

            # Для множественного выбора ответы должны полностью совпадать
            if user_selected == correct_answers:
                correct_count += 1

        percentage = round((correct_count / total_count) * 100)
        grade = round(percentage / 10) 

        self.core.save_result(self.current_student_id, correct_count, total_count, percentage, grade)
        self.show_results_screen(correct_count, total_count, percentage, grade)

    def show_results_screen(self, correct_count, total_count, percentage, grade):
        self.clear_window()
        frame = tk.Frame(self.root)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(frame, text=f"Правильных вопросов {correct_count} из {total_count}", font=("Arial", 16)).pack(pady=10)
        tk.Label(frame, text=f"Ваш результат: {percentage}%", font=("Arial", 20, "bold")).pack(pady=10)
        tk.Label(frame, text=f"Ваша оценка: {grade}", font=("Arial", 24, "bold"), fg="#27ae60").pack(pady=20)
        tk.Button(frame, text="Завершить", font=("Arial", 14), bg="#95a5a6", fg="white", padx=20, command=self.root.destroy).pack(pady=30)

    # --- ЛОГИКА ПРЕПОДАВАТЕЛЯ (без изменений) ---

    def teacher_login(self):
        self.clear_window()
        frame = tk.Frame(self.root)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        tk.Button(frame, text="Выгрузить ответы студентов", font=("Arial", 14, "bold"), bg="#8e44ad", fg="white", padx=20, pady=10, command=self.show_teacher_dashboard).pack()

    def show_teacher_dashboard(self):
        self.clear_window()
        
        tk.Label(self.root, text="Результаты тестирования", font=("Arial", 18, "bold")).pack(pady=20)

        columns = ("name", "group", "result")
        tree = ttk.Treeview(self.root, columns=columns, show="headings", height=20)
        tree.heading("name", text="ФИО")
        tree.heading("group", text="Группа")
        tree.heading("result", text="Результат")
        
        tree.column("name", width=300)
        tree.column("group", width=150)
        tree.column("result", width=150, anchor="center")
        
        tree.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        scrollbar = ttk.Scrollbar(tree, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        students = self.core.get_all_students()
        
        for s_id, s_data in students.items():
            name = s_data.get('name', 'Информация отсутствует')
            group = s_data.get('group', 'Информация отсутствует')

            if s_data.get('status') == 'completed':
                percent = s_data.get('percentage', 0)
                grade = s_data.get('grade', 0)
                res_text = f"{percent}% (Балл: {grade})"
            else:
                res_text = "Тест в процессе"

            tree.insert("", "end", values=(name, group, res_text))