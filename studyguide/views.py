from django.shortcuts import render
from OsirisApi import OsirisApi
from osiristue.decorators import render_async_and_cache
import urllib.parse
from math import floor
import channels

def getCourses(courses, path):
    if type(courses) != list:
        return []
    API = OsirisApi()
    coursesinfo = []
    for i, course in enumerate(courses):
        info = API.course(course)
        if info is not None:
            for c in info:
                staff = c.pop('responsiblestaff')
                owner = c.pop('owner')
                c['teacher'] = staff['name']
                c['teachermail'] = staff['email']
                c['group'] = owner['group']
                coursesinfo.append(c)
            channels.Group('render_page_{}'.format(path.replace('&', '_'))).send({'text' : str(floor(((i + 1) / len(courses)) * 100))})

    return coursesinfo

def chooseFaculty(request):
    API = OsirisApi()
    return render(request, 'choosefaculty.html', {
        'faculties' : API.faculties()
    })

@render_async_and_cache
def listBC(request, faculty):
    faculty = urllib.parse.unquote(faculty)
    API = OsirisApi()
    return render(request, 'listBC.html', {
        'faculty' : [f[1] for f in API.faculties() if faculty == f[0]][0],
        'type' : 'Bachelor College',
        'courses' : getCourses(API.facultyCoursesType(faculty, 'BC'), urllib.parse.unquote(request.path).replace('/','_').replace('&','_'))
    })

@render_async_and_cache
def listGS(request, faculty):
    faculty = urllib.parse.unquote(faculty)
    API = OsirisApi()
    return render(request, 'listGS.html', {
        'faculty' : [f[1] for f in API.faculties() if faculty == f[0]][0],
        'type' : 'Graduate School',
        'courses' : getCourses(API.facultyCoursesType(faculty, 'GS'), urllib.parse.unquote(request.path).replace('/','_').replace('&','_'))
    })