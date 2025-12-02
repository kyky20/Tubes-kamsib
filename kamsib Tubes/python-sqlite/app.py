from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import sqlite3

app = Flask(__name__)

# [MITIGASI CLICKJACKING]
@app.after_request
def add_security_headers(response):
    # Mencegah browser merender halaman di dalam frame/iframe
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    return response

# [PENTING] Secret key diperlukan untuk fitur session
app.secret_key = 'kunci_rahasia_anda_disini' 

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    grade = db.Column(db.String(10), nullable=False)

    def __repr__(self):
        return f'<Student {self.name}>'

# --- ROUTE AUTHENTICATION (Login & Logout) ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Validasi sederhana (Hardcoded untuk contoh)
        # Username: admin, Password: admin321
        if username == 'admin' and password == 'admin321':
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('index'))
        else:
            error = 'Username atau Password salah!'
            
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear() # Menghapus semua data sesi
    return redirect(url_for('login'))

# --- ROUTE UTAMA ---

@app.route('/')
def index():
    # Opsi: Jika ingin halaman depan juga butuh login, hilangkan tanda pagar di bawah:
    # if 'logged_in' not in session:
    #     return redirect(url_for('login'))

    # RAW Query
    students = db.session.execute(text('SELECT * FROM student')).fetchall()
    
    # Kirim status login ke template (opsional, untuk menyembunyikan/menampilkan tombol)
    user_logged_in = 'logged_in' in session
    return render_template('index.html', students=students, logged_in=user_logged_in)

@app.route('/add', methods=['POST'])
def add_student():
    # [Proteksi: Cek Login]
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    name = request.form['name']
    age = request.form['age']
    grade = request.form['grade']
    
    connection = sqlite3.connect('instance/students.db')
    cursor = connection.cursor()

    # [PERBAIKAN KEAMANAN: SQL Injection]
    # KODE LAMA (RENTAN):
    # query = f"INSERT INTO student (name, age, grade) VALUES ('{name}', {age}, '{grade}')"
    # cursor.execute(query)

    # KODE BARU (AMAN):
    # Menggunakan placeholder (?) agar input dianggap sebagai data, bukan perintah
    query = "INSERT INTO student (name, age, grade) VALUES (?, ?, ?)"
    cursor.execute(query, (name, age, grade))
    
    connection.commit()
    connection.close()
    return redirect(url_for('index'))

@app.route('/delete/<string:id>') 
def delete_student(id):
    # [Proteksi: Cek Login]
    if 'logged_in' not in session:
        return redirect(url_for('login')) # Arahkan ke halaman login jika belum login
    
    # RAW Query
    db.session.execute(text(f"DELETE FROM student WHERE id={id}"))
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_student(id):
    # [Proteksi: Cek Login]
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        grade = request.form['grade']
        
        # RAW Query
        db.session.execute(text(f"UPDATE student SET name='{name}', age={age}, grade='{grade}' WHERE id={id}"))
        db.session.commit()
        return redirect(url_for('index'))
    else:
        # RAW Query
        student = db.session.execute(text(f"SELECT * FROM student WHERE id={id}")).fetchone()
        return render_template('edit.html', student=student)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)