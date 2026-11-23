from pathlib import Path
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "student_record_app_key"
DB_PATH = Path(__file__).resolve().parent / "students.db"


def get_connection():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def create_table():
    with get_connection() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS students (
                roll INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                marks REAL NOT NULL
            )
        """)


@app.route("/")
def dashboard():
    with get_connection() as con:
        total = con.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        average = con.execute("SELECT AVG(marks) FROM students").fetchone()[0]
        highest = con.execute("SELECT MAX(marks) FROM students").fetchone()[0]
        recent = con.execute("SELECT * FROM students ORDER BY roll DESC LIMIT 5").fetchall()
    return render_template("dashboard.html", total=total,
                           average=round(average or 0, 1),
                           highest=round(highest or 0, 1), recent=recent)


@app.route("/students")
def students_page():
    search = request.args.get("q", "").strip()
    with get_connection() as con:
        if search:
            if search.isdigit():
                records = con.execute(
                    "SELECT * FROM students WHERE roll = ? OR name LIKE ? ORDER BY roll",
                    (int(search), f"%{search}%")
                ).fetchall()
            else:
                records = con.execute(
                    "SELECT * FROM students WHERE name LIKE ? ORDER BY roll",
                    (f"%{search}%",)
                ).fetchall()
        else:
            records = con.execute("SELECT * FROM students ORDER BY roll").fetchall()
    return render_template("students.html", students=records, search=search)


@app.route("/add", methods=["POST"])
def add_student():
    try:
        roll = int(request.form.get("roll", ""))
        name = request.form.get("name", "").strip()
        age = int(request.form.get("age", ""))
        marks = float(request.form.get("marks", ""))
        if roll <= 0:
            raise ValueError("Roll number must be greater than zero.")
        if not name or not all(part.isalpha() for part in name.split()):
            raise ValueError("Enter a valid name using letters only.")
        if not 5 <= age <= 100:
            raise ValueError("Age must be between 5 and 100.")
        if not 0 <= marks <= 100:
            raise ValueError("Marks must be between 0 and 100.")
        with get_connection() as con:
            con.execute("INSERT INTO students (roll, name, age, marks) VALUES (?, ?, ?, ?)",
                        (roll, name, age, marks))
        flash("Student record added successfully.", "success")
    except ValueError as exc:
        flash(str(exc) or "Please enter valid details.", "error")
    except sqlite3.IntegrityError:
        flash("That roll number already exists.", "error")
    return redirect(url_for("students_page"))


@app.route("/delete/<int:roll>", methods=["POST"])
def delete_student(roll):
    with get_connection() as con:
        con.execute("DELETE FROM students WHERE roll = ?", (roll,))
    flash("Student record deleted.", "success")
    return redirect(url_for("students_page"))


if __name__ == "__main__":
    create_table()
    app.run(debug=True)
