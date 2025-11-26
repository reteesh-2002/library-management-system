from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("admin_login/", views.admin_login, name="admin_login"),
    path("student_login/", views.student_login, name="student_login"),
    path("logout/", views.user_logout, name="logout"),
    
    path("admin_dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("student_dashboard/", views.student_dashboard, name="student_dashboard"),
    
    path("add_book/", views.add_book, name="add_book"),
    path("view_books/", views.view_books, name="view_books"),
    path("edit_book/<int:book_id>/", views.edit_book, name="edit_book"),
    path("delete_book/<int:book_id>/", views.delete_book, name="delete_book"),
    
    path("add_student/", views.add_student, name="add_student"),
    path("view_students/", views.view_students, name="view_students"),
    path("edit_student/<int:student_id>/", views.edit_student, name="edit_student"),
    path("delete_student/<int:student_id>/", views.delete_student, name="delete_student"),
    
    path("issue_book/", views.issue_book, name="issue_book"),
    path("issued_books/", views.issued_books, name="issued_books"),
    path("return_book/<int:issue_id>/", views.return_book, name="return_book"),
    
    path("search_books/", views.search_books, name="search_books"),
    path("reserve_book/<int:book_id>/", views.reserve_book, name="reserve_book"),
]
