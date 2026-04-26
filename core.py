import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import uuid

class Core:
    def __init__(self):
        # 1. Путь к вашему скачанному JSON-ключу
        cred_path = r"D:\git_training\app\app-test-for-students-7ba3a-firebase-adminsdk-fbsvc-579eafcfa1.json"
        
        # Защита от повторной инициализации
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            # 2. Инициализация приложения
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://app-test-for-students-7ba3a-default-rtdb.europe-west1.firebasedatabase.app/'
            })

    def create_student(self, name, group):
        """Создает запись о студенте в базе данных в момент входа и возвращает его уникальный ID"""
        student_id = str(uuid.uuid4())
        ref = db.reference(f'students/{student_id}')
        ref.set({
            'name': name,
            'group': group,
            'status': 'started' # Статус, чтобы понимать, завершил ли он тест
        })
        return student_id

    def save_result(self, student_id, correct_count, total_count, percentage, grade):
        """Обновляет запись студента результатами теста"""
        ref = db.reference(f'students/{student_id}')
        ref.update({
            'status': 'completed',
            'correct_count': correct_count,
            'total_count': total_count,
            'percentage': percentage,
            'grade': grade
        })

    def get_questions(self):
        """Получает список вопросов из Firebase"""
        ref = db.reference('questions')
        data = ref.get()
        
        # Обработка структуры JSON (если данные загружены как словарь с ключом 'questions')
        if isinstance(data, dict) and 'questions' in data:
            return [q for q in data['questions'] if q is not None]
        # Если загружены напрямую как список
        elif isinstance(data, list):
            return [q for q in data if q is not None]
        return []

    def get_all_students(self):
        """Получает словарь со всеми студентами для преподавателя"""
        ref = db.reference('students')
        data = ref.get()
        if data:
            return data
        return {}