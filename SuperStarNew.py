import base64
import re
import smtplib
import time
from email.header import Header
from email.mime.text import MIMEText
import requests
from bs4 import BeautifulSoup as bs
from ping3 import ping


class SuperStar:

    def __init__(self,Phone,Pwd):
        self.__Phone=Phone
        self.__Pwd=str(base64.encodebytes(bytes(Pwd.encode('utf-8')))).lstrip(r"b'").rstrip(r"\n'")
        self.__data = {"fid": "1971", "uname": self.__Phone,
            "password": self.__Pwd, 'refer': 'http%3A%2F%2Fi.mooc.chaoxing.com', 't': 'true'}
        self.__headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36'}
        # to login
        self.__loginurl = "https://passport2.chaoxing.com/fanyalogin"
        # to personal homepage
        self.__myspaceurl = 'http://i.chaoxing.com/'
        # needed for getting the whole url for works and exams
        self.__beginurl = 'https://mooc1-1.chaoxing.com'
        self.arg_list_work=['待做']
        self.arg_list_exam=['未开始', '待做']
        self.arg_list_score_valid=['已完成']
        self.arg_list_score_expired=['已过期']
        self.arg_list_score_skipByName = ['组']
        self.arg_list_timeRestriction=[time.strftime("%Y",time.localtime())]
        self.pingAddressList=["passport2.chaoxing.com", 'i.chaoxing.com']
        self.__courseurls = []
        self.__urlObtained=0
        self.__sessionRefreshThreshold=32
        self.__pauseTime=0.7
        self.__logIn()

    def __networkTest(self):
        results=[]
        for add in self.pingAddressList:
            results.append(ping(add))
        if all(result==False for result in results):
            raise Exception('No Internet connection')
        elif any(result>0.1 for result in results):
            print('Bad network connection, could take some time')
            return True
        else:
            return True

    def __logIn(self):
        if (self.__networkTest() == True):
            self.__s=requests.session()
            self.__s.post(self.__loginurl, headers=self.__headers, data=self.__data)
            time.sleep(self.__pauseTime)

    def __getCoursesPage(self):
        space = self.__s.get(self.__myspaceurl, headers=self.__headers)
        self.__urlObtained+=1
        space = bs(space.text, "html.parser")
        if self.__handleExcepition(space)==False:
            space = self.__s.get(self.__myspaceurl, headers=self.__headers)
            self.__urlObtained += 1
            space = bs(space.text, "html.parser")
        span = re.search(r",'(.*?)'",
                         space.find('span', title="课程").parent.attrs['onclick']).span()
        return(space.find('span', title="课程").parent.attrs['onclick'][
                     span[0] + 2:span[1] - 1])

    def __getCourseUrl(self,courseName):
        coursePageUrl=self.__getCoursesPage()
        # to courses page to get the urls of every course
        coursesPageRQ = self.__s.get(coursePageUrl, headers=self.__headers)
        self.__urlObtained += 1
        coursesPageSoup = bs(coursesPageRQ.text, "html.parser")
        if self.__handleExcepition(coursesPageSoup) == False:
            # to courses page to get the urls of every course
            coursesPageRQ = self.__s.get(coursePageUrl, headers=self.__headers)
            self.__urlObtained += 1
            coursesPageSoup = bs(coursesPageRQ.text, "html.parser")
        try:
            targetCourse = coursesPageSoup.find('a', text=re.compile(courseName,re.I), title=re.compile(courseName,re.I))
            span = re.search(r'href=".*?"', str(targetCourse)).span()
        except:
            raise Exception('No such course found!')
        longurl = str(targetCourse)[span[0] + 6:span[1] - 1]
        partialUrl = re.sub('amp;', '', longurl)
        return(self.__beginurl + partialUrl)

    def getCourseFullName(self,string):
        if not 'http' in string:
            courseUrl = self.__getCourseUrl(string)
        else:
            courseUrl=string
        courseDetail = self.__s.get(courseUrl, headers=self.__headers)
        self.__urlObtained += 1
        courseDetail = bs(courseDetail.text, 'html.parser')
        if self.__handleExcepition(courseDetail) == False:
            courseDetail = self.__s.get(courseUrl, headers=self.__headers)
            self.__urlObtained += 1
            courseDetail = bs(courseDetail.text, 'html.parser')
        courseFullName = courseDetail.find("div", class_="headerwrap").h1.span.attrs['title'].replace(u'\xa0', u' ')
        return courseFullName

    def __getMaxPage(self,url):
        page=10
        url.replace('&', '&pageNum=%d&'%page)
        page = self.__s.get(url, headers=self.__headers)
        self.__urlObtained += 1
        page = bs(page.text, 'html.parser')
        if self.__handleExcepition(page) == False:
            page = self.__s.get(url, headers=self.__headers)
            self.__urlObtained += 1
            page = bs(page.text, 'html.parser')
        try:
            span=re.search(r',(.*), "changePage"',str(page.contents)).span()
            max=str(page.contents)[span[0]+1:span[1]-14]
            return int(max)
        except:
            pass


    def __getWorkFirstUrl(self, string):
        if 'http' in string:
            courseUrl=string
        else:
            courseUrl=self.__getCourseUrl(string)
        urls=[]
        courseDetail = self.__s.get(courseUrl, headers=self.__headers)
        self.__urlObtained += 1
        courseDetail = bs(courseDetail.text, 'html.parser')
        if self.__handleExcepition(courseDetail) == False:
            courseDetail = self.__s.get(courseUrl, headers=self.__headers)
            self.__urlObtained += 1
            courseDetail = bs(courseDetail.text, 'html.parser')
        firsturl = self.__beginurl + courseDetail.find('a', title='作业').attrs['data']
        if self.__urlObtained % self.__sessionRefreshThreshold == 0:
            self.__sessionRefresh()
        return firsturl



    def __getExamFirstUrl(self, string):
        if 'http' in string:
            courseUrl=string
        else:
            courseUrl = self.__getCourseUrl(string)
        courseDetail = self.__s.get(courseUrl, headers=self.__headers)
        self.__urlObtained += 1
        courseDetail = bs(courseDetail.text, 'html.parser')
        if self.__handleExcepition(courseDetail) == False:
            courseDetail = self.__s.get(courseUrl, headers=self.__headers)
            self.__urlObtained += 1
            courseDetail = bs(courseDetail.text, 'html.parser')
        firsturl = self.__beginurl + courseDetail.find('a', title='考试').attrs['data']
        if self.__urlObtained % self.__sessionRefreshThreshold == 0:
            self.__sessionRefresh()
        return firsturl

    def __getOtherUrls(self, firstUrl):
        max=self.__getMaxPage(firstUrl)
        urlList=[]
        for page in range(2,max+1):
            urlList.append(firstUrl.replace('&','&pageNum=%d&'%page,1))
        return urlList



    def __getWorksFromOnePage(self, pageUrl,isFirstPage=False):
        worksofPage=[]
        resp = self.__s.get(pageUrl, headers=self.__headers)
        self.__urlObtained += 1
        soup = bs(resp.text, "html.parser")
        if not self.__handleExcepition(soup):
            resp = self.__s.get(pageUrl, headers=self.__headers)
            self.__urlObtained += 1
            soup = bs(resp.text, "html.parser")
        all = soup.find("ul", class_="clearfix", style=r"*width:1020px;").find_all('li')
        all.reverse()
        for work in all:
            if any(arg in work.text for arg in self.arg_list_work) and any(
                    str(arg) in work.find_all(class_='pt5')[1].text.lstrip().rstrip() for arg in
                    self.arg_list_timeRestriction):
                dict = {'work': work.find('a').text.lstrip().rstrip(),
                        'deadline': work.find_all(class_='pt5')[1].text.lstrip().rstrip()}
                worksofPage.append(dict)
        if isFirstPage==True:
            try:
                soup.find('span',class_='current')
                return worksofPage,True
            except:
                return worksofPage,False
        else:
            return worksofPage


    def __getExamsFromOnePage(self, pageUrl,isFirstPage=False):
        examsofPage = []
        resp = self.__s.get(pageUrl, headers=self.__headers)
        self.__urlObtained += 1
        soup = bs(resp.text, "html.parser")
        if not self.__handleExcepition(soup):
            resp = self.__s.get(pageUrl, headers=self.__headers)
            self.__urlObtained += 1
            soup = bs(resp.text, "html.parser")
        all = soup.find("div", class_="ulDiv", style=r"padding-top:10px;").find_all('li')
        all.reverse()
        for exam in all:
            if any(arg in exam.text for arg in self.arg_list_exam) and any(
                    str(arg) in exam.find(class_='pt5').text.lstrip().rstrip() for arg in
                    self.arg_list_timeRestriction):
                dict = {'exam': exam.find('a').text.lstrip().rstrip(),
                        'deadline': exam.find(class_='pt5').text.lstrip().rstrip()}
                examsofPage.append(dict)
        if isFirstPage==True:
            if not soup.find('span',class_='current')==None:
                return examsofPage,True
            else:
                return examsofPage,False
        else:
            return examsofPage

    def __getWorks(self, string):
        if 'http' in string:
            workurl = string
        else:
            workurl=self.__getWorkFirstUrl(string)
        worksofCourse = []
        workFromPage,notOnlyPage=self.__getWorksFromOnePage(workurl,isFirstPage=True)
        worksofCourse.extend(workFromPage)
        if notOnlyPage==True:
            otherUrls=self.__getOtherUrls(workurl)
            for pageUrl in otherUrls:
                workFromPage=self.__getWorksFromOnePage(pageUrl)
                if not workFromPage==None:
                    worksofCourse.extend(workFromPage)
        return worksofCourse


    def __getExams(self, string):
        if 'http' in string:
            examurl = string
        else:
            examurl=self.__getExamFirstUrl(string)
        examsofCourse = []
        examFromPage,notOnlyPage=self.__getExamsFromOnePage(examurl,isFirstPage=True)
        examsofCourse.extend(examFromPage)
        if notOnlyPage==True:
            otherUrls=self.__getOtherUrls(examurl)
            for pageUrl in otherUrls:
                examFromPage=self.__getExamsFromOnePage(pageUrl)
                if not examFromPage==None:
                    examsofCourse.extend(examFromPage)
        return examsofCourse

    def __getAllCoursesPageElement(self):
        coursePageUrl = self.__getCoursesPage()
        time.sleep(self.__pauseTime)
        coursesPageRQ = self.__s.get(coursePageUrl, headers=self.__headers)
        self.__urlObtained += 1
        coursesPageSoup = bs(coursesPageRQ.text, "html.parser")
        if self.__handleExcepition(coursesPageSoup) == False:
            coursesPageRQ = self.__s.get(coursePageUrl, headers=self.__headers)
            self.__urlObtained += 1
            coursesPageSoup = bs(coursesPageRQ.text, "html.parser")
        return coursesPageSoup.find_all('li', class_='courseItem curFile')

    def __getAllCoursesUrl(self):
        allCourses=self.__getAllCoursesPageElement()
        if len(allCourses) == 0:
            raise Exception('Obtaining all courses url error')
        for course in allCourses:
            if '已开启结课模式 ' not in course.text:
                span = re.search(r'href=".*?"', str(course.find_all('div')[1].h3.a)).span()
                longurl = str(course.find_all('div')[1].h3.a)[span[0] + 6:span[1] - 1]
                partialUrl = re.sub('amp;', '', longurl)
                self.__courseurls.append(self.__beginurl + partialUrl)

    def __sessionRefresh(self):
        time.sleep(self.__pauseTime)
        self.__logIn()
        self.__urlObtained=0
        print('session refreshed')


    def __handleExcepition(self,soup):
        if '您的操作出现异常，请输入验证码' in soup.text:
            print('exception handled')
            self.__sessionRefresh()
            return False
        else:
            return True



    def getCourseTasks(self, string, getWorks=True, getExams=True):
        if (self.__networkTest() == True):
            result={'courseFullName': self.getCourseFullName(string)}
            if getWorks==True:
                works = self.__getWorks(string)
                if not works == []:
                    result['works']=works
            if getExams==True:
                exams = self.__getExams(string)
                if not exams == []:
                    result['exams']=exams
            return result
        else:
            return None




    def getAllTasks(self, courseCount=100, getWorks=True, getExams=True):
        if(self.__networkTest()==True):
            info={}
            self.__getAllCoursesUrl()
            # traverse each course for works and exams
            for i in range(int(courseCount)):
                try:
                    self.__courseurls[i]
                except IndexError:
                    break
                # go to course homepage for works url and exams url
                tasksOfCourse={}
                workurl=self.__getWorkFirstUrl(self.__courseurls[i])
                examurl=self.__getExamFirstUrl(self.__courseurls[i])
                courseName=self.getCourseFullName(self.__courseurls[i])

                works=self.__getWorks(workurl)
                exams=self.__getExams(examurl)
                if not works==[] and getWorks==True:
                    tasksOfCourse.setdefault('works','')
                    tasksOfCourse['works']=works
                if not exams==[] and getExams==True:
                    tasksOfCourse.setdefault('exams','')
                    tasksOfCourse['exams']=exams

                if not tasksOfCourse=={}:
                    info.setdefault(courseName,'')
                    info[courseName]=tasksOfCourse
            return info
        else:
            return None


    def getCourseAvgScore(self,string,getWorksAvg=True,getExamsAvg=True):
        if (self.__networkTest() == True):
            courseFullName=self.getCourseFullName(string)
            totalWorksScore=0
            worksCount=0
            totalExamsScore=0
            examsCount=0
            workFirstUrl = self.__getWorkFirstUrl(string)
            workUrls=[workFirstUrl]
            if self.__getWorksFromOnePage(workFirstUrl,isFirstPage=True)[1]:
                workOtherUrls = self.__getOtherUrls(workFirstUrl)
                if not workOtherUrls == None:
                    workUrls.extend(workOtherUrls)


            examFirstUrl=self.__getExamFirstUrl(string)
            examUrls=[examFirstUrl]
            if self.__getExamsFromOnePage(examFirstUrl,isFirstPage=True)[1]:
                examOtherUrls = self.__getOtherUrls(examFirstUrl)
                if not examOtherUrls == None:
                    examUrls.extend(examOtherUrls)


            worksAvg=0
            examsAvg=0

            if getWorksAvg:
                #worksAvg
                scoresofWorks = []
                for workUrl in workUrls:
                    resp = self.__s.get(workUrl, headers=self.__headers)
                    self.__urlObtained += 1
                    soup = bs(resp.text, "html.parser")
                    if not self.__handleExcepition(soup):
                        resp = self.__s.get(workUrl, headers=self.__headers)
                        self.__urlObtained += 1
                        soup = bs(resp.text, "html.parser")
                    allWorks = soup.find("ul", class_="clearfix", style=r"*width:1020px;").find_all('li')
                    for work in allWorks:
                        if any(str(arg) in work.find("span",text=re.compile('时间')).parent.text for arg in self.arg_list_timeRestriction):
                            workName = work.find('a').text.lstrip().rstrip()
                            if any(arg in workName for arg in self.arg_list_score_skipByName):
                                continue
                            elif any(arg in work.text for arg in self.arg_list_score_expired):
                                workScore=0
                                worksCount += 1
                            elif any(arg in work.text for arg in self.arg_list_score_valid):
                                try:
                                    workScore=float(work.find(text=re.compile('分')).parent.text.lstrip().rstrip().rstrip('分'))
                                    worksCount += 1
                                except:
                                    continue
                            else:
                                continue

                            dict = {'work': workName,
                                'score': workScore}
                            scoresofWorks.append(dict)


                if worksCount==0:
                    worksAvg=None
                else:
                    for score in scoresofWorks:
                        totalWorksScore+=float(score['score'])
                    worksAvg=round(totalWorksScore/worksCount,2)

            if getExamsAvg:
                #examAvg
                scoresofExams=[]
                for examurl in examUrls:
                    resp = self.__s.get(examurl, headers=self.__headers)
                    self.__urlObtained += 1
                    soup = bs(resp.text, "html.parser")
                    if not self.__handleExcepition(soup):
                        resp = self.__s.get(examurl, headers=self.__headers)
                        self.__urlObtained += 1
                        soup = bs(resp.text, "html.parser")
                    allExams = soup.find("div", class_="ulDiv", style=r"padding-top:10px;").find_all('li')
                    for exam in allExams:
                        if any(str(arg) in exam.find("span",text=re.compile('时间')).parent.text for arg in self.arg_list_timeRestriction):
                            examName = exam.find('a').text.lstrip().rstrip()
                            if any(arg in examName for arg in self.arg_list_score_skipByName):
                                continue
                            if any(arg in exam.text for arg in self.arg_list_score_expired):
                                examScore = 0
                                examsCount += 1
                            elif any(arg in exam.text for arg in self.arg_list_score_valid):
                                try:
                                    examScore=float(exam.find(text=re.compile('分')).parent.text.lstrip().rstrip().rstrip('分'))
                                    examsCount += 1
                                except:
                                    continue
                            else:
                                continue
                            dict = {'work': examName,
                                    'score': examScore}
                            scoresofExams.append(dict)

                if examsCount==0:
                    examsAvg=None
                else:
                    for score in scoresofExams:
                        totalExamsScore += score['score']
                    examsAvg=round(totalExamsScore/examsCount,2)
            if getWorksAvg and getExamsAvg:
                return {'courseName':courseFullName,'worksAvg':worksAvg,'examsAvg':examsAvg}
            elif getWorksAvg:
                return {'courseName':courseFullName,'worksAvg':worksAvg}
            elif getExamsAvg:
                return {'courseName':courseFullName,'examsAvg':examsAvg}
        else:
            return None


    def getAllAvgScore(self,courseCount=100,getWorksAvg=True,getExamsAvg=True):
        if (self.__networkTest() == True):
            result=[]
            self.__getAllCoursesUrl()
            for i in range(courseCount):
                try:
                    self.__courseurls[i]
                except IndexError:
                    break
                result.append(self.getCourseAvgScore(self.__courseurls[i],getWorksAvg,getExamsAvg))
            return result
        else:
            return None

    def sendMail(self,from_addr, smtp_server, password, to_addr, message, messageType='plain',title='学习通任务自动检查'):
        msg = MIMEText(message, _subtype=messageType, _charset='utf-8')
        msg['From'] = Header(from_addr)
        msg['To'] = Header(to_addr)
        msg['Subject'] = Header(title)
        server = smtplib.SMTP_SSL(smtp_server)
        server.connect(smtp_server, port=465)
        server.login(from_addr, password)
        server.sendmail(from_addr, to_addr, msg.as_string())
        server.quit()




