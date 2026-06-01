from django.contrib import admin
from .models import Question, Choice, Submission
from .models import Course, Lesson, Instructor, Learner, Enrollment

class LessonInline(admin.StackedInline):
    model = Lesson
    extra = 5
    
class QuestionInline(admin.StackedInline):
    model = Question
    extra = 5
    
class ChoiceInline(admin.StackedInline):
    model = Choice
    extra = 5

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    inlines = [LessonInline]
    list_display = ('name', 'pub_date')
    list_filter = ['pub_date']
    search_fields = ['name', 'description']

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title']
    
@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'mode', 'date_enrolled')
    
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    inlines = [ChoiceInline]
    
admin.site.register(Instructor)
admin.site.register(Learner)
admin.site.register(Choice)
admin.site.register(Submission)