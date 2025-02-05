import sys
import sqlite3
import csv
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QPushButton,
    QVBoxLayout, QHBoxLayout, QWidget, QLineEdit, QLabel, QDialog, QFormLayout,
    QDateEdit, QComboBox, QTextEdit, QMessageBox, QHeaderView, QCheckBox, QFileDialog
)
from PyQt5.QtCore import Qt, QDate



class Task:
    def __init__(self, id, title, description, due_date, priority, completed, category):
        self.id = id  # Database ID (None if not yet saved)
        self.title = title
        self.description = description
        self.due_date = due_date  # stored as a string "yyyy-MM-dd"
        self.priority = priority  # "Low", "Medium", or "High"
        self.completed = completed  # Boolean
        self.category = category  # Optional category string


# Database Handler  SQLite
class TaskDatabase:
    def __init__(self, db_file="tasks.db"):
        self.conn = sqlite3.connect(db_file)
        self.create_table()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                due_date TEXT,
                priority TEXT,
                completed INTEGER,
                category TEXT
            )
        """)
        self.conn.commit()

    def add_task(self, task):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO tasks (title, description, due_date, priority, completed, category) VALUES (?, ?, ?, ?, ?, ?)",
            (task.title, task.description, task.due_date, task.priority, 1 if task.completed else 0, task.category)
        )
        self.conn.commit()
        task.id = cursor.lastrowid
        return task.id

    def update_task(self, task):
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE tasks SET title=?, description=?, due_date=?, priority=?, completed=?, category=? WHERE id=?",
            (task.title, task.description, task.due_date, task.priority, 1 if task.completed else 0, task.category,
             task.id)
        )
        self.conn.commit()

    def delete_task(self, task_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        self.conn.commit()

    def get_all_tasks(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, title, description, due_date, priority, completed, category FROM tasks")
        rows = cursor.fetchall()
        tasks = []
        for row in rows:
            id, title, description, due_date, priority, completed, category = row
            task = Task(id, title, description, due_date, priority, bool(completed), category)
            tasks.append(task)
        return tasks



# Adding/Editing a Task

class TaskDialog(QDialog):
    def __init__(self, parent=None, task=None):
        super(TaskDialog, self).__init__(parent)
        self.setWindowTitle("Add Task" if task is None else "Edit Task")
        self.task = task

        # Create input fields
        self.title_edit = QLineEdit()
        self.description_edit = QTextEdit()
        self.due_date_edit = QDateEdit()
        self.due_date_edit.setCalendarPopup(True)
        self.due_date_edit.setDate(QDate.currentDate())
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Low", "Medium", "High"])
        self.category_edit = QLineEdit()
        self.completed_checkbox = QCheckBox("Completed")

        # Layout using QFormLayout
        form_layout = QFormLayout()
        form_layout.addRow("Title:", self.title_edit)
        form_layout.addRow("Description:", self.description_edit)
        form_layout.addRow("Due Date:", self.due_date_edit)
        form_layout.addRow("Priority:", self.priority_combo)
        form_layout.addRow("Category:", self.category_edit)
        form_layout.addRow("", self.completed_checkbox)

        # Dialog buttons
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)

        main_layout = QVBoxLayout()
        main_layout.addLayout(form_layout)
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

        # If editing an existing task, pre-fill the fields
        if task:
            self.title_edit.setText(task.title)
            self.description_edit.setPlainText(task.description)
            if task.due_date:
                dt = QDate.fromString(task.due_date, "yyyy-MM-dd")
                if dt.isValid():
                    self.due_date_edit.setDate(dt)
            self.priority_combo.setCurrentText(task.priority)
            self.category_edit.setText(task.category)
            self.completed_checkbox.setChecked(task.completed)

    def get_task_data(self):
        """Return the data from the dialog as a dictionary."""
        title = self.title_edit.text()
        description = self.description_edit.toPlainText()
        due_date = self.due_date_edit.date().toString("yyyy-MM-dd")
        priority = self.priority_combo.currentText()
        category = self.category_edit.text()
        completed = self.completed_checkbox.isChecked()
        return {
            "title": title,
            "description": description,
            "due_date": due_date,
            "priority": priority,
            "category": category,
            "completed": completed
        }



# Main Window

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("To-Do List App")
        self.resize(900, 650)

        self.db = TaskDatabase()  # Handles database operations
        self.tasks = []

        # Themes
        self.light_theme = """
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTableWidget {
                background-color: #ffffff;
                border: 1px solid #cccccc;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QLineEdit, QComboBox, QTextEdit, QDateEdit {
                padding: 4px;
                border: 1px solid #cccccc;
                border-radius: 4px;
            }
            QLabel {
                font-weight: bold;
            }
        """
        self.dark_theme = """
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QTableWidget {
                background-color: #3c3f41;
                color: #ffffff;
                border: 1px solid #555555;
            }
            QPushButton {
                background-color: #007ACC;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #005F9E;
            }
            QLineEdit, QComboBox, QTextEdit, QDateEdit {
                padding: 4px;
                border: 1px solid #555555;
                border-radius: 4px;
                background-color: #3c3f41;
                color: #ffffff;
            }
            QLabel {
                font-weight: bold;
                color: #ffffff;
            }
        """
        self.dark_mode = False  # Start in light mode


        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)


        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search tasks...")
        self.search_bar.textChanged.connect(self.refresh_tasks)

        self.filter_priority = QComboBox()
        self.filter_priority.addItem("All Priorities")
        self.filter_priority.addItems(["Low", "Medium", "High"])
        self.filter_priority.currentIndexChanged.connect(self.refresh_tasks)

        self.filter_completed = QComboBox()
        self.filter_completed.addItems(["All", "Completed", "Incomplete"])
        self.filter_completed.currentIndexChanged.connect(self.refresh_tasks)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Search:"))
        filter_layout.addWidget(self.search_bar)
        filter_layout.addWidget(QLabel("Priority:"))
        filter_layout.addWidget(self.filter_priority)
        filter_layout.addWidget(QLabel("Status:"))
        filter_layout.addWidget(self.filter_completed)


        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Title", "Due Date", "Priority", "Category", "Completed"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSortingEnabled(True)  # Enable sorting by clicking on column headers


        self.add_button = QPushButton("Add Task")
        self.edit_button = QPushButton("Edit Task")
        self.delete_button = QPushButton("Delete Task")
        self.toggle_completed_button = QPushButton("Toggle Completed")

        self.add_button.clicked.connect(self.add_task)
        self.edit_button.clicked.connect(self.edit_task)
        self.delete_button.clicked.connect(self.delete_task)
        self.toggle_completed_button.clicked.connect(self.toggle_completed)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.toggle_completed_button)

        # --- Extra Feature Buttons ---
        self.clear_completed_button = QPushButton("Clear Completed")
        self.export_csv_button = QPushButton("Export CSV")
        self.import_csv_button = QPushButton("Import CSV")
        self.toggle_theme_button = QPushButton("Toggle Theme")
        self.mark_all_completed_button = QPushButton("Mark All Completed")

        self.clear_completed_button.clicked.connect(self.clear_completed_tasks)
        self.export_csv_button.clicked.connect(self.export_tasks_csv)
        self.import_csv_button.clicked.connect(self.import_tasks_csv)
        self.toggle_theme_button.clicked.connect(self.toggle_theme)
        self.mark_all_completed_button.clicked.connect(self.mark_all_completed)

        extra_button_layout = QHBoxLayout()
        extra_button_layout.addWidget(self.clear_completed_button)
        extra_button_layout.addWidget(self.export_csv_button)
        extra_button_layout.addWidget(self.import_csv_button)
        extra_button_layout.addWidget(self.toggle_theme_button)
        extra_button_layout.addWidget(self.mark_all_completed_button)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(filter_layout)
        main_layout.addWidget(self.table)
        main_layout.addLayout(button_layout)
        main_layout.addLayout(extra_button_layout)

        self.main_widget.setLayout(main_layout)

        # Theme
        QApplication.instance().setStyleSheet(self.light_theme)

        self.refresh_tasks()  # Load tasks from the database

    def refresh_tasks(self):
        """Reload tasks from the database and apply search/filter criteria."""
        self.tasks = self.db.get_all_tasks()

        # Filter by search keyword
        keyword = self.search_bar.text().lower()
        if keyword:
            self.tasks = [task for task in self.tasks
                          if keyword in task.title.lower() or keyword in task.description.lower()]

        # Filter by priority
        priority_filter = self.filter_priority.currentText()
        if priority_filter != "All Priorities":
            self.tasks = [task for task in self.tasks if task.priority == priority_filter]

        # Filter by completion status
        completed_filter = self.filter_completed.currentText()
        if completed_filter == "Completed":
            self.tasks = [task for task in self.tasks if task.completed]
        elif completed_filter == "Incomplete":
            self.tasks = [task for task in self.tasks if not task.completed]

        self.populate_table()

    def populate_table(self):
        """Populate the QTableWidget with the current list of tasks."""
        self.table.setRowCount(0)
        for task in self.tasks:
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)
            self.table.setItem(row_position, 0, QTableWidgetItem(str(task.id)))
            self.table.setItem(row_position, 1, QTableWidgetItem(task.title))
            self.table.setItem(row_position, 2, QTableWidgetItem(task.due_date))
            self.table.setItem(row_position, 3, QTableWidgetItem(task.priority))
            self.table.setItem(row_position, 4, QTableWidgetItem(task.category))
            self.table.setItem(row_position, 5, QTableWidgetItem("Yes" if task.completed else "No"))

    def add_task(self):
        """Open the Add Task dialog and add a new task if accepted."""
        dialog = TaskDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_task_data()
            if not data["title"]:
                QMessageBox.warning(self, "Validation Error", "Title cannot be empty.")
                return
            new_task = Task(None, data["title"], data["description"], data["due_date"],
                            data["priority"], data["completed"], data["category"])
            self.db.add_task(new_task)
            self.refresh_tasks()

    def get_selected_task(self):
        """Return the Task object corresponding to the currently selected row."""
        selected_items = self.table.selectedItems()
        if selected_items:
            task_id = int(selected_items[0].text())
            for task in self.tasks:
                if task.id == task_id:
                    return task
        return None

    def edit_task(self):
        """Open the Edit Task dialog for the selected task."""
        task = self.get_selected_task()
        if task:
            dialog = TaskDialog(self, task)
            if dialog.exec_() == QDialog.Accepted:
                data = dialog.get_task_data()
                if not data["title"]:
                    QMessageBox.warning(self, "Validation Error", "Title cannot be empty.")
                    return
                task.title = data["title"]
                task.description = data["description"]
                task.due_date = data["due_date"]
                task.priority = data["priority"]
                task.category = data["category"]
                task.completed = data["completed"]
                self.db.update_task(task)
                self.refresh_tasks()
        else:
            QMessageBox.warning(self, "No selection", "Please select a task to edit.")

    def delete_task(self):
        """Delete the currently selected task after confirmation."""
        task = self.get_selected_task()
        if task:
            reply = QMessageBox.question(
                self, "Confirm Delete",
                f"Are you sure you want to delete task '{task.title}'?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.db.delete_task(task.id)
                self.refresh_tasks()
        else:
            QMessageBox.warning(self, "No selection", "Please select a task to delete.")

    def toggle_completed(self):
        """Toggle the completion status of the selected task."""
        task = self.get_selected_task()
        if task:
            task.completed = not task.completed
            self.db.update_task(task)
            self.refresh_tasks()
        else:
            QMessageBox.warning(self, "No selection", "Please select a task to toggle its completion status.")


    def clear_completed_tasks(self):
        """Delete all tasks that are marked as completed."""
        completed_tasks = [task for task in self.db.get_all_tasks() if task.completed]
        if not completed_tasks:
            QMessageBox.information(self, "Info", "No completed tasks to clear.")
            return
        reply = QMessageBox.question(
            self, "Confirm Clear",
            "Are you sure you want to delete all completed tasks?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            for task in completed_tasks:
                self.db.delete_task(task.id)
            self.refresh_tasks()

    def mark_all_completed(self):
        """Mark all tasks as completed."""
        tasks_updated = False
        for task in self.db.get_all_tasks():
            if not task.completed:
                task.completed = True
                self.db.update_task(task)
                tasks_updated = True
        if tasks_updated:
            QMessageBox.information(self, "Success", "All tasks have been marked as completed.")
        else:
            QMessageBox.information(self, "Info", "All tasks were already completed.")
        self.refresh_tasks()

    def export_tasks_csv(self):
        """Export all tasks to a CSV file."""
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getSaveFileName(self, "Export Tasks to CSV", "", "CSV Files (*.csv)", options=options)
        if filename:
            try:
                with open(filename, mode='w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    # Write header row
                    writer.writerow(["Title", "Description", "Due Date", "Priority", "Completed", "Category"])
                    for task in self.db.get_all_tasks():
                        writer.writerow([
                            task.title,
                            task.description,
                            task.due_date,
                            task.priority,
                            "Yes" if task.completed else "No",
                            task.category
                        ])
                QMessageBox.information(self, "Success", f"Tasks exported successfully to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred while exporting tasks:\n{e}")

    def import_tasks_csv(self):
        """Import tasks from a CSV file."""
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(self, "Import Tasks from CSV", "", "CSV Files (*.csv)",
                                                  options=options)
        if filename:
            try:
                with open(filename, mode='r', newline='', encoding='utf-8') as file:
                    reader = csv.reader(file)
                    header = next(reader, None)  # Skip header row if present
                    count = 0
                    for row in reader:
                        if len(row) < 6:
                            continue  # Skip invalid rows
                        title, description, due_date, priority, completed_str, category = row[:6]
                        completed = True if completed_str.strip().lower() in ["yes", "true", "1"] else False
                        if not title.strip():
                            continue  # Skip tasks without a title
                        new_task = Task(None, title.strip(), description.strip(), due_date.strip(),
                                        priority.strip(), completed, category.strip())
                        self.db.add_task(new_task)
                        count += 1
                QMessageBox.information(self, "Success", f"{count} tasks imported successfully from {filename}")
                self.refresh_tasks()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred while importing tasks:\n{e}")

    def toggle_theme(self):
        """Toggle between light and dark themes."""
        app = QApplication.instance()
        if self.dark_mode:
            app.setStyleSheet(self.light_theme)
            self.dark_mode = False
        else:
            app.setStyleSheet(self.dark_theme)
            self.dark_mode = True



if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Light theme (the MainWindow.toggle_theme method will override this)
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f5f5f5;
        }
        QTableWidget {
            background-color: #ffffff;
            border: 1px solid #cccccc;
        }
        QPushButton {
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #45a049;
        }
        QLineEdit, QComboBox, QTextEdit, QDateEdit {
            padding: 4px;
            border: 1px solid #cccccc;
            border-radius: 4px;
        }
        QLabel {
            font-weight: bold;
        }
    """)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
