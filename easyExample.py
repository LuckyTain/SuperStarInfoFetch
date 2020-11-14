from SuperStarNew import SuperStar
#输入所有必要信息
phone=input('输入手机号')
pw=input('输入密码')
count=input('本学期课程数')

#初始化SuperStar对象
ss=SuperStar(phone,pw)

#打印查询的信息
print(ss.getAllTasks(count))