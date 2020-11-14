from SuperStarNew import SuperStar
import os

def checkAll(phone, pw,courseCount):
    ss = SuperStar(phone, pw)
    print('登录完成')
    print('开始获取所有课程信息')
    tasks = ss.getAllTasks(courseCount)
    content = ''
    for key in tasks.keys():
        content += '<h1 style="font-size:30px">' + key + '：</h1>'
        if 'works' in tasks[key].keys():
            content += '<h2>作业</h2>'
            content += '<h3>-----------------------------</h3>'
            for work in tasks[key]['works']:
                content += '<h3>' + work['work'] + '</h3>'
                content += '<h4>' + work['deadline'] + '</h4>'
            content += '<br>'
        if 'exams' in tasks[key].keys():
            content += '<h2>考试</h2>'
            content += '<h3>-----------------------------</h3>'
            for exam in tasks[key]['exams']:
                content += '<h3>' + exam['exam'] + '</h3>'
                content += '<h4>' + exam['deadline'] + '</h4>'
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
