from flask import Flask, request, jsonify, abort
import uuid
from typing import List, Dict

#Создаём экземпляр приложения Flask
app = Flask(__name__)
#Список для хранения задач
tasks: List[Dict] = []

#Класс Task для представления задачи
class Task:
    def __init__(self, title: str, description: str = "", completed: bool = False):
        #Генерация id
        self.id = str(uuid.uuid4())
        #Название задачи
        self.title = title
        #Описание задачи
        self.description = description
        #Статус выполнения задачи (по умолчанию False)
        self.completed = completed

    def to_dict(self):
        #Метод возвращает задачу в виде словаря
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "completed": self.completed
        }

#Получения списка задач с поддержкой фильтрации, поиска и пагинации
@app.route('/tasks', methods=['GET'])
def get_tasks():
    #Получаем параметры запроса из URL
    #фильтр по статусу выполнения (true/false)
    completed = request.args.get('completed')
    #строка для поиска в названии задач
    search = request.args.get('search')
    #номер страницы для пагинации (по умолчанию 1)
    page = request.args.get('page', default=1, type=int)
    #количество задач на странице (по умолчанию 10)
    size = request.args.get('size', default=10, type=int)

    #Создаём копию списка задач, чтобы не изменять оригинал
    filtered_tasks = tasks[:]

    #Фильтрация по статусу выполнения
    if completed is not None:
        completed = completed.lower() == 'true'
        filtered_tasks = [task for task in filtered_tasks if task.completed == completed]

    # Поиск по названию задачи
    if search is not None:
        filtered_tasks = [task for task in filtered_tasks if search.lower() in task.title.lower()]

    # Реализация пагинации
    # Считаем общее количество задач после фильтрации
    total_tasks = len(filtered_tasks)
    # Вычисляем начальный индекс для текущей страницы
    start = (page - 1) * size
    # Вычисляем конечный индекс
    end = start + size
    # Извлекаем задачи для текущей страницы
    paginated_tasks = filtered_tasks[start:end]

    # Формируем ответ с метаинформацией о пагинации
    response = {
        "tasks": [task.to_dict() for task in paginated_tasks],  # Список задач в формате JSON
        "total": total_tasks,  # Общее количество задач
        "page": page,  # Текущая страница
        "size": size,  # Размер страницы
        "total_pages": (total_tasks + size - 1) // size  # Общее количество страниц
    }
    # Возвращаем ответ с кодом 200 OK
    return jsonify(response), 200

#Получение задачи по её ID
@app.route('/tasks/<task_id>', methods=['GET'])
def get_task(task_id: str):
    task = next((t for t in tasks if t.id == task_id), None)
    #Если задача не найдена, возвращаем ошибку 404
    if task is None:
        abort(404, description="Task not found")
    #Возвращаем задачу с кодом 200 OK
    return jsonify(task.to_dict()), 200

#Создание новой задачи
@app.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    #Проверяем наличие данных, поле title не пустое
    if not data or 'title' not in data or not data['title']:
        abort(400, description="Title is required")
    #Создаём новую задачу
    task = Task(
        title=data['title'],
        description=data.get('description', ''),  #Если description не указано, используем пустую строку
        completed=data.get('completed', False)    #Если completed не указано, используем False
    )
    #Добавляем задачу в список
    tasks.append(task)
    #Возвращаем созданную задачу с кодом 201 Created
    return jsonify(task.to_dict()), 201

#Обновление существующей задачи
@app.route('/tasks/<task_id>', methods=['PUT'])
def update_task(task_id: str):
    #Ищем задачу по ID
    task = next((t for t in tasks if t.id == task_id), None)
    #Если задача не найдена, возвращаем ошибку 404
    if task is None:
        abort(404, description="Task not found")
    #Получаем данные из тела запроса
    data = request.get_json()
    #Проверяем, что данные переданы
    if not data:
        abort(400, description="No data provided")
    #Обновляем поля задачи, если они указаны в запросе
    if 'title' in data:
        if not data['title']:
            abort(400, description="Title cannot be empty")
        task.title = data['title']
    if 'description' in data:
        task.description = data['description']
    if 'completed' in data:
        task.completed = data['completed']
    # Возвращаем обновлённую задачу с кодом 200 OK
    return jsonify(task.to_dict()), 200

#Удаление задачи
@app.route('/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id: str):
    global tasks
    #Ищем задачу по ID
    task = next((t for t in tasks if t.id == task_id), None)
    #Если задача не найдена, возвращаем ошибку 404
    if task is None:
        abort(404, description="Task not found")
    #Удаляем задачу из списка
    tasks = [t for t in tasks if t.id != task_id]
    #Возвращаем пустой ответ с кодом 204 No Content
    return '', 204

#Обработчик ошибки 400 Bad Request
@app.errorhandler(400)
def bad_request(error):
    # Возвращаем описание ошибки
    return jsonify({"error": str(error.description)}), 400

#Обработчик ошибки 404 Not Found
@app.errorhandler(404)
def not_found(error):
    # Возвращаем описание ошибки
    return jsonify({"error": str(error.description)}), 404

# Запускаем сервер Flask в режиме отладки на порту 5000
if __name__ == '__main__':
    app.run(debug=True, port=5000)