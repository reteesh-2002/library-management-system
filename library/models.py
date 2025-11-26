from django.db import models
from django.contrib.auth.models import User
from datetime import datetime, timedelta

class Book(models.Model):
    CATEGORY_CHOICES = [
        ('Fiction', 'Fiction'),
        ('Non-Fiction', 'Non-Fiction'),
        ('Science', 'Science'),
        ('Technology', 'Technology'),
        ('History', 'History'),
        ('Biography', 'Biography'),
        ('Self-Help', 'Self-Help'),
        ('Business', 'Business'),
        ('Arts', 'Arts'),
        ('Other', 'Other'),
    ]
    
    isbn = models.CharField(max_length=13, unique=True)
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    publisher = models.CharField(max_length=200)
    publication_date = models.DateField()
    total_copies = models.IntegerField(default=1)
    available_copies = models.IntegerField(default=1)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to='book_covers/', blank=True, null=True)
    added_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} by {self.author}"
    
    class Meta:
        ordering = ['-added_date']

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=20, unique=True)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    department = models.CharField(max_length=100)
    year = models.IntegerField()
    profile_picture = models.ImageField(upload_to='student_profiles/', blank=True, null=True)
    registration_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.student_id} - {self.user.get_full_name()}"
    
    class Meta:
        ordering = ['student_id']

class IssuedBook(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    issued_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_returned = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.book.title} - {self.student.student_id}"
    
    def calculate_fine(self):
        if not self.is_returned and datetime.now().date() > self.due_date:
            days_overdue = (datetime.now().date() - self.due_date).days
            self.fine_amount = days_overdue * 5
            self.save()
        return self.fine_amount
    
    class Meta:
        ordering = ['-issued_date']

class BookReservation(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    reservation_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.book.title} reserved by {self.student.student_id}"
    
    class Meta:
        ordering = ['-reservation_date']
