from SuperStarNew import SuperStar
import os

def checkAll(phone, pw,courseCount):
    ss = SuperStar(phone, pw)
    print('登录完成')
    print('开始获取所有课程信息')
    info = ss.get_all_courses_info(courseCount)
    content = '<!DOCTYPE html>'
    for course in info:
        if not ('works' in course.keys() and len(course['works']) > 0 or 'exams' in course.keys() and len(
                course['exams']) > 0):
            continue
        content += '<h1 style="font-size:30px">' + course['course'] + '：</h1>'
        if 'works' in course.keys() and len(course['works']) > 0:
            content += '<h2>作业</h2>'
            content += '<h3>-----------------------------</h3>'
            for work in course['works']:
                work_name = work['work']
                start_time = work['start_time']
                end_time = work['end_time']
                if work_name is not None:
                    content += '<h3>' + work_name + '</h3>'
                if start_time is not None:
                    content += '<h4>' + start_time + ' —— ' + end_time + '</h4>'
                content += '<br>'
            content += '<br>'
        if 'exams' in course.keys() and len(course['exams']) > 0:
            content += '<h2>考试</h2>'
            content += '<h3>-----------------------------</h3>'
            for exam in course['exams']:
                exam_name = exam['exam']
                start_time = exam['start_time']
                end_time = exam['end_time']
                if exam_name is not None:
                    content += '<h3>' + exam_name + '</h3>'
                if start_time is not None:
                    content += '<h4>' + start_time + ' —— ' + end_time + '</h4>'
                content += '<br>'
            content += '<br>'
    return content


def Main():
    phone=input('输入手机号')
    pw=input('输入密码')
    count=input('本学期课程数')
    tasks = checkAll(phone,pw,count)
    print('获取完成，写入html中')
    f = open(r"Tasks.html", 'w', encoding='utf-8')
    f.write(tasks)
    f.close()
    print('正在打开html文件')
    os.startfile(r"Tasks.html")


Main()
