# SuperStarInfoFetch
 超星学习通作业考试获取

# SuperStar
以手机号（账号）和密码来实例化类。

# get_possible_course_full_names
输入课程名关键字，返回匹配到的所有可能课程全名。大小写不敏感。

# get_course_info
输入课程名关键词或课程页面Url，返回该课程（或匹配到所有名字匹配的课程）所有未完成且未到期的作业、考试。不包含章节任务点。
## 参数
string：字符串。可以是课程名或课程页面Url
get_works = True, 默认开启，爬取作业
get_exams = True, 默认开启，爬取考试
get_stats = False, 默认关闭，爬取课程统计信息
get_timestamp = False, 默认关闭，在爬取作业和考试时获取其开始、结束时间
### 新版学习通只能进入每个任务的单独页面才能获取到开始和结束时间信息。若不允许查看的任务也就无法获取时间戳。该选项开启后比较耗时。
## 返回值 
{'course':课程名称,'works':{作业名，剩余时间，是否过期，开始时间，结束时间，作业状态},'exams':{同作业},'stats':{统计数据}}
### 参考works/exams的键名
'work','status','validity','start_time','end_time','time_left'
### 参考stats的键名
'chapter_task_finished','chapater_task_total','chapter_task_progress_rank','chapter_study_times','course_credits','highest_credits','highest_credits_student','check_in_attendance','check_in_initiated','check_in_percentage','chapter_test_finished','chapter_test_total','works_finished','works_total','works_average_score','discussion_posts_count','discussion_replies_count','discussion_likes_acquired','exams_finished','exams_total'


# get_all_courses_info
输入课程数，从上至下（越后添加的课程越靠前）返回所有课程的所有未完成且未到期的所有作业、考试。不包含章节任务点。
## 参数
courseCount：课程数目。从顶部开始爬取的课程数量。默认为100，若课程数少于100会自动停止。
get_works = True, 默认开启，爬取作业
get_exams = True, 默认开启，爬取考试
get_stats = False, 默认关闭，爬取课程统计信息
get_timestamp = False, 默认关闭，在爬取作业和考试时获取其开始、结束时间

# send_mail
从指定发件邮箱发邮件到指定收件邮箱
## 参数
发件邮箱
发件邮箱的smtp服务器地址
发件邮箱的密码
收件邮箱
信息（字符串）
信息类型（默认纯文本，可选html）
邮件标题

# 属性列表
##标有#exclude意味着列表中的值在相应地方被匹配到后，该作业/考试将会被忽略
##标有#include意味着列表中的值在相应地方被匹配到后，该作业/考试才会被收集
##exclude优先级更高。
self.arg_list_course_name = []#exclude

self.arg_list_course_preview = ['已开启结课模式']#exclude

self.arg_list_teacher_name = []#exclude

self.arg_list_work_status=['未交']#include    enum:['未交','已完成','待批阅']

self.arg_list_exam_status=['未开始', '待做']#include     enum:['未开始', '待做','已完成','已过期']

self.arg_bool_task_validity = True
##新版学习通 过期与否作业都显示未交。故除了本就存在的任务状态，添加了一个validity判断。True代表只收集未过期的任务。False代表只收集过期的任务。None代表无视任务是否过期。



不知道学习通给不同学校提供的网页是不是一样。如果不一样那可能有的学校用不了。
初衷是写给自己用的，写个脚本计划任务检查新作业并发到自己邮箱来对付一个悄悄咪咪布置作业留几个小时的老师。
能找到这个的都是好孩子吧hhh