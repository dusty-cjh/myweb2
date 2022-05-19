from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = 'name qq_number college grade college_student_number certificate ctime'.split()
    fields = 'name qq_number college grade college_student_number certificate'.split()

