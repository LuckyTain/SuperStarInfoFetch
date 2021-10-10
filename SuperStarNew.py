import base64
import re
import smtplib
import time
from email.header import Header
from email.mime.text import MIMEText
import requests
import urllib.parse
import json
from bs4 import BeautifulSoup as bs
from ping3 import ping


class SuperStar:

    def __init__(self,Phone,Pwd):
        self.__Phone=Phone
        self.__Pwd=str(base64.encodebytes(bytes(Pwd.encode('utf-8')))).lstrip(r"b'").rstrip(r"\n'")

        self.url_dict = {'login_post_url': r"https://passport2.chaoxing.com/fanyalogin",
                         'course_list_url': r'http://mooc1-1.chaoxing.com/visit/courselistdata',
                         'course_detail_url': r'https://mooc1-1.chaoxing.com/visit/stucoursemiddle',
                         'works_list_url': r'https://mooc1.chaoxing.com/mooc2/work/list',
                         'exams_list_url': r'https://mooc1.chaoxing.com/mooc2/exam/exam-list',
                         'work_view_url': r'https://mooc1.chaoxing.com/mooc2/work/view',  #finished works
                         'work_preview_url': r'https://mooc1.chaoxing.com/mooc2/work/preview',  #expired works, currently deprecated
                         'work_do_work_url': r'https://mooc1.chaoxing.com/mooc2/work/dowork',  #ongoing works, currently deprecated
                         'exam_revision_url': r'https://mooc1.chaoxing.com/exam/test/reVersionPaperMarkContentNew',  #finished exams
                         'exam_look_url': r'https://mooc1.chaoxing.com/exam/lookPaper',  #expired exams
                         'stats_index_url': r'https://stat2-ans.chaoxing.com/study-data/index',  #stats index
                         'stats_sign_url': r'https://stat2-ans.chaoxing.com/study-data/sign',  #sign data
                         'stats_credits_url': r'https://stat2-ans.chaoxing.com/study-data/point'  #course credits
                         }

        self.required_attrs_dict = {
                                    'course_detail_url': ['courseid','clazzid','vc','cpi','ismooc2'],
                                    'works_list_url': ['courseid','classid','cpi','enc'],
                                    'exams_list_url': ['enc','openc','courseid','clazzid','cpi','ut'],
                                    'work_view_url': ['courseid','classid','cpi','workId','answerId','enc'],
                                    'work_preview_url': ['courseid','classid','cpi','workId','enc'],
                                    'work_do_work_url': ['courseid','classid','cpi','workId','answerId','enc'],
                                    'exam_revision_url': ['courseId','classId','cpi','id','newMooc','ut','openc'],
                                    'exam_look_url': ['courseid','classid','paperId','examRelationId','newMooc','ut','openc','enc'],
                                    'stats_index_url': ['courseid','clazzid','cpi','ut'],
                                    'stats_sign_url': ['courseid','clazzid','cpi','ut'],
                                    'stats_credits_url': ['courseid','clazzid','cpi','ut']}


        self.attrs_names_dict = {'courseid,courseId,enc-courseId': 'courseid',
                                 'classid,clazzid,classId,enc-clazzId': 'classid',
                                 'ut,heardUt,enc-ut' : 'heardUt',
                                 'personid,enc-cpi' : 'cpi'
                                 }


        self.data_dict = {'login_data': {"fid": "1971", "uname": self.__Phone,
            "password": self.__Pwd, 'refer': 'http%3A%2F%2Fi.mooc.chaoxing.com', 't': 'true'},
                          'request_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36'}
                          }

        #data to get work list
        self.__courselistdata={
            'courseType': 1,
            'courseFolderId': 0,
            'courseFolderSize': 0
        }
        self.arg_list_course_name = []#exclude
        self.arg_list_course_preview = ['已开启结课模式']#exclude
        self.arg_list_teacher_name = []#exclude
        self.arg_list_work_status=['未交']#include    enum:['未交','已完成','待批阅']
        self.arg_list_exam_status=['未开始', '待做']#include     enum:['未开始', '待做','已完成','已过期']
        self.arg_bool_task_validity = True
        #self.arg_list_timeRestriction=[time.strftime("%Y",time.localtime())]#include
        self.pingAddressList=["passport2.chaoxing.com", 'i.chaoxing.com']
        self.__requests_operation_count=0
        self.__session_refresh_threshold=500#32
        self.__pauseTime=0.5
        self.__retry_times = 3
        self.__login()
        self.__courses_list_page = self.__post(self.url_dict['course_list_url'], headers=self.data_dict['request_headers'], data = self.__courselistdata)
        self.__courses_list_page_soup = bs(self.__courses_list_page.text, "html.parser")

        
    def __post(self,url,data=None,json=None,headers = None):
        '''
        Wrapped version of post. Count operations to induce session refresh in order to avoid authentication etc.
        :param url:
        :param data:
        :param json:
        :param headers:
        :return:
        '''
        if not self.__requests_operation_count == 0 and self.__requests_operation_count % self.__session_refresh_threshold == 0:
            self.__refresh_session()
        self.__requests_operation_count+=1
        return self.__s.post(url,data,json,headers = headers)

    def __get(self, url, data=None, json=None, headers=None):
        '''
        Wrapped version of get. Count operations to induce session refresh in order to avoid authentication etc.
        Auto retry when asked for authentication.
        :param url:
        :param data:
        :param json:
        :param headers:
        :return:
        '''
        if not self.__requests_operation_count == 0 and self.__requests_operation_count % self.__session_refresh_threshold == 0:
            self.__refresh_session()
        for i in range(self.__retry_times):
            resp = self.__s.get(url, data = data,json = json,headers=headers)
            self.__requests_operation_count += 1
            if self.__handle_exception(resp.text):
                break
            if i == self.__retry_times - 1:
                raise Exception('maximum retry reached')

        return resp

    def __networkTest(self):
        '''
        Throws exception when no connection, print message when connection quality is bad.
        :return:
        '''
        results=[]
        for add in self.pingAddressList:
            results.append(ping(add))
        if all(result is None for result in results):
            raise Exception('No Internet connection')
        elif any(result is None or result>0.1 for result in results):
            print('Bad network connection, could take some time')
        return True


    def __login(self):
        '''
        Log in to SuperStar and save the session.
        :return:
        '''
        self.__networkTest()
        self.__s=requests.session()
        self.__s.post(self.url_dict['login_post_url'], headers=self.data_dict['request_headers'], data=self.data_dict['login_data'])
        time.sleep(self.__pauseTime)

    def __get_course_detail_page_url_by_name(self, courseName):
        '''
        Get course detail page url by course name. If got multiple matches, returns the first hit, conventionally the latest course.
        :param courseName: Allow partial course name, case insensitive.
        :return: Url of the first course name match.
        '''

        try:
            target_course_url = self.__courses_list_page_soup.find('span', text=re.compile(courseName,re.I))\
                .find_parent('li', id=re.compile('course')).find(class_='course-cover').a.attrs['href']

            #assemble url
            # target_course_url = self.__courses_list_page_soup.find('span', text=re.compile(courseName, re.I)) \
            #     .find_parent('li', id=re.compile('course')).find(class_='course-cover').a.attrs['href']
            #
            # target_course_url = self.__modify_url(target_course_url,self.required_attrs_dict['course_detail_url'],self.__get_params_from_url(target_course_url))


        except:
            raise Exception('No such course found!')

        return target_course_url


    def __get_main_attrs(self,source_page_soup):
        '''
        Get some universal attributes from either course detail page or work/exam list page
        :param source_page_soup:
        :return:
        '''
        main_attrs_dict = {}

        for item in source_page_soup.find_all('input', type='hidden'):
            try:
                main_attrs_dict[self.__standardize_attr_name(item.attrs['id'])] = item.attrs['value']
            except:
                continue

        return main_attrs_dict

    def __get_attrs_from_url(self, url):
        return dict(urllib.parse.parse_qsl(urllib.parse.urlparse(url).query))

    def __specify_attrs_manually(self, target_url_name, source_soup =None):
        #everything here is manually defined. just in case more urls need to be synthesized in the future.
        attrs_dict = {}

        if target_url_name == 'works_list_url':
            attrs_dict['enc'] = self.__get_attrs_from_url(source_soup.find(title ='作业').attrs['data-url'])['enc']

        elif target_url_name == 'exams_list_url':
            url_has_attrs = ['enc','openc']
            parsed_attrs_dict = self.__get_attrs_from_url(source_soup.find(title='考试').attrs['data-url'])

            for attr in url_has_attrs:
                attrs_dict[self.__standardize_attr_name(attr)] = parsed_attrs_dict[attr]

        elif target_url_name == 'exam_revision_url':
            attrs_dict['id'] = re.search('(\\d+)',source_soup.find(onclick = re.compile('.*')).attrs['onclick']).group()
            attrs_dict['newMooc'] = 'true'
            attrs_dict['p'] = '1'
            attrs_dict['ut'] = 's'

        elif target_url_name == 'stats_index_url':
            attrs_dict['ut'] = 's'


        return attrs_dict


    def __standardize_attr_name(self,attr_name):
        for match_names in self.attrs_names_dict:
            if attr_name in match_names.split(','):
                return self.attrs_names_dict[match_names]

        return attr_name

    def __modify_url(self,url,required_attrs_list,*attrs_dicts):

        # subsequent attrs dicts will overwrite the old ones. example order: main_attrs, manual_attrs
        attrs_dict = {}
        for dict in attrs_dicts:
            for item in dict.items():
                for attrs_names in self.attrs_names_dict:
                    if item[0] in attrs_names.split(','):
                        name = self.attrs_names_dict[attrs_names]
                        break

                else:
                    name = item[0]
                attrs_dict[name] = item[1]



        parsed_url = urllib.parse.urlparse(url)
        query_dict = {}
        for required_attr in required_attrs_list:
            query_dict[required_attr] = attrs_dict[self.__standardize_attr_name(required_attr)]
        assembled_url = urllib.parse.urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path,
                                                 parsed_url.params, urllib.parse.urlencode(query_dict),
                                                 parsed_url.fragment))
        return assembled_url

    def __get_sections_urls(self, string, works = False, exams = False, stats = False):
        '''
        Get urls from sections of a course detail page.
        :param string: Course name or course detail page url. Allow partial name, case insensitive.
        :param works: Whether get works entry page url.
        :param exams: Whether get exams entry page url.
        :param stats: Whether get stats entry page url.
        :return:
        '''
        if 'http' in string:
            course_detail_page_url=string
        else:
            course_detail_page_url=self.__get_course_detail_page_url_by_name(string)

        course_detail = self.__get(course_detail_page_url, headers=self.data_dict['request_headers'])
        course_detail = bs(course_detail.text, 'html.parser')
        result_dict = {}

        if works:
            url_name = 'data-url'
            entry_url = course_detail.find('a', title='作业').attrs[url_name]

            # assemble url
            # entry_url = self.__modify_url(entry_url, self.required_attrs_dict['works_list_url'], self.__get_main_attrs(course_detail), self.__specify_attrs_manually('works_list_url', course_detail))

            result_dict['works'] = entry_url

        if exams:
            url_name = 'exams_list_url'
            entry_url = course_detail.find('a', title='考试').attrs['data-url']

            # assemble url
            entry_url = self.__modify_url(entry_url, self.required_attrs_dict[url_name],
                                          self.__get_main_attrs(course_detail),
                                          self.__specify_attrs_manually(url_name, course_detail))

            result_dict['exams'] = entry_url

        if stats:
            url_name = 'stats_index_url'

            # assemble url
            entry_url = self.__modify_url(self.url_dict[url_name],self.required_attrs_dict[url_name],
                                          self.__get_main_attrs(course_detail),self.__specify_attrs_manually(url_name))

            result_dict['stats'] = entry_url

        return result_dict

    def __get_task_timestamps(self, task_url, task_type):
        task_page = self.__get(task_url, headers=self.data_dict['request_headers'])
        task_page = bs(task_page.text, 'html.parser')
        try:
            if task_type == 'work':
                time_stamps = list(
                    time.text for time in task_page.find(text=re.compile('作答时间', re.I)).parent.find_all('em'))
            elif task_type == 'exam':
                time_stamps = list(
                    time.text for time in task_page.find(text=re.compile('考试时间', re.I)).parent.find_all('em'))
            elif task_type == 'exchange':
                time_stamps = list(
                    time.text for time in task_page.find(text=re.compile('互评时间', re.I)).parent.find_all('em'))
        except:
            time_stamps = [None,None]
        return time_stamps


    def __determine_task_base_url_type(self,task_soup):
        try:
            task_info = task_soup.find(onclick = re.compile('.*')).attrs['onclick']
        except:
            task_info = task_soup.parent.find(onclick=re.compile('.*')).attrs['onclick']
        if re.compile('notallow',re.I).search(task_info):
            #not allowed to review
            return False
        elif 'goTask' in task_info:
            #work
            return 'work_view_url'
        elif 'viewPaper' in task_info:
            #exam
            status = task_soup.find('p', class_='status').text.strip()
            if status == '已完成':
                return 'exam_revision_url'
            elif status == '已过期':
                return 'exam_look_url'

    def __task_is_valid(self,task_soup):
        try:
            invalid = task_soup.find('div', class_=re.compile('icon-.+-g',re.I)).parent
            return False
        except:
            return True

    def __task_is_exchanged(self,task_soup):
        try:
            exchange = task_soup.find(class_=re.compile('icon-hp',re.I)).parent
            return True
        except:
            return False


    def __get_works_of_single_page(self, page_url, get_timestamp = True):
        '''
        Get the works from a single work list page.
        :param page_url: Work list page url.
        :param get_timestamp: True to get task start and end time.
        :return: Works information.
        '''
        works_of_page=[]

        works_list_page = self.__get(page_url, headers=self.data_dict['request_headers'])
        works_list_page_soup = bs(works_list_page.text, "html.parser")

        try:
            all_works= list(works_list_page_soup.find("div", class_="bottomList").ul.find_all('li'))
        except:
            all_works = []

        for work in all_works:
            work_name = work.find('p',class_ = 'overHidden2 fl').text
            work_status = work.find('p',class_ = 'status').text.strip()

            # whether work is still valid
            valid = self.__task_is_valid(work)
            if self.arg_bool_task_validity is not None:
                if not valid == self.arg_bool_task_validity:
                    continue

            #whether is exchanged work
            if self.__task_is_exchanged(work):
                work_type = 'exchanged'
            else:
                work_type = 'work'

            #try to get time left
            try:
                work_time_left = work.find('div',class_ = 'time notOver').text.strip()
            except:
                work_time_left = None

            if get_timestamp:
                if not valid and work_status == '未交':  #if never finished, timestamp will not be displayed.
                    timestamps = [None, None]
                else:
                    base_url_type = self.__determine_task_base_url_type(work)
                    if base_url_type:
                        work_detail_page_url = work.attrs['data']
                        timestamps = self.__get_task_timestamps(work_detail_page_url,work_type)
                    else:
                        timestamps = [None, None]
            else:
                timestamps = [None,None]

            if all(arg not in work_status for arg in self.arg_list_work_status):
                continue

            dict = {'work': work_name,
                    'status': work_status,
                    'validity': valid,
                    'start_time': timestamps[0],
                    'end_time': timestamps[1],
                    'time_left': work_time_left}


            works_of_page.append(dict)

        try:
            current_page = re.search(r'(\d)',re.search('(nowPage.*?,)',works_list_page.text).group()).group()
            total_page_count = re.search(r'(\d)',re.search('(pageNum.*?,)',works_list_page.text).group()).group()

            if current_page < total_page_count:
                next_page_exists = True
            else:
                next_page_exists = False
        except:
            next_page_exists = False

        return works_of_page,next_page_exists


    def __get_exams_of_single_page(self, page_url,get_timestamp = True):
        '''
        Get the exams from a single exam list page.
        :param page_url: Exam list page url.
        :param get_timestamp: True to get task start and end time.
        :return: Exams information.
        '''
        exams_of_page = []

        exams_list_page = self.__s.get(page_url, headers=self.data_dict['request_headers'])
        exams_list_page_soup = bs(exams_list_page.text, "html.parser")


        try:
            all_exams = list(exams_list_page_soup.find("div", class_="bottomList").ul.find_all('li'))
        except:
            all_exams = []

        for exam in all_exams:
            exam_name = exam.find('p', class_='overHidden2 fl').text
            exam_status = exam.find('p', class_='status').text.strip()

            # whether work is still valid
            valid = self.__task_is_valid(exam)
            if self.arg_bool_task_validity is not None:
                if not valid == self.arg_bool_task_validity:
                    continue

            # try to get time left
            try:
                exam_time_left = exam.find('div', class_='time notOver').text.strip()
            except:
                exam_time_left = None

            if get_timestamp:
                base_url_type = self.__determine_task_base_url_type(exam)
                if base_url_type:
                    exam_detail_page_url = self.__modify_url(self.url_dict[base_url_type],self.required_attrs_dict[base_url_type],self.__get_main_attrs(exams_list_page_soup),self.__specify_attrs_manually(base_url_type,exam))
                    timestamps = self.__get_task_timestamps(exam_detail_page_url,'exam')
                else:
                    timestamps = [None, None]
            else:
                timestamps = [None,None]

            if all(arg not in exam_status for arg in self.arg_list_exam_status):
                continue

            dict = {'exam': exam_name,
                    'status': exam_status,
                    'validity': valid,
                    'start_time': timestamps[0],
                    'end_time': timestamps[1],
                    'time_left': exam_time_left}

            exams_of_page.append(dict)

        try:
            current_page = re.search(r'(\d)', re.search('(nowPage.*?,)', exams_list_page.text).group()).group()
            total_page_count = re.search(r'(\d)', re.search('(pageNum.*?,)', exams_list_page.text).group()).group()

            if current_page < total_page_count:
                next_page_exists = True
            else:
                next_page_exists = False
        except:
            next_page_exists = False

        return exams_of_page, next_page_exists


    def __get_stats_of_course(self, page_url):
        stats_dict = {}
        stats_index_page_soup = bs(self.__get(page_url).text,"html.parser")

        #initialize
        keys = ['chapter_task_finished','chapater_task_total','chapter_task_progress_rank','chapter_study_times',
                'course_credits','highest_credits','highest_credits_student','check_in_attendance',
                'check_in_initiated','check_in_percentage','chapter_test_finished','chapter_test_total',
                'works_finished','works_total','works_average_score','discussion_posts_count',
                'discussion_replies_count','discussion_likes_acquired','exams_finished','exams_total']

        for key in keys:
            stats_dict[key] = None

        #chapter task
        try:
            chapter_task_section = stats_index_page_soup.find('h2',text = '章节任务点').parent.parent
        except:
            pass
        try:
            stats_dict['chapter_task_finished'],stats_dict['chapater_task_total'] =chapter_task_section.find('p',text = '完成进度').parent.find('h2').text.rstrip('个').strip().split('/')
        except:
            pass
        try:
            stats_dict['chapter_task_progress_rank'] = chapter_task_section.find('p',text = '当前排名').parent.find('h2').text.strip().rstrip('名')
        except:
            pass
        try:
            stats_dict['chapter_task_finish_percentage'] = chapter_task_section.find('p',text = '完成率').parent.find('h2').text.strip()
        except:
            pass

        #chapter study times
        try:
            stats_dict['chapter_study_times'] = stats_index_page_soup.find('h2',text = '章节学习次数').parent.parent.find\
                ('div',class_ = 'single-list').find('h2').text.rstrip('次').strip()
        except:
            pass

        #course credit
        credits_url_name = 'stats_credits_url'
        try:
            credits_data_dict = json.loads(self.__post(self.__modify_url(self.url_dict[credits_url_name],self.required_attrs_dict[credits_url_name],self.__get_main_attrs(stats_index_page_soup))).text)
        except:
            pass
        try:
            stats_dict['course_credits'] = credits_data_dict['ponits']
        except:
            pass
        try:
            stats_dict['highest_credits'] = credits_data_dict['maxPonits']['ponits']
        except:
            pass
        try:
            stats_dict['highest_credits_student'] = credits_data_dict['maxPonits']['username']
        except:
            pass

        #check in
        sign_url_name = 'stats_sign_url'
        try:
            sign_data_dict = json.loads(self.__post(self.__modify_url(self.url_dict[sign_url_name],self.required_attrs_dict[sign_url_name],self.__get_main_attrs(stats_index_page_soup))).text)
        except:
            pass
        try:
            stats_dict['check_in_attendance'], stats_dict['check_in_initiated'] = sign_data_dict['attendanceCount'],sign_data_dict['allCount']
        except:
            pass
        try:
            if sign_data_dict['allCount'] > 0:
                stats_dict['check_in_percentage'] = '%s%%'%(100 * sign_data_dict['attendanceCount'] / sign_data_dict['allCount'])
            else:
                stats_dict['check_in_percentage'] = None
        except:
            pass

        #chapter test
        try:
            course_chapter_test_section = stats_index_page_soup.find('h2',text = '章节测验').parent.parent
        except:
            pass
        try:
            stats_dict['chapter_test_finished'], stats_dict['chapter_test_total'] = course_chapter_test_section.\
                find('span',text = '个').parent.text.rstrip('个').strip().split('/')
        except:
            pass
        try:
            stats_dict['chapter_test_average_score'] = course_chapter_test_section.find('span',text = '分').previousSibling.text
        except:
            pass

        #works
        try:
            course_works_section = stats_index_page_soup.find('h2',text = '作业').parent.parent
        except:
            pass
        try:
            stats_dict['works_finished'], stats_dict['works_total'] = course_works_section.find('span',text = '个').parent.text.rstrip('个').strip().split('/')
        except:
            pass
        try:
            stats_dict['works_average_score'] = course_works_section.find('span',text = '分').previousSibling.text
        except:
            pass

        #discussion
        try:
            course_discussion_section = stats_index_page_soup.find('h2',text = '讨论').parent.parent
        except:
            pass
        try:
            stats_dict['discussion_posts_count'] = course_discussion_section.find('p',text = '发帖').parent.find('h2').find('span').text
        except:
            pass
        try:
            stats_dict['discussion_replies_count'] = course_discussion_section.find('p',text = '回帖').parent.find('h2').find('span').text
        except:
            pass
        try:
            stats_dict['discussion_likes_acquired'] = course_discussion_section.find('p',text='获赞数').parent.find('h2').find('span').text
        except:
            pass

        #exams
        try:
            course_exams_section = stats_index_page_soup.find('h2',text = '在线考试').parent.parent
        except:
            pass
        try:
            stats_dict['exams_finished'], stats_dict['exams_total'] = course_exams_section.find('span',text = '个').parent.text.strip().rstrip('个').strip().split('/')
        except:
            pass

        return stats_dict


    def __get_all_courses_element(self):
        '''
        Get courses page elements.
        :return: Courses page elements as a list.
        '''

        return self.__courses_list_page_soup.find(class_='course-list').find_all('li', class_='course clearfix')

    def __get_all_courses_detail_page_url(self):
        '''
        Get all courses detail page url according to the argument lists set.
        :return: Courses detail page urls.
        '''
        all_courses_elements=self.__get_all_courses_element()

        if len(all_courses_elements) == 0:
            raise Exception('Obtaining all courses url error')

        url_list = []

        for course in all_courses_elements:
            ui_open_review = course.find(class_='course-cover').find(class_='ui-open-review')

            if ui_open_review is not None:
                if any(arg in ui_open_review.text for arg in self.arg_list_course_preview):
                    continue

            course_info = course.find(class_='course-info')
            course_name = course_info.find(class_='course-name overHidden2').text
            teacher_name = course_info.find(class_ = 'line2').text

            if any(arg in course_name for arg in self.arg_list_course_name) or any(arg in teacher_name for arg in self.arg_list_teacher_name):
                continue

            # 未开课课程没有课程连接
            if course.find(class_='course-cover').a is None:
                continue

            course_detail_page_url = course.find(class_='course-cover').a.attrs['href']

            url_list.append(course_detail_page_url)

        return url_list

    def __refresh_session(self):
        '''
        Refresh session to avoid authentication.
        :return:
        '''
        time.sleep(self.__pauseTime)
        self.__login()
        self.__requests_operation_count=0
        print('session refreshed')


    def __handle_exception(self, text):
        '''
        Refresh session if asked for authentication.
        :param text: Response.text
        :return: True for no exception happened, False for exception handled, former operation is failed and is needed to
        be performed again.
        '''
        if '您的操作出现异常，请输入验证码' in text:
            print('exception handled')
            self.__refresh_session()
            return False
        else:
            return True

    def get_possible_course_full_names(self, string):
        '''
        Get full names of courses.
        :param string:Partial course name or course detail page url.
        :return:Possible courses full names.
        '''
        if 'http' in string:
            course_id = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(string).query))['courseid']
            course_name = self.__courses_list_page_soup.find('li',courseid = course_id)\
                .find('span',class_='course-name overHidden2').text
            return [course_name]
        else:
            results = []
            for span in self.__courses_list_page_soup.find_all('span',class_='course-name overHidden2'
                                                             ,text = re.compile(string,re.I)):
                results.append(span.text)

            return results

    def get_course_info(self, string, get_works = True, get_exams = True, get_stats = False, get_timestamp = False):
        '''
        Get information about the specified course.
        :param string: Course name or course detail page url. Allow partial name, case insensitive.
        :param get_works: Whether get works info.
        :param get_exams: Whether get exams info.
        :param get_stats: Whether get stats info.
        :param get_timestamp: Whether to include timestamps in works and exams.
        :return: Dictionary of all the information collected.
        '''
        work_url,exam_url,stats_url = self.__get_sections_urls(string, True, True, True).values()
        name = self.get_possible_course_full_names(string)[0]
        print('scraping:\t'+name)
        result_dict = {'course': name}

        if get_works:
            works_of_course = []
            current_page = 0
            next_page_exists = True

            while (next_page_exists):
                current_page += 1
                works_from_page, next_page_exists = self.__get_works_of_single_page(work_url, get_timestamp)
                works_of_course.extend(works_from_page)

                if not next_page_exists:
                    break

                if current_page == 1:
                    work_url += '&status=0&pageNum=%d' % (current_page + 1)
                else:
                    work_url = work_url.replace('pageNum=%d' % current_page, '&pageNum=%d&' % (current_page + 1), 1)

            result_dict['works'] = works_of_course

        if get_exams:
            exams_of_course = []
            current_page = 0
            next_page_exists = True

            while (next_page_exists):
                current_page += 1
                exams_from_page, next_page_exists = self.__get_exams_of_single_page(exam_url, get_timestamp)
                exams_of_course.extend(exams_from_page)

                if not next_page_exists:
                    break

                if current_page == 1:
                    exam_url += '&status=0&pageNum=%d' % (current_page + 1)
                else:
                    exam_url = exam_url.replace('pageNum=%d' % current_page, '&pageNum=%d&' % (current_page + 1), 1)

            result_dict['exams'] = exams_of_course

        if get_stats:
            result_dict['stats'] = self.__get_stats_of_course(stats_url)

        return result_dict


    def get_all_courses_info(self, courseCount=100, get_works=True, get_exams=True, get_stats = False, get_timestamp = False):
        '''
        Get all tasks.
        :param courseCount: How many courses should be went through. Will stop autimatically if there's no more
        courses.
        :param get_works: True to get works.
        :param get_exams: True to get exams.
        :param get_stats: True to get stats.
        :param get_timestamp: True to include timestamps in works and exams.
        :return: Tasks information.
        '''
        self.__networkTest()
        info=[]
        course_detail_page_urls = self.__get_all_courses_detail_page_url()
        # traverse each course for works and exams
        for i in range(int(courseCount)):
            try:
                course_detail_page_urls[i]
            except IndexError:
                break
            # go to course detail page for works url and exams url
            tasks_of_course = self.get_course_info(course_detail_page_urls[i],get_works,get_exams,get_stats,get_timestamp)
            info.append(tasks_of_course)

        return info


    def send_mail(self, from_addr, smtp_server, password, to_addr, message, message_type='plain', title='学习通任务自动检查'):
        '''
        Send an E-mail to designated mailbox.
        :param from_addr:
        :param smtp_server:
        :param password:
        :param to_addr:
        :param message:
        :param message_type:
        :param title:
        :return:
        '''
        msg = MIMEText(message, _subtype=message_type, _charset='utf-8')
        msg['From'] = Header(from_addr)
        msg['To'] = Header(to_addr)
        msg['Subject'] = Header(title)
        server = smtplib.SMTP_SSL(smtp_server)
        server.connect(smtp_server, port=465)
        server.login(from_addr, password)
        server.sendmail(from_addr, to_addr, msg.as_string())
        server.quit()




