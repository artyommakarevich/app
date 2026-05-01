import tkinter as tk
import threading
import random
from tkinter import ttk, messagebox


C_BG      = "#f5f6fa"
C_PRIMARY = "#3498db"
C_SUCCESS = "#2ecc71"
C_DANGER  = "#e74c3c"
C_WARNING = "#e67e22"
C_DARK    = "#2c3e50"
C_GRAY    = "#7f8c8d"
C_LIGHT   = "#ecf0f1"
C_PURPLE  = "#8e44ad"
C_WHITE   = "#ffffff"

TEACHER_LOGIN    = "teacher"
TEACHER_PASSWORD = "teacher"


class GUI:
    def __init__(self, root: tk.Tk, core) -> None:
        self.root = root
        self.core = core

        self.current_student_id: str | None = None
        self.all_questions: list = []
        self.test_settings: dict = {}          # {test_id: {num_questions, open_results}}

        self.current_test: dict | None = None
        self._current_open_results: bool = False   # open_results для текущего теста

        self.test_questions: list = []         # список вопросов текущего теста
        self.saved_answers: dict = {}          # {q_id: set(selected_option_indices)}
        self.current_q_idx: int = 0

        self.current_var: tk.IntVar | None = None
        self.current_vars: list = []

        self.root.title("Приложение для тестирования студентов")
        self.root.geometry("920x700")
        self.root.resizable(True, True)
        self.root.configure(bg=C_BG)

        self._build_login_screen()

    # ── Утилиты ──────────────────────────────────────────────────────────────

    def _clear(self) -> None:
        for w in self.root.winfo_children():
            w.destroy()

    def _btn(self, parent, text, command, bg=C_PRIMARY, fg=C_WHITE,
             font_size=12, bold=False, padx=15, pady=6, **kw) -> tk.Button:
        weight = "bold" if bold else "normal"
        return tk.Button(
            parent, text=text, command=command,
            font=("Arial", font_size, weight),
            bg=bg, fg=fg, activebackground=bg,
            padx=padx, pady=pady, cursor="hand2", relief="flat", **kw
        )

    def _label(self, parent, text, size=12, bold=False, fg=C_DARK, **kw) -> tk.Label:
        weight = "bold" if bold else "normal"
        return tk.Label(
            parent, text=text, font=("Arial", size, weight),
            fg=fg, bg=parent.cget("bg"), **kw
        )

    def _set_loading(self, loading: bool,
                     status_label: tk.Label | None = None,
                     buttons: list | None = None,
                     message: str = "Подождите...") -> None:
        if status_label:
            status_label.config(text=message if loading else "", fg=C_WARNING)
        if buttons:
            state = "disabled" if loading else "normal"
            for btn in buttons:
                btn.config(state=state)

    # Экран входа

    def _build_login_screen(self) -> None:
        self._clear()
        outer = tk.Frame(self.root, bg=C_BG, padx=50, pady=40)
        outer.pack(fill="both", expand=True)

        self._label(outer, "Добро пожаловать!", size=22, bold=True).pack(pady=(0, 30))

        role_frame = tk.LabelFrame(
            outer, text="Выберите роль", font=("Arial", 11), bg=C_BG, padx=20, pady=12
        )
        role_frame.pack(fill="x", pady=(0, 20))

        self._role_var = tk.StringVar(value="student")
        for text, value in [("👨‍🎓  Студент", "student"), ("👨‍🏫  Преподаватель", "teacher")]:
            tk.Radiobutton(
                role_frame, text=text, variable=self._role_var, value=value,
                font=("Arial", 11), bg=C_BG, command=self._on_role_change
            ).pack(side="left", padx=(0, 25))

        self._dyn = tk.Frame(outer, bg=C_BG)
        self._dyn.pack(fill="x")
        self._create_student_fields()

    def _on_role_change(self) -> None:
        for w in self._dyn.winfo_children():
            w.destroy()
        if self._role_var.get() == "student":
            self._create_student_fields()
        else:
            self._create_teacher_fields()

    def _create_student_fields(self) -> None:
        for label_text, attr in [("ФИО:", "_name_entry"), ("Группа:", "_group_entry")]:
            tk.Label(self._dyn, text=label_text, font=("Arial", 10), bg=C_BG).pack(anchor="w")
            entry = tk.Entry(self._dyn, font=("Arial", 11))
            entry.pack(fill="x", pady=(0, 12))
            setattr(self, attr, entry)
        self._student_login_btn = self._btn(self._dyn, "Войти", self._student_login, bold=True)
        self._student_login_btn.pack(pady=10)
        self._student_status_lbl = tk.Label(
            self._dyn, text="", font=("Arial", 10, "italic"), bg=C_BG
        )
        self._student_status_lbl.pack()

    def _create_teacher_fields(self) -> None:
        for label_text, attr, show_char in [
            ("Логин:", "_teacher_login_entry", ""),
            ("Пароль:", "_teacher_pass_entry", "*"),
        ]:
            tk.Label(self._dyn, text=label_text, font=("Arial", 10), bg=C_BG).pack(anchor="w")
            entry = tk.Entry(self._dyn, font=("Arial", 11), show=show_char)
            entry.pack(fill="x", pady=(0, 12))
            setattr(self, attr, entry)
        self._teacher_login_btn = self._btn(
            self._dyn, "Войти как преподаватель",
            self._teacher_login, bg=C_WARNING, bold=True
        )
        self._teacher_login_btn.pack(pady=10)
        self._teacher_status_lbl = tk.Label(
            self._dyn, text="", font=("Arial", 10, "italic"), bg=C_BG
        )
        self._teacher_status_lbl.pack()

    # Сценарий студента: вход

    def _student_login(self) -> None:
        name  = self._name_entry.get().strip()
        group = self._group_entry.get().strip()
        if not name or not group:
            messagebox.showwarning("Внимание", "Заполните ФИО и группу.")
            return
        self._set_loading(
            True, self._student_status_lbl,
            [self._student_login_btn], "⏳ Подключение..."
        )
        threading.Thread(
            target=self._student_login_thread, args=(name, group), daemon=True
        ).start()

    def _student_login_thread(self, name, group):
        try:
            sid      = self.core.create_student(name, group)
            qs       = self.core.get_questions()
            settings = self.core.get_test_settings()   # загружаем настройки из Firebase
            self.root.after(0, lambda: self._student_login_success(sid, qs, settings))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Ошибка", str(e)))

    def _student_login_success(self, sid, qs, settings):
        self._set_loading(False, self._student_status_lbl, [self._student_login_btn])
        self.current_student_id = sid
        self.all_questions      = qs
        self.test_settings      = settings
        self._show_test_list()

    # Список тестов 

    def _show_test_list(self) -> None:
        self._clear()

        header = tk.Frame(self.root, bg=C_DARK, pady=15)
        header.pack(fill="x")
        tk.Label(
            header, text="Доступные варианты тестов",
            font=("Arial", 16, "bold"), bg=C_DARK, fg=C_WHITE
        ).pack()

        container = tk.Frame(self.root, bg=C_BG)
        container.pack(fill="both", expand=True, padx=20, pady=10)

        canvas    = tk.Canvas(container, bg=C_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=C_BG)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=860)
        canvas.configure(yscrollcommand=scrollbar.set)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for test in self.core.get_tests():
            q_start  = test["q_start"]
            q_end    = min(test["q_end"], len(self.all_questions))
            pool_sz  = max(0, q_end - q_start)

            # Берём актуальное кол-во вопросов из настроек
            ts       = self.test_settings.get(test["id"], {})
            num_q    = min(ts.get("num_questions", pool_sz), pool_sz)
            open_res = ts.get("open_results", test["open_results"])

            open_icon = "🔓 Открытый" if open_res else "🔒 Закрытый"

            card = tk.Frame(
                scrollable_frame, bg=C_WHITE, padx=20, pady=15, relief="solid", bd=1
            )
            card.pack(fill="x", pady=8, padx=10)

            info_f = tk.Frame(card, bg=C_WHITE)
            info_f.pack(side="left", fill="both", expand=True)

            tk.Label(
                info_f, text=test["name"],
                font=("Arial", 14, "bold"), bg=C_WHITE, fg=C_DARK
            ).pack(anchor="w")
            tk.Label(
                info_f,
                text=f"Вопросов: {num_q}  |  Тип: {open_icon}",
                font=("Arial", 10), bg=C_WHITE, fg=C_GRAY
            ).pack(anchor="w", pady=(5, 0))

            self._btn(
                card, "Начать тест →",
                lambda t=test: self._start_test(t),
                bg=C_SUCCESS, bold=True
            ).pack(side="right")

    # Процесс теста 

    def _start_test(self, test: dict) -> None:
        self.root.unbind_all("<MouseWheel>")

        q_start = test["q_start"]
        q_end   = min(test["q_end"], len(self.all_questions))
        pool    = self.all_questions[q_start:q_end]

        # Кол-во вопросов из настроек
        ts    = self.test_settings.get(test["id"], {})
        num_q = ts.get("num_questions", len(pool))
        num_q = max(1, min(num_q, len(pool)))

        # Рандомная выборка num_q вопросов из пула 
        self.test_questions = random.sample(pool, num_q)

        # Сохраняем настройку open_results для этого конкретного прохождения
        self._current_open_results = ts.get("open_results", test["open_results"])

        self.current_test   = test
        self.current_q_idx  = 0
        self.saved_answers  = {}
        self._build_test_ui()
        self._render_question()

    def _build_test_ui(self) -> None:
        self._clear()
        header = tk.Frame(self.root, bg=C_DARK, pady=10)
        header.pack(fill="x")
        tk.Label(
            header, text=self.current_test["name"],
            font=("Arial", 12, "bold"), bg=C_DARK, fg=C_WHITE
        ).pack()

        self._lbl_counter = tk.Label(
            self.root, font=("Arial", 10, "italic"), fg=C_GRAY, bg=C_BG
        )
        self._lbl_counter.pack(anchor="w", padx=30, pady=(15, 0))

        self._lbl_question = tk.Label(
            self.root, font=("Arial", 13, "bold"),
            wraplength=840, justify="left", bg=C_BG, fg=C_DARK
        )
        self._lbl_question.pack(anchor="w", padx=30, pady=(10, 20))

        self._opts_frame = tk.Frame(self.root, bg=C_BG)
        self._opts_frame.pack(fill="both", expand=True, padx=35)

        nav = tk.Frame(self.root, bg=C_LIGHT, pady=15)
        nav.pack(fill="x", side="bottom")

        self._btn_finish = self._btn(
            nav, "Завершить", self._finish_test, bg=C_DANGER, bold=True
        )
        self._btn_finish.pack(side="left", padx=25)
        self._finish_status_lbl = tk.Label(nav, text="", font=("Arial", 10), bg=C_LIGHT)
        self._finish_status_lbl.pack(side="left")

        self._btn_next = self._btn(nav, "Далее →", self._go_next, bg=C_PRIMARY, bold=True)

    def _render_question(self) -> None:
        q = self.test_questions[self.current_q_idx]

        # Нумерация
        self._lbl_counter.config(
            text=f"Вопрос {self.current_q_idx + 1} из {len(self.test_questions)}"
        )
        self._lbl_question.config(text=q["text"])

        for w in self._opts_frame.winfo_children():
            w.destroy()

        # Рандомное перемешивание вариантов ответа
        opts = list(range(len(q["options"])))
        random.shuffle(opts)

        prev    = self.saved_answers.get(q["id"], set())
        is_mult = (
            isinstance(q.get("correct"), list) and len(q["correct"]) > 1
        )

        if is_mult:
            self.current_vars = []
            for i in opts:
                v = tk.BooleanVar(value=(i in prev))
                tk.Checkbutton(
                    self._opts_frame, text=q["options"][i],
                    variable=v, font=("Arial", 12),
                    bg=C_BG, wraplength=800, justify="left"
                ).pack(anchor="w", pady=5)
                self.current_vars.append((i, v))
        else:
            def_val = list(prev)[0] if prev else -1
            self.current_var = tk.IntVar(value=def_val)
            for i in opts:
                tk.Radiobutton(
                    self._opts_frame, text=q["options"][i],
                    variable=self.current_var, value=i,
                    font=("Arial", 12),
                    bg=C_BG, wraplength=800, justify="left"
                ).pack(anchor="w", pady=5)

        self._btn_next.pack_forget()
        if self.current_q_idx < len(self.test_questions) - 1:
            self._btn_next.pack(side="right", padx=25)

    def _save_current_answers(self):
        q      = self.test_questions[self.current_q_idx]
        sel    = set()
        is_mult = (
            isinstance(q.get("correct"), list) and len(q["correct"]) > 1
        )
        if is_mult:
            for idx, v in self.current_vars:
                if v.get():
                    sel.add(idx)
        else:
            if self.current_var.get() != -1:
                sel.add(self.current_var.get())
        self.saved_answers[q["id"]] = sel

    def _go_next(self):
        self._save_current_answers()
        self.current_q_idx += 1
        self._render_question()

    def _finish_test(self):
        self._save_current_answers()
        correct_count = 0
        for q in self.test_questions:
            target = set(q["correct"]) if isinstance(q["correct"], list) else {q["correct"]}
            if self.saved_answers.get(q["id"], set()) == target:
                correct_count += 1

        total = len(self.test_questions)
        perc  = round((correct_count / total) * 100) if total > 0 else 0
        grade = round(perc / 10)

        self._set_loading(
            True, self._finish_status_lbl, [self._btn_finish], "⏳ Сохранение..."
        )
        threading.Thread(
            target=self._save_thread,
            args=(correct_count, total, perc, grade),
            daemon=True
        ).start()

    def _save_thread(self, c, t, p, g):
        try:
            self.core.save_result(
                self.current_student_id, self.current_test["id"], c, t, p, g
            )
            self.root.after(0, lambda: self._show_results(c, t, p, g))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Ошибка", str(e)))

    # Результаты студента 
    def _show_results(self, c, t, p, g):
        self._clear()

        top = tk.Frame(self.root, bg=C_DARK, pady=20)
        top.pack(fill="x")
        tk.Label(
            top,
            text=f"Ваш результат: {p}%  (Оценка: {g})",
            font=("Arial", 18, "bold"),
            bg=C_DARK, fg=C_SUCCESS
        ).pack()

        # таблица 
        if self._current_open_results:
            container = tk.Frame(self.root, bg=C_BG)
            container.pack(fill="both", expand=True, padx=20, pady=10)

            table_frame = tk.Frame(container)
            table_frame.pack(fill="both", expand=True)

            cols = ("num", "your", "correct")
            tree = ttk.Treeview(table_frame, columns=cols, show="headings")

            tree.heading("num",     text="№ вопроса")
            tree.heading("your",    text="Ваш ответ")
            tree.heading("correct", text="Правильный ответ")

            tree.column("num",     width=100, minwidth=80,  anchor="center")
            tree.column("your",    width=370, minwidth=200)
            tree.column("correct", width=370, minwidth=200)

            tree.tag_configure("correct_row", background="#ccffcc") 
            tree.tag_configure("wrong_row",   background="#ffe6e6")

            v_scroll = ttk.Scrollbar(table_frame, orient="vertical",   command=tree.yview)
            h_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
            tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

            tree.grid(row=0, column=0, sticky="nsew")
            v_scroll.grid(row=0, column=1, sticky="ns")
            h_scroll.grid(row=1, column=0, sticky="ew")
            table_frame.rowconfigure(0, weight=1)
            table_frame.columnconfigure(0, weight=1)

            for row_num, q in enumerate(self.test_questions, start=1):
                correct_idx = (
                    set(q["correct"]) if isinstance(q["correct"], list) else {q["correct"]}
                )
                user_idx    = self.saved_answers.get(q["id"], set())

                correct_text = "; ".join(str(q["options"][i]) for i in sorted(correct_idx))
                user_text    = (
                    "; ".join(str(q["options"][i]) for i in sorted(user_idx))
                    if user_idx else "—"
                )

                is_correct = (user_idx == correct_idx)
                tag = "correct_row" if is_correct else "wrong_row"

                tree.insert("", "end", values=(row_num, user_text, correct_text), tags=(tag,))

        self._btn(
            self.root, "Вернуться в меню",
            self._show_test_list, bg=C_GRAY
        ).pack(pady=20)

    # Панель преподавателя 

    def _teacher_login(self) -> None:
        if (
            self._teacher_login_entry.get() == TEACHER_LOGIN
            and self._teacher_pass_entry.get() == TEACHER_PASSWORD
        ):
            self._show_teacher_panel()
        else:
            messagebox.showerror("Ошибка", "Неверные данные")

    def _show_teacher_panel(self) -> None:
        self._clear()
        frame = tk.Frame(self.root, bg=C_BG)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        self._label(
            frame, "Панель преподавателя", size=16, bold=True
        ).pack(pady=(0, 25))

        self._btn(
            frame, "📋  Просмотр результатов",
            self._load_teacher_dashboard, bg=C_PURPLE, pady=15
        ).pack(pady=10, fill="x")

        self._btn(
            frame, "⚙️  Настройки тестов",
            self._show_test_settings, bg=C_PRIMARY, pady=15
        ).pack(pady=10, fill="x")

        self._btn(
            frame, "🗑  Очистить базу студентов",
            self._clear_students, bg=C_DANGER
        ).pack(pady=10, fill="x")

    # Настройки тестов (преподаватель)

    def _show_test_settings(self) -> None:
        """Загружает настройки из Firebase и открывает экран редактирования."""
        self._clear()
        header = tk.Frame(self.root, bg=C_DARK, pady=10)
        header.pack(fill="x")
        tk.Label(
            header, text="⚙️  Настройки тестов",
            font=("Arial", 14, "bold"), bg=C_DARK, fg=C_WHITE
        ).pack()

        tk.Label(
            self.root, text="⏳ Загрузка настроек…",
            font=("Arial", 12), bg=C_BG
        ).pack(expand=True)

        threading.Thread(target=self._fetch_settings_thread, daemon=True).start()

    def _fetch_settings_thread(self):
        try:
            settings = self.core.get_test_settings()
            self.root.after(0, lambda: self._render_test_settings(settings))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Ошибка", str(e)))

    def _render_test_settings(self, settings: dict) -> None:
        self._clear()

        # Заголовок
        header = tk.Frame(self.root, bg=C_DARK, pady=10)
        header.pack(fill="x")
        tk.Label(
            header, text="⚙️  Настройки тестов",
            font=("Arial", 14, "bold"), bg=C_DARK, fg=C_WHITE
        ).pack()

        outer = tk.Frame(self.root, bg=C_BG)
        outer.pack(fill="both", expand=True, padx=20, pady=10)

        canvas   = tk.Canvas(outer, bg=C_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        scroll_f  = tk.Frame(canvas, bg=C_BG)

        scroll_f.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scroll_f, anchor="nw", width=840)
        canvas.configure(yscrollcommand=scrollbar.set)

        def _mw(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _mw)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Хранилище виджетов для последующего сбора значений 
        self._settings_widgets: dict = {} 

        tests    = self.core.get_tests()
        pool_map = {}
        for test in tests:
            q_end    = min(test["q_end"], 240)   # ≤ общее кол-во вопросов
            pool_map[test["id"]] = max(1, q_end - test["q_start"])

        # Заголовок таблицы
        hdr = tk.Frame(scroll_f, bg=C_LIGHT, pady=6)
        hdr.pack(fill="x", padx=5, pady=(0, 4))
        tk.Label(hdr, text="Вариант",              font=("Arial", 10, "bold"), bg=C_LIGHT, width=14, anchor="w").grid(row=0, column=0, padx=10)
        tk.Label(hdr, text="Кол-во вопросов (10–60)", font=("Arial", 10, "bold"), bg=C_LIGHT, width=25, anchor="w").grid(row=0, column=1, padx=10)
        tk.Label(hdr, text="Показывать правильные ответы", font=("Arial", 10, "bold"), bg=C_LIGHT, width=30, anchor="w").grid(row=0, column=2, padx=10)

        for test in tests:
            tid      = test["id"]
            ts       = settings.get(tid, {})
            pool_sz  = pool_map[tid]
            cur_nq   = max(10, min(60, ts.get("num_questions", pool_sz)))
            cur_or   = ts.get("open_results", test["open_results"])

            row = tk.Frame(scroll_f, bg=C_WHITE, pady=10, relief="solid", bd=1)
            row.pack(fill="x", padx=5, pady=4)

            # Название теста
            tk.Label(
                row, text=test["name"],
                font=("Arial", 11, "bold"), bg=C_WHITE, fg=C_DARK, width=14, anchor="w"
            ).grid(row=0, column=0, padx=15, pady=5, sticky="w")

            # Спинбокс для кол-ва вопросов
            nq_var = tk.StringVar(value=str(cur_nq))
            sb = tk.Spinbox(
                row, from_=10, to=min(60, pool_sz),
                textvariable=nq_var, font=("Arial", 11),
                width=6, justify="center"
            )
            sb.grid(row=0, column=1, padx=25, pady=5, sticky="w")

            # Пояснение о размере пула
            tk.Label(
                row,
                text=f"(пул: {pool_sz} вопр.)",
                font=("Arial", 9), bg=C_WHITE, fg=C_GRAY
            ).grid(row=0, column=1, padx=(110, 0), pady=5, sticky="w")

            # Чекбокс "Показывать правильные ответы"
            or_var = tk.BooleanVar(value=cur_or)
            tk.Checkbutton(
                row, text="Включено",
                variable=or_var,
                font=("Arial", 11), bg=C_WHITE,
                activebackground=C_WHITE
            ).grid(row=0, column=2, padx=25, pady=5, sticky="w")

            self._settings_widgets[tid] = (nq_var, or_var)

        btn_frame = tk.Frame(self.root, bg=C_BG, pady=12)
        btn_frame.pack()

        self._save_settings_status = tk.Label(
            btn_frame, text="", font=("Arial", 10, "italic"), bg=C_BG, fg=C_WARNING
        )
        self._save_settings_status.pack(side="top", pady=(0, 6))

        self._btn_save_settings = self._btn(
            btn_frame, "💾  Сохранить настройки",
            self._save_test_settings, bg=C_SUCCESS, bold=True
        )
        self._btn_save_settings.pack(side="left", padx=8)

        self._btn(
            btn_frame, "← Назад",
            self._show_teacher_panel, bg=C_GRAY
        ).pack(side="left", padx=8)

    def _save_test_settings(self) -> None:
        """Собирает значения из виджетов и сохраняет в Firebase."""
        payload = {}
        for tid, (nq_var, or_var) in self._settings_widgets.items():
            try:
                nq = int(nq_var.get())
                nq = max(10, min(60, nq))
            except ValueError:
                nq = 30
            payload[tid] = {
                "num_questions": nq,
                "open_results":  or_var.get(),
            }

        self._set_loading(
            True,
            self._save_settings_status,
            [self._btn_save_settings],
            "⏳ Сохранение…"
        )
        threading.Thread(
            target=self._save_settings_thread, args=(payload,), daemon=True
        ).start()

    def _save_settings_thread(self, payload: dict):
        try:
            self.core.save_test_settings(payload)
            self.root.after(0, lambda: self._on_settings_saved(payload))
        except Exception as e:
            self.root.after(
                0, lambda: messagebox.showerror("Ошибка сохранения", str(e))
            )

    def _on_settings_saved(self, payload: dict):
        # Кэшируем актуальные настройки локально
        self.test_settings = payload
        self._set_loading(False, self._save_settings_status, [self._btn_save_settings])
        self._save_settings_status.config(text="✅ Настройки сохранены!", fg=C_SUCCESS)

    # Таблица результатов (преподаватель)

    def _load_teacher_dashboard(self):
        self._clear()
        tk.Label(
            self.root, text="⏳ Загрузка данных…",
            font=("Arial", 12), bg=C_BG
        ).pack(expand=True)
        threading.Thread(target=self._fetch_students_thread, daemon=True).start()

    def _fetch_students_thread(self):
        data = self.core.get_all_students()
        self.root.after(0, lambda: self._show_teacher_table(data))

    def _show_teacher_table(self, students):
        self._clear()
        header = tk.Frame(self.root, bg=C_DARK, pady=10)
        header.pack(fill="x")
        tk.Label(
            header, text="Журнал успеваемости",
            font=("Arial", 14, "bold"), bg=C_DARK, fg=C_WHITE
        ).pack()

        tests = self.core.get_tests()
        cols  = ["name", "group"] + [f"t{t['id']}" for t in tests]

        container = tk.Frame(self.root, bg=C_BG)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        tree = ttk.Treeview(container, columns=cols, show="headings")
        tree.heading("name",  text="ФИО")
        tree.heading("group", text="Гр.")
        tree.column("name",  width=200)
        tree.column("group", width=60, anchor="center")

        for t in tests:
            cid = f"t{t['id']}"
            tree.heading(cid, text=f"В{t['id']}")
            tree.column(cid, width=75, anchor="center")

        for sid, info in students.items():
            vals = [info.get("name"), info.get("group")]
            for t in tests:
                p = info.get(f"test_{t['id']}_percentage")
                vals.append(f"{p}%" if p is not None else "-")
            tree.insert("", "end", iid=sid, values=vals)

        tree.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")

        btns = tk.Frame(self.root, bg=C_BG, pady=10)
        btns.pack()
        self._btn(
            btns, "Удалить выбранного",
            lambda: self._delete_student(tree), bg=C_WARNING
        ).pack(side="left", padx=5)
        self._btn(
            btns, "Очистить данные",
            self._clear_students_from_table, bg=C_DANGER
        ).pack(side="left", padx=5)
        self._btn(
            btns, "Назад",
            self._show_teacher_panel, bg=C_GRAY
        ).pack(side="left", padx=5)

    def _delete_student(self, tree):
        sel = tree.selection()
        if not sel:
            return
        if messagebox.askyesno("Удаление", "Удалить результат студента?"):
            self.core.delete_student(sel[0])
            self._load_teacher_dashboard()

    def _clear_students_from_table(self):
        if messagebox.askyesno("Очистка", "Удалить ВСЕХ студентов?"):
            self.core.clear_students()
            self._load_teacher_dashboard()

    def _clear_students(self):
        if messagebox.askyesno("Очистка", "Удалить ВСЕХ студентов?"):
            self.core.clear_students()
            self._show_teacher_panel()
