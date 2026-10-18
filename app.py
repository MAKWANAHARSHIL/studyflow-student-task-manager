
import json
import os
from pathlib import Path
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY", "development-only-change-this"
)

DATA_DIR = Path(os.environ.get("TASK_DATA_DIR", "data"))
DATA_FILE = DATA_DIR / "tasks.json"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_tasks():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            tasks = json.load(file)
            return tasks if isinstance(tasks, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_tasks(tasks):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    temporary_file = DATA_FILE.with_suffix(".tmp")

    with open(temporary_file, "w", encoding="utf-8") as file:
        json.dump(tasks, file, indent=2)

    temporary_file.replace(DATA_FILE)


@app.get("/")
def index():
    tasks = sorted(
        load_tasks(),
        key=lambda task: task.get("created_at", ""),
        reverse=True
    )

    completed = sum(task.get("completed", False) for task in tasks)

    return render_template(
        "index.html",
        tasks=tasks,
        total=len(tasks),
        completed=completed,
        pending=len(tasks) - completed
    )


@app.post("/add")
def add_task():
    title = request.form.get("title", "").strip()
    subject = request.form.get("subject", "").strip()
    due_date = request.form.get("due_date", "").strip()
    priority = request.form.get("priority", "Medium")

    if not title:
        flash("Please enter a task title.", "error")
        return redirect(url_for("index"))

    if priority not in {"Low", "Medium", "High"}:
        priority = "Medium"

    tasks = load_tasks()

    tasks.append({
        "id": max([task.get("id", 0) for task in tasks] + [0]) + 1,
        "title": title[:120],
        "subject": subject[:80],
        "due_date": due_date,
        "priority": priority,
        "completed": False,
        "created_at": datetime.utcnow().isoformat() + "Z"
    })

    save_tasks(tasks)
    flash("Task added successfully.", "success")
    return redirect(url_for("index"))


@app.post("/toggle/<int:task_id>")
def toggle_task(task_id):
    tasks = load_tasks()

    for task in tasks:
        if task.get("id") == task_id:
            task["completed"] = not task.get("completed", False)
            save_tasks(tasks)
            flash("Task status updated.", "success")
            break
    else:
        flash("Task not found.", "error")

    return redirect(url_for("index"))


@app.post("/delete/<int:task_id>")
def delete_task(task_id):
    tasks = load_tasks()
    updated = [task for task in tasks if task.get("id") != task_id]

    if len(updated) == len(tasks):
        flash("Task not found.", "error")
    else:
        save_tasks(updated)
        flash("Task deleted.", "success")

    return redirect(url_for("index"))


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "student-task-manager"
    }


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "5000")),
        debug=False
    )
