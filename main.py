import os
from datetime import datetime
import requests
import time


class APIHandler:
    url_users: str = "https://json.medrating.org/users"
    url_todos: str = "https://json.medrating.org/todos"

    def get_users(self) -> list[dict] | None:
        try:
            users_request = requests.get(self.url_users)
            users = users_request.json()
            return users
        except requests.exceptions.ConnectionError:
            print("Не удалось получить список пользователей.")
            return None

    def get_user(self, user_id: int) -> dict | None:
        try:
            user_request = requests.get(f"{self.url_users}/{user_id}")
            user = user_request.json()
            return user
        except requests.exceptions.ConnectionError:
            return None

    def get_user_todos(self, user_id: int):
        try:
            user_todos = requests.get(f"{self.url_todos}/?userId={user_id}")
            todos = user_todos.json()
            return todos
        except requests.exceptions.ConnectionError:
            print("Не удалось получить список задач.")
            return None


class Writer:
    def __init__(self, directory_name: str = "tasks"):
        self.directory_name = directory_name
        self.__api_handler = APIHandler()
        self.__set_users()

    def __mkdir(self) -> bool:
        try:
            if not os.path.exists(self.directory_name):
                os.mkdir(self.directory_name)
            return True
        except OSError:
            print("Ошибка при создании директории.")
            return False

    def __set_users(self) -> None:
        self.users = self.__api_handler.get_users()

    def __get_todos(self, user) -> tuple[dict | None, list[dict], list[dict]]:
        user_todos = self.__api_handler.get_user_todos(user['id'])
        completed_todos = list(filter(lambda todo: todo['completed'], user_todos))
        uncompleted_todos = list(filter(lambda todo: not todo['completed'], user_todos))
        return user_todos, completed_todos, uncompleted_todos

    @staticmethod
    def __get_todo_title(todo: dict) -> str:
        if len(todo['title']) > 48:
            todo['title'] = f"{todo['title'][:48]}..."
        return todo['title']

    def __get_user_record(self, user: dict) -> str:
        user_todos, completed_todos, uncompleted_todos = self.__get_todos(user)

        record = f"Отчёт {user['company']['name']}.\n"
        record += f"{user['name']} <{user['email']}> {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
        record += f"Всего задач: {len(user_todos)}\n\n"

        record += f"Завершённые задачи ({len(completed_todos)}):\n"

        for completed_todo in completed_todos:
            record += f"{self.__get_todo_title(completed_todo)}\n"
        record += "\n"
        record += f"Оставшиеся задачи ({len(uncompleted_todos)}):\n"

        for uncompleted_todo in uncompleted_todos:
            record += f"{self.__get_todo_title(uncompleted_todo)}\n"

        return record

    def __get_user_filename(self, user: dict) -> str:
        filename = f"{user['username']}"

        if os.path.exists(f"{self.directory_name}/{filename}.txt"):
            created_at = os.path.getmtime(f"{self.directory_name}/{filename}.txt")
            created_at = datetime.strptime(time.ctime(created_at), "%a %b %d %H:%M:%S %Y")
            os.renames(f"{self.directory_name}/{filename}.txt",
                       f"{self.directory_name}/old_{filename}_{created_at.strftime('%Y-%m-%dT%H-%M')}.txt")

        return f"{filename}.txt"

    def __write(self) -> None:
        if self.__mkdir():
            for user in self.users:
                with open(
                        f"{self.directory_name}/{self.__get_user_filename(user)}", 'w', encoding="utf-8"
                ) as user_file:
                    record = self.__get_user_record(user)
                    user_file.write(record)

    def run(self) -> None:
        self.__write()


if __name__ == "__main__":
    writer = Writer()
    writer.run()
