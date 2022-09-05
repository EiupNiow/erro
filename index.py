# -*- coding: utf-8 -*- 
import time,json,requests,random,datetime,os
import campus

def main(mark, phone, password, deviceId, SendKey):
    #定义变量
    success,failure=[],[]
    #提交打卡
    for index,value in enumerate(phone):
        print("开始尝试为用户%s打卡"%(value[-4:]))
        count = 0
        while (count <= 3):
            try:
                token = campus.campus_start(phone[index],password[index],deviceId[index])
                userInfo=getUserInfo(token)
                if mark == 0:
                    response = checkIn(userInfo,token)
                if mark == 1:
                    ownphone=phone[index]
                    response = check(ownphone,userInfo,token)
                strTime = getNowTime()
                if response.json()["msg"] == '成功':
                    success.append(value[-4:])
                    print(response.text)
                    msg = strTime + value[-4:]+"打卡成功"
                    break
                else:
                    failure.append(value[-4:])
                    print(response.text)
                    msg =  strTime + value[-4:] + "打卡异常"
                    count = count + 1
                    if count<=3:
                        print('%s打卡失败，开始第%d次重试...'%(value[-4:],count))
                    time.sleep(5)
            except Exception as e:
                print(e.__class__)
                failure.append(value[-4:])
                strTime = getNowTime()
                msg = strTime + value[-4:] +"出现错误"
                count = count + 1
                response = '出现错误'
                if count<=3:
                    print('%s打卡出错，开始第%d次重试...'%(value[-4:],count))
                time.sleep(3)
        if index == 0:
            result=response
        print(msg)
        print("-----------------------")
    fail = sorted(set(failure),key=failure.index)
    title = "成功: %s 人,失败: %s 人"%(len(success),len(fail))
    try:
       print('主用户开始微信推送...')
       wechatPush(title,SendKey[0],success,fail,result)
    except Exception as e:
        print("微信推送出现错误：")
        print(e.__class__)

#时间函数
def getNowTime():
    cstTime = (datetime.datetime.utcnow() + datetime.timedelta(hours=8))
    strTime = cstTime.strftime("%H:%M:%S ")
    return strTime

#信息获取函数
def getUserInfo(token):
    try:
        data = {"appClassify": "DK", "token": token}
        sign_url = "https://reportedh5.17wanxiao.com/api/clock/school/getUserInfo"
        response = requests.post(sign_url, data=data)
        return response.json()['userInfo']
    except:
        print('getUserInfo ERR，Retry......')

#校内打卡提交函数
def checkIn(userInfo,token):
    sign_url = "https://reportedh5.17wanxiao.com/sass/api/epmpics"
     #随机温度(36.2~36.8)
    a=random.uniform(36.2,36.8)
    temperature = round(a, 1)
    jsons={
            "businessType": "epmpics",
            "method": "submitUpInfoSchool",
            "jsonData": {
            "deptStr": {
                "deptid": userInfo['classId'],
                "text": userInfo['classDescription']
            },
            #请自行打卡抓包修改地址字段
            "areaStr": {"streetNumber":"","street":"xxxxx","district":"中原区","city":"郑州市","province":"河南省","town":"","pois":"xxxxxxxx","lng":xxx.xxxxx + random.random()/1000,"lat":xxx.xxxxx + random.random()/1000,"address":"xxxxxxx","text":"河南省-郑州市","code":""},
            "reportdate": round(time.time()*1000),
            "customerid": userInfo['customerId'],
            "deptid": userInfo['classId'],
            "source": "app",
            "templateid": "clockSign2",
            "stuNo": userInfo['stuNo'],
            "username": userInfo['username'],
            "userid": round(time.time()),
            "updatainfo": [  
                {
                    "propertyname": "temperature",
                    "value": temperature
                },
                {
                    "propertyname": "symptom",
                    "value": "无症状"
                }
            ],
            "customerAppTypeRuleId": 147,
            "clockState": 0,
            "token": token
            },
            "token": token
    }
    #提交打卡
    response = requests.post(sign_url, json=jsons)
    return response

#校外打卡
def check(ownphone,userInfo,token):
    sign_url = "https://reportedh5.17wanxiao.com/sass/api/epmpics"
    #获取datajson
    post_json = {
            "businessType": "epmpics",
            "jsonData": {
            "templateid": "pneumonia",
            "token": token
        },
            "method": "getUpDataInfoDetail"
    }      
    response = requests.post(sign_url, json=post_json).json()
    data = json.loads(response['data'])
    info_dict = {
            "add":data['add'],
            "areaStr": data['areaStr'],
            "updatainfo": [{"propertyname": i["propertyname"], "value": i["value"]} for i in
                            data['cusTemplateRelations']]
        }
    #随机温度
    a=random.uniform(36.2,36.8)
    temperature = round(a, 1)
    for i in info_dict['updatainfo']: 
        if i['propertyname'] == 'temperature':
            i['value'] = temperature
    #校外打卡提交json
    check_json = {
    "businessType": "epmpics",
    "method": "submitUpInfo",
    "jsonData": {
        "add": info_dict['add'],
        "areaStr": info_dict['areaStr'],
        "cardNo": "null",
        "customerid": userInfo['customerId'],
        "deptStr": {
            "deptid": userInfo['classId'],
            "text": userInfo['classDescription'],
        },
        "phonenum": ownphone,
        "stuNo": userInfo['stuNo'],
        "templateid": "pneumonia",
        "upTime": "null",
        "userid": userInfo['userId'],
        "username": userInfo['username'],
        "deptid": userInfo['classId'],
        "updatainfo": info_dict['updatainfo'],
        "source": "app",
        "reportdate": round(time.time()),
        "gpsType": 1,
        "token": token
    }
}
    res = requests.post(sign_url, json=check_json) 
    return res

#微信通知
def wechatPush(title,SendKey,success,fail,result):    
    strTime = getNowTime()
    if result == '出现错误':
        page=['出现错误']
    else:
        page = json.dumps(result.json(), sort_keys=True, indent=4, separators=(',', ': '),ensure_ascii=False)
    content = f"""
`{strTime}` 
#### 打卡成功用户：
`{success}` 
#### 打卡失败用户:
`{fail}`
#### 主用户打卡信息:
```
{page}
```
### 😀[收藏此项目](https://github.com/YooKing/HAUT_autoCheck)

"""
  
    data = {
            "title":title,
            "desp":content
    }
    scurl='https://sctapi.ftqq.com/'+SendKey+'.send'
    for _ in range(3):
        try:
            req = requests.post(scurl,data = data)
            if req.json()['data']['error'] == 'SUCCESS':
                print("Server酱推送服务成功")
                break
            else:
                print("Server酱推送服务失败")
                time.sleep(3) 
        except Exception as e:
            print(e.__class__)

def main_handler(arg1, arg2):
    mark = 0
    phone, password, deviceId, SendKey = [], [], [], []  
    i = 1
    while True:  
        try:
            users = os.environ.get('user' + str(i))
            info = users.split(',')
            phone.append(info[0])
            password.append(info[1])
            deviceId.append(info[2])
            SendKey.append(info[3])
            i += 1
        except:
            break
    main(mark, phone, password, deviceId, SendKey)
           
if __name__ == '__main__':
    mark = 0
    #sectets字段录入
    phone, password, deviceId, SendKey = [], [], [], []    
    while True:  
        try:
            users = input()
            info = users.split(',')
            phone.append(info[0])
            password.append(info[1])
            deviceId.append(info[2])
            SendKey.append(info[3])
        except:
            break
    main(mark, phone, password, deviceId, SendKey)