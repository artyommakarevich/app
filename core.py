import sys
import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import uuid

TESTS = [
    {"id": 1, "name": "Вариант 1", "q_start": 0,   "q_end": 60,  "open_results": True},
    {"id": 2, "name": "Вариант 2", "q_start": 60,  "q_end": 120, "open_results": True},
    {"id": 3, "name": "Вариант 3", "q_start": 120, "q_end": 180, "open_results": True},
    {"id": 4, "name": "Вариант 4", "q_start": 179, "q_end": 240, "open_results": True},
    {"id": 5, "name": "Вариант 5", "q_start": 0,   "q_end": 60,  "open_results": False},
    {"id": 6, "name": "Вариант 6", "q_start": 60,  "q_end": 120, "open_results": False},
    {"id": 7, "name": "Вариант 7", "q_start": 120, "q_end": 180, "open_results": False},
    {"id": 8, "name": "Вариант 8", "q_start": 179, "q_end": 240, "open_results": False},
]


def resource_path(relative_name: str) -> str:
    """Возвращает абсолютный путь к ресурсу — работает и в .exe (PyInstaller),
    и в обычном Python."""
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative_name)


class Core:
    def __init__(self):
        self._cred_path = resource_path(
            "app-test-for-students-7ba3a-firebase-adminsdk-fbsvc-579eafcfa1.json"
        )

    def _ensure_firebase(self) -> None:
        """Инициализирует Firebase при первом обращении."""
        if not firebase_admin._apps:
            cred = credentials.Certificate(self._cred_path)
            firebase_admin.initialize_app(
                cred,
                {
                    "databaseURL": (
                        "https://app-test-for-students-7ba3a-default-rtdb"
                        ".europe-west1.firebasedatabase.app/"
                    )
                },
            )

    #Тесты

    def get_tests(self) -> list:
        return TESTS

    # Вопросы

    def get_questions(self) -> list:
        self._ensure_firebase()
        ref = db.reference("questions")
        data = ref.get()
        if isinstance(data, dict) and "questions" in data:
            return [q for q in data["questions"] if q is not None]
        elif isinstance(data, list):
            return [q for q in data if q is not None]
        return []

    #  Настройки тестов (хранятся в Firebase) 

    def get_test_settings(self) -> dict:
        """Возвращает словарь {test_id: {num_questions, open_results}}.
        Если настройки не сохранены — берёт значения по умолчанию из TESTS."""
        self._ensure_firebase()
        data = db.reference("test_settings").get() or {}
        result = {}
        for test in TESTS:
            tid = test["id"]
            pool_size = test["q_end"] - test["q_start"]
            default_nq = min(60, max(10, pool_size))
            default_or = test["open_results"]
            saved = data.get(str(tid), {})
            result[tid] = {
                "num_questions": int(saved.get("num_questions", default_nq)),
                "open_results": bool(saved.get("open_results", default_or)),
            }
        return result

    def save_test_settings(self, settings: dict) -> None:
        """Сохраняет все настройки тестов за один вызов.
        settings = {test_id: {num_questions: int, open_results: bool}}
        """
        self._ensure_firebase()
        payload = {str(tid): v for tid, v in settings.items()}
        db.reference("test_settings").set(payload)

    # Студенты

    def create_student(self, name: str, group: str) -> str:
        self._ensure_firebase()
        student_id = str(uuid.uuid4())
        db.reference(f"students/{student_id}").set({"name": name, "group": group})
        return student_id

    def save_result(
        self,
        student_id: str,
        test_id: int,
        correct_count: int,
        total_count: int,
        percentage: int,
        grade: int,
    ) -> None:
        self._ensure_firebase()
        db.reference(f"students/{student_id}").update(
            {
                f"test_{test_id}_correct":    correct_count,
                f"test_{test_id}_total":      total_count,
                f"test_{test_id}_percentage": percentage,
                f"test_{test_id}_grade":      grade,
            }
        )

    def get_all_students(self) -> dict:
        self._ensure_firebase()
        data = db.reference("students").get()
        return data if data else {}

    def delete_student(self, student_id: str) -> None:
        self._ensure_firebase()
        db.reference(f"students/{student_id}").delete()

    def clear_students(self) -> None:
        self._ensure_firebase()
        db.reference("students").delete()
