from django.shortcuts import render
from django.http import HttpResponseRedirect
# <HINT> Import any new Models here
from .models import Course, Enrollment, Submission, Choice
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.contrib.auth import login, logout, authenticate
import logging
# Get an instance of a logger
logger = logging.getLogger(__name__)
# Create your views here.


def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'onlinecourse/user_registration_bootstrap.html', context)
    elif request.method == 'POST':
        # Check if user exists
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            login(request, user)
            return redirect("onlinecourse:index")
        else:
            context['message'] = "User already exists."
            return render(request, 'onlinecourse/user_registration_bootstrap.html', context)


def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('onlinecourse:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'onlinecourse/user_login_bootstrap.html', context)
    else:
        return render(request, 'onlinecourse/user_login_bootstrap.html', context)


def logout_request(request):
    logout(request)
    return redirect('onlinecourse:index')


def check_if_enrolled(user, course):
    is_enrolled = False
    if user.id is not None:
        # Check if user enrolled
        num_results = Enrollment.objects.filter(user=user, course=course).count()
        if num_results > 0:
            is_enrolled = True
    return is_enrolled


# CourseListView
class CourseListView(generic.ListView):
    template_name = 'onlinecourse/course_list_bootstrap.html'
    context_object_name = 'course_list'

    def get_queryset(self):
        user = self.request.user
        courses = Course.objects.order_by('-total_enrollment')[:10]
        for course in courses:
            if user.is_authenticated:
                course.is_enrolled = check_if_enrolled(user, course)
        return courses


class CourseDetailView(generic.DetailView):
    model = Course
    template_name = 'onlinecourse/course_detail_bootstrap.html'


def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user

    is_enrolled = check_if_enrolled(user, course)
    if not is_enrolled and user.is_authenticated:
        # Create an enrollment
        Enrollment.objects.create(user=user, course=course, mode='honor')
        course.total_enrollment += 1
        course.save()

    return HttpResponseRedirect(reverse(viewname='onlinecourse:course_details', args=(course.id,)))


def submit(request, course_id):
    if request.method != "POST":
        return redirect('onlinecourse:course_details', pk=course_id)

    course = get_object_or_404(Course, pk=course_id)
    enrollment = get_object_or_404(
        Enrollment,
        user=request.user,
        course=course
    )
    
    submission = Submission.objects.create(enrollment=enrollment)
    choice_ids = extract_answers(request)
    choices = Choice.objects.filter(id__in=choice_ids)
    submission.choices.set(choices)
    submission_id = submission.id
    
    return HttpResponseRedirect(reverse(viewname='onlinecourse:exam_result', args=(course_id, submission_id,)))
    

# An example method to collect the selected choices from the exam form from the request object
def extract_answers(request):
   submitted_answers = []
   for key in request.POST:
       if key.startswith('question_'):
           value = request.POST[key]
           choice_id = int(value)
           submitted_answers.append(choice_id)
   return submitted_answers


def show_exam_result(request, course_id, submission_id):
    course = get_object_or_404(Course, id=course_id)
    submission = get_object_or_404(Submission, id=submission_id)
    choices = submission.choices.all()
    context = {}
    
    results = []
    
    total_score, total_obtained_score = 0, 0

    for question in course.questions.all():
        # Get the choice IDs submitted for this question
        selected_choice_ids = set(choices.filter(question=question).values_list('id', flat=True))
        
        correct_choice_ids = set(
            question.choices.filter(is_correct=True)
            .values_list('id', flat=True)
        )
        
        not_selected_choice_ids = correct_choice_ids - selected_choice_ids
        
        correct_choices = Choice.objects.filter(id__in=correct_choice_ids)
        selected_choices = Choice.objects.filter(id__in=selected_choice_ids)
        not_selected_choices = Choice.objects.filter(id__in=not_selected_choice_ids)
        
        result = {
            'question': question.question_text,
            'correct_answers': correct_choices,
            'selected_answers': selected_choices,
            'not_selected_answers': not_selected_choices,
        }
        
        # Use the question's is_get_score method to check if answer is correct
        if selected_choice_ids == correct_choice_ids:
            total_obtained_score += question.grade_point
            result['is_correct'] = True
        else:
            result['is_correct'] = False
        
        results.append(result)
            
        total_score += question.grade_point
            
    context['user'] = request.user
    context['course'] = course
    context['obtained_score'] = total_obtained_score
    context['total_score'] = total_score
    context['passed'] = total_obtained_score / total_score * 100 > 80 if total_score > 0 else False
    context['results'] = results

    return render(request, 'onlinecourse/exam_result_bootstrap.html', context)

