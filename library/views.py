from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from datetime import datetime, timedelta
from .models import Book, Student, IssuedBook, BookReservation
from django.contrib.auth.models import User
from django.core.paginator import Paginator

def index(request):
    total_books = Book.objects.count()
    total_students = Student.objects.count()
    issued_books = IssuedBook.objects.filter(is_returned=False).count()
    available_books = Book.objects.aggregate(total=Count('available_copies'))
    
    context = {
        'total_books': total_books,
        'total_students': total_students,
        'issued_books': issued_books,
        'available_books': available_books,
    }
    return render(request, 'library/index.html', context)

def admin_login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            if request.user.is_superuser:
                messages.success(request, "Login successful!")
                return redirect("/admin_dashboard")
            else:
                messages.error(request, "You are not an admin.")
                return redirect("/admin_login")
        else:
            messages.error(request, "Invalid Username or Password.")
            return render(request, "admin_login.html")
    return render(request, "admin_login.html")

def student_login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)

        if user is not None:
            try:
                student = Student.objects.get(user=user)
                if student.is_active:
                    login(request, user)
                    messages.success(request, "Login successful!")
                    return redirect("/student_dashboard")
                else:
                    messages.error(request, "Your account is inactive. Contact admin.")
                    return redirect("/student_login")
            except Student.DoesNotExist:
                messages.error(request, "Student profile not found.")
                return redirect("/student_login")
        else:
            messages.error(request, "Invalid Username or Password.")
            return render(request, "library/student_login.html")
    return render(request, "library/student_login.html")

def user_logout(request):
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect("/")

@login_required(login_url='/admin_login')
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect('/')
    
    total_books = Book.objects.count()
    total_students = Student.objects.count()
    issued_books = IssuedBook.objects.filter(is_returned=False).count()
    overdue_books = IssuedBook.objects.filter(is_returned=False, due_date__lt=datetime.now().date()).count()
    recent_books = Book.objects.all()[:5]
    recent_issues = IssuedBook.objects.filter(is_returned=False)[:5]
    
    context = {
        'total_books': total_books,
        'total_students': total_students,
        'issued_books': issued_books,
        'overdue_books': overdue_books,
        'recent_books': recent_books,
        'recent_issues': recent_issues,
    }
    return render(request, 'library/admin_dashboard.html', context)

@login_required(login_url='/student_login')
def student_dashboard(request):
    try:
        student = Student.objects.get(user=request.user)
        issued_books = IssuedBook.objects.filter(student=student, is_returned=False)
        book_history = IssuedBook.objects.filter(student=student, is_returned=True)[:5]
        reservations = BookReservation.objects.filter(student=student, is_active=True)
        total_fines = sum([book.calculate_fine() for book in issued_books])
        
        context = {
            'student': student,
            'issued_books': issued_books,
            'book_history': book_history,
            'reservations': reservations,
            'total_fines': total_fines,
        }
        return render(request, 'library/student_dashboard.html', context)
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('/')

@login_required(login_url='/admin_login')
def add_book(request):
    if not request.user.is_superuser:
        return redirect('/')
    
    if request.method == "POST":
        isbn = request.POST['isbn']
        title = request.POST['title']
        author = request.POST['author']
        category = request.POST['category']
        publisher = request.POST['publisher']
        publication_date = request.POST['publication_date']
        total_copies = request.POST['total_copies']
        description = request.POST.get('description', '')
        cover_image = request.FILES.get('cover_image')
        
        book = Book.objects.create(
            isbn=isbn,
            title=title,
            author=author,
            category=category,
            publisher=publisher,
            publication_date=publication_date,
            total_copies=total_copies,
            available_copies=total_copies,
            description=description,
            cover_image=cover_image
        )
        messages.success(request, f"Book '{title}' added successfully!")
        return redirect('/view_books')
    
    return render(request, 'library/add_book.html')

@login_required(login_url='/admin_login')
def view_books(request):
    if not request.user.is_superuser:
        return redirect('/')
    
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    
    books = Book.objects.all()
    
    if search_query:
        books = books.filter(
            Q(title__icontains=search_query) |
            Q(author__icontains=search_query) |
            Q(isbn__icontains=search_query)
        )
    
    if category_filter:
        books = books.filter(category=category_filter)
    
    paginator = Paginator(books, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = Book.CATEGORY_CHOICES
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'category_filter': category_filter,
        'categories': categories,
    }
    return render(request, 'library/view_books.html', context)

@login_required(login_url='/admin_login')
def edit_book(request, book_id):
    if not request.user.is_superuser:
        return redirect('/')
    
    book = get_object_or_404(Book, id=book_id)
    
    if request.method == "POST":
        book.isbn = request.POST['isbn']
        book.title = request.POST['title']
        book.author = request.POST['author']
        book.category = request.POST['category']
        book.publisher = request.POST['publisher']
        book.publication_date = request.POST['publication_date']
        book.total_copies = request.POST['total_copies']
        book.description = request.POST.get('description', '')
        
        if request.FILES.get('cover_image'):
            book.cover_image = request.FILES['cover_image']
        
        book.save()
        messages.success(request, f"Book '{book.title}' updated successfully!")
        return redirect('/view_books')
    
    return render(request, 'library/edit_book.html', {'book': book})

@login_required(login_url='/admin_login')
def delete_book(request, book_id):
    if not request.user.is_superuser:
        return redirect('/')
    
    book = get_object_or_404(Book, id=book_id)
    title = book.title
    book.delete()
    messages.success(request, f"Book '{title}' deleted successfully!")
    return redirect('/view_books')

@login_required(login_url='/admin_login')
def add_student(request):
    if not request.user.is_superuser:
        return redirect('/')
    
    if request.method == "POST":
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        student_id = request.POST['student_id']
        phone = request.POST['phone']
        address = request.POST['address']
        department = request.POST['department']
        year = request.POST['year']
        profile_picture = request.FILES.get('profile_picture')
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        student = Student.objects.create(
            user=user,
            student_id=student_id,
            phone=phone,
            address=address,
            department=department,
            year=year,
            profile_picture=profile_picture
        )
        
        messages.success(request, f"Student '{student_id}' added successfully!")
        return redirect('/view_students')
    
    return render(request, 'library/add_student.html')

@login_required(login_url='/admin_login')
def view_students(request):
    if not request.user.is_superuser:
        return redirect('/')
    
    search_query = request.GET.get('search', '')
    department_filter = request.GET.get('department', '')
    
    students = Student.objects.all()
    
    if search_query:
        students = students.filter(
            Q(student_id__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query)
        )
    
    if department_filter:
        students = students.filter(department=department_filter)
    
    paginator = Paginator(students, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    departments = Student.objects.values_list('department', flat=True).distinct()
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'department_filter': department_filter,
        'departments': departments,
    }
    return render(request, 'library/view_students.html', context)

@login_required(login_url='/admin_login')
def edit_student(request, student_id):
    if not request.user.is_superuser:
        return redirect('/')
    
    student = get_object_or_404(Student, id=student_id)
    
    if request.method == "POST":
        student.user.first_name = request.POST['first_name']
        student.user.last_name = request.POST['last_name']
        student.user.email = request.POST['email']
        student.user.save()
        
        student.phone = request.POST['phone']
        student.address = request.POST['address']
        student.department = request.POST['department']
        student.year = request.POST['year']
        student.is_active = request.POST.get('is_active') == 'on'
        
        if request.FILES.get('profile_picture'):
            student.profile_picture = request.FILES['profile_picture']
        
        student.save()
        messages.success(request, f"Student '{student.student_id}' updated successfully!")
        return redirect('/view_students')
    
    return render(request, 'library/edit_student.html', {'student': student})

@login_required(login_url='/admin_login')
def delete_student(request, student_id):
    if not request.user.is_superuser:
        return redirect('/')
    
    student = get_object_or_404(Student, id=student_id)
    student_id_num = student.student_id
    student.user.delete()
    messages.success(request, f"Student '{student_id_num}' deleted successfully!")
    return redirect('/view_students')

@login_required(login_url='/admin_login')
def issue_book(request):
    if not request.user.is_superuser:
        return redirect('/')
    
    if request.method == "POST":
        book_id = request.POST['book_id']
        student_id = request.POST['student_id']
        days = int(request.POST.get('days', 14))
        
        book = get_object_or_404(Book, id=book_id)
        student = get_object_or_404(Student, student_id=student_id)
        
        if book.available_copies > 0:
            due_date = datetime.now().date() + timedelta(days=days)
            
            issued_book = IssuedBook.objects.create(
                book=book,
                student=student,
                due_date=due_date
            )
            
            book.available_copies -= 1
            book.save()
            
            messages.success(request, f"Book '{book.title}' issued to {student.student_id} successfully!")
            return redirect('/issued_books')
        else:
            messages.error(request, "No copies available for this book!")
            return redirect('/issue_book')
    
    books = Book.objects.filter(available_copies__gt=0)
    students = Student.objects.filter(is_active=True)
    
    context = {
        'books': books,
        'students': students,
    }
    return render(request, 'library/issue_book.html', context)

@login_required(login_url='/admin_login')
def issued_books(request):
    if not request.user.is_superuser:
        return redirect('/')
    
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', 'active')
    
    if status_filter == 'active':
        issued_books_list = IssuedBook.objects.filter(is_returned=False)
    elif status_filter == 'returned':
        issued_books_list = IssuedBook.objects.filter(is_returned=True)
    else:
        issued_books_list = IssuedBook.objects.all()
    
    if search_query:
        issued_books_list = issued_books_list.filter(
            Q(book__title__icontains=search_query) |
            Q(student__student_id__icontains=search_query)
        )
    
    for issued_book in issued_books_list:
        if not issued_book.is_returned:
            issued_book.calculate_fine()
    
    paginator = Paginator(issued_books_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    return render(request, 'library/issued_books.html', context)

@login_required(login_url='/admin_login')
def return_book(request, issue_id):
    if not request.user.is_superuser:
        return redirect('/')
    
    issued_book = get_object_or_404(IssuedBook, id=issue_id)
    
    if not issued_book.is_returned:
        issued_book.is_returned = True
        issued_book.return_date = datetime.now().date()
        issued_book.calculate_fine()
        issued_book.save()
        
        book = issued_book.book
        book.available_copies += 1
        book.save()
        
        messages.success(request, f"Book '{book.title}' returned successfully!")
    else:
        messages.error(request, "This book has already been returned!")
    
    return redirect('/issued_books')

def search_books(request):
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    
    books = Book.objects.filter(available_copies__gt=0)
    
    if search_query:
        books = books.filter(
            Q(title__icontains=search_query) |
            Q(author__icontains=search_query) |
            Q(isbn__icontains=search_query)
        )
    
    if category_filter:
        books = books.filter(category=category_filter)
    
    paginator = Paginator(books, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = Book.CATEGORY_CHOICES
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'category_filter': category_filter,
        'categories': categories,
    }
    return render(request, 'library/search_books.html', context)

@login_required(login_url='/student_login')
def reserve_book(request, book_id):
    try:
        student = Student.objects.get(user=request.user)
        book = get_object_or_404(Book, id=book_id)
        
        existing_reservation = BookReservation.objects.filter(
            book=book,
            student=student,
            is_active=True
        ).exists()
        
        if existing_reservation:
            messages.error(request, "You have already reserved this book!")
        else:
            expiry_date = datetime.now() + timedelta(days=3)
            BookReservation.objects.create(
                book=book,
                student=student,
                expiry_date=expiry_date
            )
            messages.success(request, f"Book '{book.title}' reserved successfully!")
        
        return redirect('/search_books')
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('/')