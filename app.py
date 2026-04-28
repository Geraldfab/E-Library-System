from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'torres-capitol-college-elibrary-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///elibrary.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Configure upload folder
UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default='student')
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200), nullable=False)
    isbn = db.Column(db.String(20), unique=True)
    category = db.Column(db.String(100))
    description = db.Column(db.Text)
    cover_image = db.Column(db.String(200))
    ebook_file = db.Column(db.String(200))
    stock = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class Borrowing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    borrow_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    return_date = db.Column(db.DateTime, nullable=True)
    due_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='borrowed')
    
    user = db.relationship('User', backref='borrowings')
    book = db.relationship('Book', backref='borrowings')

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            flash('Welcome back, {}!'.format(user.full_name), 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html', school_name='Torres Capitol College', school_short='TCC')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        full_name = request.form.get('full_name')
        
        # Validation
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('signup.html', school_name='Torres Capitol College', school_short='TCC')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return render_template('signup.html', school_name='Torres Capitol College', school_short='TCC')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return render_template('signup.html', school_name='Torres Capitol College', school_short='TCC')
        
        # Create new user
        hashed_password = generate_password_hash(password)
        new_user = User(
            username=username,
            email=email,
            password=hashed_password,
            full_name=full_name,
            role='student'
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html', school_name='Torres Capitol College', school_short='TCC')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    books = Book.query.all()
    borrowed_books = Borrowing.query.filter_by(user_id=session['user_id'], status='borrowed').all()
    
    return render_template('dashboard.html', 
                         user=user, 
                         books=books, 
                         borrowed_books=borrowed_books,
                         school_name='Torres Capitol College',
                         school_short='TCC')

@app.route('/library')
def library():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    search_query = request.args.get('search', '')
    category = request.args.get('category', '')
    
    query = Book.query
    
    if search_query:
        query = query.filter(Book.title.contains(search_query) | Book.author.contains(search_query))
    
    if category:
        query = query.filter_by(category=category)
    
    books = query.all()
    categories = db.session.query(Book.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    
    return render_template('library.html', 
                         books=books, 
                         categories=categories,
                         school_name='Torres Capitol College',
                         school_short='TCC')

@app.route('/borrow/<int:book_id>')
def borrow_book(book_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    book = Book.query.get(book_id)
    if not book or book.stock <= 0:
        flash('Book not available', 'danger')
        return redirect(url_for('library'))
    
    # Check if already borrowed
    existing = Borrowing.query.filter_by(user_id=session['user_id'], book_id=book_id, status='borrowed').first()
    if existing:
        flash('You already have this book', 'warning')
        return redirect(url_for('library'))
    
    from datetime import datetime, timedelta
    due_date = datetime.now() + timedelta(days=7)
    
    borrowing = Borrowing(
        user_id=session['user_id'],
        book_id=book_id,
        due_date=due_date
    )
    
    book.stock -= 1
    db.session.add(borrowing)
    db.session.commit()
    
    flash('Book borrowed successfully!', 'success')
    return redirect(url_for('my_borrowings'))

@app.route('/my-borrowings')
def my_borrowings():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    borrowings = Borrowing.query.filter_by(user_id=session['user_id']).order_by(Borrowing.borrow_date.desc()).all()
    
    return render_template('my_borrowings.html', 
                         borrowings=borrowings,
                         school_name='Torres Capitol College',
                         school_short='TCC')

@app.route('/return/<int:borrowing_id>')
def return_book(borrowing_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    borrowing = Borrowing.query.get(borrowing_id)
    
    if not borrowing or borrowing.user_id != session['user_id']:
        flash('Invalid borrowing', 'danger')
        return redirect(url_for('my_borrowings'))
    
    from datetime import datetime
    borrowing.return_date = datetime.now()
    borrowing.status = 'returned'
    borrowing.book.stock += 1
    
    db.session.commit()
    
    flash('Book returned successfully!', 'success')
    return redirect(url_for('my_borrowings'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

# Admin routes
@app.route('/admin')
def admin():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session.get('role') != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    users = User.query.all()
    books = Book.query.all()
    borrowings = Borrowing.query.all()
    
    return render_template('admin.html', 
                         users=users, 
                         books=books, 
                         borrowings=borrowings,
                         school_name='Torres Capitol College',
                         school_short='TCC')

@app.route('/admin/add-book', methods=['GET', 'POST'])
def add_book():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        isbn = request.form.get('isbn')
        category = request.form.get('category')
        description = request.form.get('description')
        stock = int(request.form.get('stock', 1))
        

        # Handle image upload
        cover_image = None
        if 'cover_image' in request.files:
            file = request.files['cover_image']
            if file and file.filename:
                filename = secure_filename(file.filename)
                # Add timestamp to filename to avoid duplicates
                import time
                timestamp = int(time.time())
                new_filename = f"{timestamp}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))
                cover_image = new_filename
        
        # Handle ebook upload
        ebook_file = None
        if 'ebook_file' in request.files:
            file = request.files['ebook_file']
            if file and file.filename:
                filename = secure_filename(file.filename)
                import time
                timestamp = int(time.time())
                new_filename = f"{timestamp}_{filename}"
                # Save to uploads/ebooks subfolder
                os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'ebooks'), exist_ok=True)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'ebooks', new_filename))
                ebook_file = new_filename
        
        book = Book(
            title=title,
            author=author,
            isbn=isbn,
            category=category,
            description=description,
            stock=stock,
            cover_image=cover_image,
            ebook_file=ebook_file
        )
        
        db.session.add(book)
        db.session.commit()
        
        flash('Book added successfully!', 'success')
        return redirect(url_for('admin'))
    
    return render_template('add_book.html', school_name='Torres Capitol College', school_short='TCC')

@app.route('/admin/delete-book/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))
    
    book = Book.query.get_or_404(book_id)
    
    # Delete cover image if exists
    if book.cover_image:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], book.cover_image))
        except:
            pass
    
    # Delete ebook file if exists
    if book.ebook_file:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], 'ebooks', book.ebook_file))
        except:
            pass
    
    db.session.delete(book)
    db.session.commit()
    
    flash('Book deleted successfully!', 'success')
    return redirect(url_for('admin'))

# Initialize database
with app.app_context():
    db.create_all()

    # Add ebook_file column if it does not exist (migration for existing databases)
    try:
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('book')]
        if 'ebook_file' not in columns:
            db.session.execute(db.text('ALTER TABLE book ADD COLUMN ebook_file VARCHAR(200)'))
            db.session.commit()
    except:
        pass
    
    # Create admin user if not exists
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin = User(
            username='admin',
            email='admin@tcc.edu.ph',
            password=generate_password_hash('admin123'),
            full_name='Library Administrator',
            role='admin'
        )
        db.session.add(admin)
        
        # Add sample books
        sample_books = [
            Book(title='Introduction to Programming', author='John Smith', isbn='978-0-13-110362-7', category='Computer Science', description='A comprehensive guide to programming basics', stock=5),
            Book(title='Data Structures and Algorithms', author='Sarah Johnson', isbn='978-0-26-203384-8', category='Computer Science', description='Learn essential data structures and algorithms', stock=3),
            Book(title='Database Management Systems', author='Michael Chen', isbn='978-0-07-352332-3', category='Computer Science', description='Introduction to DBMS concepts', stock=4),
            Book(title='English Composition', author='Emily Brown', isbn='978-0-13-400455-3', category='Language', description='Advanced English writing skills', stock=6),
            Book(title='Filipino Kultura', author='Maria Garcia', isbn='978-971-08-4567-2', category='Social Studies', description='Introduction to Filipino culture and traditions', stock=4),
            Book(title='Mathematics Fundamentals', author='David Lee', isbn='978-0-321-12521-7', category='Mathematics', description='Basic mathematical concepts', stock=5),
            Book(title='Science and Technology', author='Rachel Green', isbn='978-0-393-91847-5', category='Science', description='Understanding modern science', stock=3),
            Book(title='Introduction to Criminology', author='James Wilson', isbn='978-1-305-97123-4', category='Criminology', description='Basic concepts in criminology', stock=4),
            Book(title='Business Management', author='Lisa Anderson', isbn='978-1-285-74126-5', category='Business', description='Principles of business management', stock=5),
            Book(title='Hotel Management', author='Robert Taylor', isbn='978-1-608-41768-5', category='Hospitality', description='Introduction to hotel operations', stock=3),
        ]
        
        for book in sample_books:
            db.session.add(book)
        
        db.session.commit()
        print("Database initialized with admin user and sample books!")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

@app.route('/read-ebook/<int:book_id>')
def read_ebook(book_id):
    book = Book.query.get_or_404(book_id)
    
    if not book.ebook_file:
        flash('No e-book file available for this book', 'warning')
        return redirect(url_for('library'))
    
    return render_template('reader.html', 
                       book=book,
                       school_name='Torres Capitol College',
                       school_short='TCC')