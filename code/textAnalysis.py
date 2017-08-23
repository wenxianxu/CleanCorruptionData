# -*- coding:utf-8 -*-

import os
import re
import csv
import datetime

#划分一审文书需要用到的正则表达式,暂时只能用来提取判决书，裁定书格式较乱
judgetype_re = r'\s*.*?书\s*$'
defendant_re = r'^\s*被告人(?!.{5,10}一案).*?[，；。]|^\s*被告人.*?（.*?）.*?[，；。]'
defender_re = r'^辩护人.{2,3}[，；。]'
suing_re = r'向本院提起公诉[；，。]|向本院提出公诉[，；。]'
zhikong_re = r'^\s*?.*?指控称?[：。，]|^\s*公诉机关指控'
zhikong_re1 = r'提请本院.*?(?:惩|判)处[，；。]$|定罪量刑[，；。]$'
zhikong_re2 = r'^被告人.*?辩称|.*?异议.*?|^被告人的辩护人认为|^\s*?(?:本院)?经(?:本院)?审[理查].*?查明.*?[：。，]'
zhikong_re_list = [r'提请本院.*?(?:惩|判)处[，；。]',r'定罪量刑[，；。]',r'被告人.*?辩称',r'.*?异议.*?',r'^被告人的辩护人认为',r'^\s*?(?:本院)?经(?:本院)?(?:法庭)?审理.*?查明.*?[：，。]',r'^上述事实',r'被告人.*?交代了.*?事实']
shenli_re = r'^\s*?(?:本院)?经(?:本院)?(?:法庭)?审[查理].*?查明.*?[：，。]'
shenli_re1 = r'^\s*?本院认为'
panjue_re = r'判决如下[:：。，]$|拟判如下[:：。，]$|判处如下[:：。，]$|作如下判决[:：。，]$'
panjue_re1 = r'^如.*?不服本判决|^\s*审\s*判\s*长'


#划分二审文书需要用到的正则表达式
defendant_re_2 = r'^上诉人（?原审被告人）?.*?[，。；]|^原审被告人.*?[，；。]'
panjue_re_2 = r'^本院认为[，：。:]|裁定如下：?:?$|判决如下：?:?$|拟判如下：?:?$|判处如下：?:?$|作如下判决：?:?$'
panjue_re1_2 = r'^本判决为终审判决|^本裁定为终审裁定'
yuanpan_re = r'判决(?:如下)[:，：。]'
yuanpan_re1 = r'(?:宣判后，)*(?:原审被告人)*.*?不服，(?:向本院)*提出？起？.*?上诉[，。；]'
yuan_fact_re = r'^原判.*?认(?:定|为)*[，：。:]|原审法院审理查明|^原审判决认定'
yuan_fact_re1 = r'判决(?:如下)?[，：。:]|^原[审判]认为|^原审法院认为|(?:宣判后，)*(?:原审被告人)*.*?不服，(?:向本院)*提出？起？.*?上诉[，。；]'
zhongjie_re = r'现已审理终结。$'

item = ['docid','defendant_name','gender','birthday','workplace','filing_date','detension_date','bailing_date',
        'arresting_date','detaining_date','begin_year','end_year','criminal_sentences','charge','punishment',
        'charge_sentences','criminal_money','money_sentences','defendant_info','panjue_list']

#判断某文本在划分好的文书列表中的位置
def get_index(target,raw_list):
    index=float('inf')
    for i in range(0,len(raw_list)):
        if target==raw_list[i]:
            index=i
    return index

#清除在被告人列表中索引在辩护人后面的无效信息
def get_clear_defendant(target_list,benchmark,raw_list):
    delete_index=float("inf")
    index=get_index(benchmark,raw_list)
    for j in range(0,len(target_list)):
        k=get_index(target_list[j],raw_list)
        if k>=index:
            delete_index=j
            break
    if delete_index!=float("inf"):
        target_list=target_list[0:delete_index]
    return target_list

#选出所有指控列表中，最为短的列表
def get_short_charge(raw_list,begin_str,end_str_list):
    temp = []
    begin = float('inf')
    end = float('inf')
    obj1 = re.compile(begin_str)
    for i in range(0,len(raw_list)):
        if obj1.search(raw_list[i]):
            begin = i
            for end_str in end_str_list:
                obj2=re.compile(end_str)
                for j in range(i,len(raw_list)):
                    if obj2.search(raw_list[j]):
                        if  end>j:
                            end=j
                            break
            break
   #     print(begin)
   #     print(end)
    if begin!=float('inf') and end!=float('inf') and begin!=end:
        temp=raw_list[begin:end]
    elif begin!=float('inf') and end!=float('inf') and begin==end:
        temp=raw_list[begin:end+1]
    return temp

#抽象出一个传入正则表达式和文本，提取出信息
def  get_info(text,re_str):
    obj=re.compile(re_str)
    temp=obj.findall(text)
    if temp==[]:
        temp=['']
    return temp

#传入一个正则表达式和文本，消除在文本中找到的正则文本并返回文本
def  get_text(text,re_str):
    obj=re.compile(re_str)
    temp=obj.findall(text)
    if temp!=[]:
        index=text.find(temp[0])
        text=text[index+len(temp[0]):]
    else:
        return text
    return text

#传入一个时间列表，将里面的时间全部转化为日期
def change_date(time_list):
    for i in range(0,len(time_list)):
        try:
            if re.search(r'\d{4}年\d+月\d+日?',time_list[i]):
                continue
            elif re.search(r'同日|当日',time_list[i]):
                time_list[i]=time_list[i-1]
            elif re.search(r'\d{4}月\d+月\d+日?',time_list[i]):
                time_list[i]=time_list[i][0:4]+time_list[i][4].replace('月','年')+time_list[i][5:]
            elif re.search(r'[\u4e00-\u9fa5]年\d+月\d+日?',time_list[i]):
                time_list[i]=time_list[i-1][0:4]+time_list[i][1:]
            elif re.search(r'次日',time_list[i]):
                year,month,day=re.findall(r'\d+',time_list[i-1])
                date_new=datetime.date(int(year),int(month),int(day))
                time_list[i]=date_new+datetime.timedelta(days=1)
                year,month,day=re.findall(r'\d+',time_list[i].strftime('%Y-%m-%d'))
                time_list[i]=year+'年'+month+'月'+day+'日'
            elif re.search(r'[\u4e00-\u9fa5]月\d+日?',time_list[i]):
                year=re.findall(r'\d+',time_list[i-1])[0]
                month=str(int(re.findall(r'\d+',time_list[i-1])[1])+1)
                day=re.findall(r'\d+',time_list[i])[0]
                time_list[i]=year+'年'+month+'月'+day+'日'
            elif re.search(r'(?<![年\d])\d+月\d+日?',time_list[i]):
                year=re.findall(r'\d+',time_list[i-1])[0]
                month,day=re.findall(r'\d+',time_list[i])
                time_list[i]=year+'年'+month+'月'+day+'日'
            else:
                continue
        except:
            continue
    for i in range(0,len(time_list)):
        if re.search(r'\d{4}年\d+月\d+日?|',time_list[i]):
            continue
        else:
            print('日期有问题')
            break
    return time_list

#提取被告人信息，传入文本和提取被告人姓名的正则表达式
def get_defendant(text): 
    temp=[]
    #提取被告人姓名
    temp=temp+[get_info(text,r'^\s*被告人.*?[，。；]|^上诉人（?原审被告人）?.*?[，。；]|^原审被告人.*?[，。；]')[-1]]
    text=get_text(text,r'\s*被告人.*?[，。；]|上诉人（?原审被告人）?.*?[，。；]|原审被告人.*?[，；。]')
    #提取被告人性别
    temp=temp+[get_info(text,r'[男女][，。]')[0]]
    text=get_text(text,r'[男女][，。]')
    #提取生日
    temp=temp+[get_info(text,r'生于[\d|X]{4}年.+?月.+?日|[\d|X]{4}年.+?月.+?日出?生')[-1]]
    text=get_text(text,r'生于[\d|X]{4}年.+?月.+?日|[\d|X]{4}年.+?月.+?日出?生')
    #提取工作单位和职务
    temp=temp+get_workplace(text)
    
    #提取逮捕时间等
    temp=temp+get_treatment(text)
    return temp
        
#提取辩护人
#def get_defender():

#提取犯罪时间

#根据正则表达式提取信息
def get_info2(text,re_str):
    obj=re.compile(re_str)
    temp=obj.findall(text)
    return temp

#提取判处力度
def get_judgement(panjue_list):
    punish=[]
    for pj in panjue_list:              
        if re.search(r'被告(?!单位)(?!.*公司)人?.*?犯?.*?罪(?:（未遂）)*[，。；]{0,1}判[处决].*[，。；]{0,1}|被告(?!单位)(?!.*公司)人?.*?犯.*?罪(?:（未遂）)*[，。]{0,1}免予?于?刑事处罚[，。；]{0,1}|被告(?!单位)(?!.*公司)人?.*?犯.*?罪(?:（未遂）)*[，。]{0,1}免除处罚[，。；]{0,1}|被告(?!单位)(?!.*公司)人?.*?犯.*?罪(?:（未遂）)*[，。]{0,1}拘役.*',pj):
            punish.append(pj)
           # punish.append(get_info2(pj,r'被告(?!单位)(?!.*公司)人?.*?犯?.*?罪(?:（未遂）)*[，。；]{0,1}判[处决].*[，。；]{0,1}|被告(?!单位)(?!.*公司)人?.*?犯.*?罪(?:（未遂）)*[，。；]{0,1}免予?于?刑事处罚[，。；]{0,1}|被告(?!单位)(?!.*公司)人?.*?犯.*?罪(?:（未遂）)*[，。]{0,1}免除处罚[，。；]{0,1}|被告(?!单位)(?!.*公司)人?.*?犯.*?罪(?:（未遂）)*[，。]{0,1}拘役.*'))
        else:
            continue
    return punish

#提取罪名
def get_charges(panjue_list):
    pass
    
#提取犯罪金额
def get_criminal_money(panjue_list):
    money=[]
    for pj in panjue_list:
        if re.search(r'被告人.*?所得.*?元|(?:涉案)*赃款.*?元|在案扣押.*?元',pj) and '判决如下：' not in pj:
            money.append(get_info2(pj,r'被告人.*?所得.*?元|(?:涉案)*赃款.*?元|在案扣押.*?元'))
        else:
            continue
    return money
        
#判断时间和金额的位置
def  get_time(time_list,money_list,text):
    i=0
    j=0
    temp=[]
    while i<len(time_list) and j<len(money_list):
        if text.find(time_list[i])>text.find(money_list[j]):
            #            print('1')
            text=get_text(text,money_list[j])
            j=j+1
        elif text.find(time_list[i])<text.find(money_list[j]):
             #           print('2')
            text=get_text(text,time_list[i])
            if text.find(time_list[i+1])>text.find(money_list[j]):
           #                     print('2-1')
                text=get_text(text,money_list[j])
                temp.append(time_list[i])
                i=i+1
                j=j+1
                if j==len(money_list):
                    break
                if i==len(time_list)-1:
                    temp.append(time_list[i])
                    break
            else:
         #                       print('2-2')
                i=i+1
                if i==len(time_list)-1:
                    temp.append(time_list[i])
                    break
   #     print('can out')
    return temp

#获取所有被告的犯罪时间
def  get_all_criminal_time(defendant, raw_list):
    for i in range(0,len(defendant)):
        temp1=raw_list
        temp2=raw_list
        defendant[i] = defendant[i] + get_one_criminal_time(defendant[i][0], temp1)  #10-11位
        defendant[i].append(get_criminal_sentences(defendant[i][0], temp2)) #12位
    
        
#获取一个被告的犯罪时间
def  get_one_criminal_time(name, raw_list):
    final = []
    facts = get_sentences(raw_list)
    final = final + get_criminal_time(name, facts)
    final = get_criminal_year(final)
    return  final
    
    
    
#将传入的列表进行整合分句
def  get_sentences(raw_list):
    temp = raw_list
    temp = ''.join(temp)
    fact_sentences=temp.split('。')
    return fact_sentences

#提取犯罪时间    
def  get_criminal_time(name, raw_list):
    final = []
    previous = []
    for  raw in raw_list:
        
        money_list = []
        time_list = []
        if re.search(r"(?:退缴|归还|退赃|退还|收到).*?元",raw):
            raw = raw.replace(''.join(re.findall(r"(?:退缴|归还|退赃|退还|收到).*?元",raw)), '')
        if  name in raw:
     #       print(raw)
            time_list = re.findall(r'\d{4}年.{0,2}月?至\d+年|\d{4}年.{0,2}月?以来|\d{4}年', raw)
   #         print(time_list)
            money_list = re.findall(r'\d+[，.]{0,1}\d*余?元(?![月旦])|\d+[，.]{0,1}\d*万元(?![月旦])', raw)
            
   #         print(money_list)
        if re.search(r'^(?:事后|在此期间)', raw) and len(time_list) == 0 and len(money_list) !=0 and len(previous) != 0 :
            final = final + previous
        if len(money_list) !=0 and len(time_list) != 0 :
            final = final + time_list
        
        previous = time_list
    return final

#提取某个被告的犯罪句子
def get_criminal_sentences(name, raw_list):
    final = []
    previous_time = []
    previous_text =""
    raw_list = get_sentences(raw_list)
    for  raw in raw_list:
        money_list = []
        time_list = []
        if  name in raw :
            time_list = re.findall(r'\d{4}年.{0,2}月?至\d{4}年|\d{4}年.{0,2}月?以来|\d{4}年', raw)
            money_list = re.findall(r'\d+[，.]{0,1}\d*余?元(?![月旦])|\d+[，.]{0,1}\d*万元(?![月旦])', raw)
        if re.search(r'^事后', raw) and len(time_list) == 0 and len(money_list) !=0 and len(previous_time) != 0 :
            final.append(previous_text)
            final.append(raw)
        if len(money_list) !=0 and len(time_list) != 0 :
            final.append(raw)
        previous_text = raw
        previous_time = time_list
 #   print(final)
    final = '。'.join(final)
    return final
    
        
#传入审理列表和提取犯罪金额的表达式
def get_trial(trial_list,re_str):
    money=[]
    max_money=None
    obj=re.compile(re_str)
    for trial in trial_list:
        if obj.search(trial):
            money=money+obj.findall(trial)
    return money


#整理被告人信息等数据
def get_final_defendant(defendant):
    final=[]   
    filing_date=''
    detension_date=''
    arresting_date=''
    bailing_date=''
    detaining_date=''
    for d in defendant:
        temp=[]
        if '原审' in d:
            if '）' in d:
                temp.append(get_info(d[0],r'(?<=）).*?(?=[，。；])')[0])
            else:
                temp.append(get_info(d[0],r'(?<=原审被告人).*?(?=[，。；])')[0])
        else:
            temp.append(get_info(d[0],r'(?<=被告人).*?(?=[，。；])')[0])
        temp[0] = temp[0].replace('）','')
        if "（" in temp[0]:
            temp[0] =temp[0][:temp[0].index('（')]
        temp.append(get_info(d[1],r'.(?=[，。])')[0])
        temp.append(get_info(d[2],r'\d+年\d+月\d+日')[0])
        temp.append(d[3])
        i=4
        while i<len(d):
            if d[i]=='现':
                i=i+2
                continue
            if d[i+1]=='立案侦查' and filing_date=='':
                filing_date=d[i]
            elif d[i+1]=='刑事拘留' and detension_date=='':
                detension_date=d[i]
            elif d[i+1]=='取保候审' and bailing_date=='':
                bailing_date=d[i]
            elif '逮捕' in d[i+1] and arresting_date=='':
                arresting_date=d[i]
            elif d[i+1]=='羁押' and detaining_date=='':
                detaining_date=d[i]
            else:
                i=i+2
                continue
        temp.append(filing_date)
        temp.append(detension_date)
        temp.append(bailing_date)
        temp.append(arresting_date)
        temp.append(detaining_date)
        final.append(temp)
    return final

#整理起止犯罪年份
def get_criminal_year(raw_list):
    temp=[]
    final=[]
    if raw_list==[]:
        final.append('')
        final.append('')
    else:
        for raw in raw_list:
            if '至' in raw:
                temp=temp+raw.split('至')
            else:
                temp.append(raw)
   #     print(temp)
        if len(temp) == 1 and re.search(r'\d{4}年.{0,2}月?以来', temp[0]):
            final.append(''.join(re.findall('\d{4}(?=年)', temp[0])))
            final.append('until the end')
            return final
        for i in range(0, len(temp)) :
            temp[i] = ''.join(re.findall('\d{4}(?=年)', temp[i]))
        temp=tuple(temp)
        final.append(min(temp))
        final.append(max(temp))
    return final

#整理判决信息
def get_panjue(name, raw_list):
    final=[]
    for p in raw_list:
        temp = p
        if re.search(r'(?:原审)?被告人' + name +'.*?[，；。]', p):
            replace = ''.join(get_info(p,r'(?:原审)?被告人' + name +'.*?[，；。]'))
            p = p.replace(p[:p.find(replace)+len(replace)], '')
            if final == []:
                final.append(replace)
                final.append(p)
                final.append(temp)
    if final == []:
        final.append("")
        final.append("")
        final.append("")
    return final

#整理总的受贿金额
def get_totalmoney1(raw_list):
    final=[]
    for p in raw_list:
        temp=[]
        temp=temp+[get_info(p[0],r'(?<=[所得赃款扣押]{2}).*?元')[0]]
        final.append(temp)
    return final

def get_totalmoney2(raw_list,number):
    final=[]
    money_sum=0
    total=[]
    for p in raw_list:
        temp=[]
        temp=temp+get_info(p[0],r'(?<=[所得赃款扣押]{2}).*?元')
        money_sum=money_sum+len(temp)
        final.append(temp)
    if money_sum==number:
        for f in final:
            for i in f:
                total.append([i])
    else:
        for i in range(0,number):
            total.append([''])
    return total

#提取工作单位和职务
def  get_workplace(text):
    temp=[]
    final=[]
    workplace=[]
    with open('../input/position.txt','rt')  as f:
        data=f.read().split()
    for work in data:
        if  work in text:
            nouse=re.findall(r'[\u4e00-\u9fa5\dX（）]*(?![，。])' + str(work) + '(?!安派出所)(?!抓获).*?[，。]',text)
            if nouse!=[]:
                for w in nouse:
                 #   print("come")
                    if w not in temp:
                        temp.append(w)
    if len(temp)>1:
        for i in range(0,len(temp)):
            include = 0
            for j in range(0,len(temp)):
                if include == 1:
                    break
                if i!=j :
                    if temp[i] in temp[j]:
                        include = 1
                if i == j:
                    continue
            if include == 0:
                final.append(temp[i])
    else:
        final=temp
    if len(final)>1:
        workplace=[''.join(final)]
    else:
        workplace=final
    if workplace==[]:
        workplace=['']
 #   print(workplace)
    return workplace
    
#在事实列表中提取工作单位
def  get_workplaces(name, raw_list):
    final = []
    temp = raw_list
    temp = get_sentences(temp)
  #  print(temp)
    for text in temp :
        
        text = text + '。'
        if name in text and re.search(r'' + name + '.*?(?:身为|作为|担任|委派).*?[，；。]|'+ name +'.*?(?<!主)任(?!务).*?[，；。]|'+ name +'.*?利用.*?职务(?:上的)?便利|时任.*?'+ name +'', text) :
            final = final + re.findall(r'' + name + '.*?(?:身为|作为|担任|委派).*?[，；。]|'+ name +'.*?(?<!主)任(?!务).*?[，；。]|'+ name +'.*?利用.*?职务(?:上的)?便利|时任.*?'+ name +'', text)
        
  #  print(final)
    final = '。'.join(final)
    
    return final
    

#抽象出划分文书的方法，传入一个划分好的文书列表，以及相应用于划分的正则表达式
def divide(raw_list,begin_str,end_str=None):
    temp=[]
    if end_str is not None:
        #      print('come')
        obj1=re.compile(begin_str)
        obj2=re.compile(end_str)
        for i in range(0,len(raw_list)):
            if  obj1.search(raw_list[i]):
           #                     print('come1')
            #                    print(raw_list[i])
                for j in range(i,len(raw_list)):
                    if obj2.search(raw_list[j]):
               #                                 print('come2')
                        temp=temp+raw_list[i:j+1]
                        break
    else:
        obj1=re.compile(begin_str)
        for i in range(0,len(raw_list)):
            if obj1.search(raw_list[i]):
              #                  print(raw_list[i])
                temp=temp+raw_list[i:i+1]
    return temp

#利用short_content来提取金额
def  get_illegel_money(name, text) :
    final = []
    if re.search(r'被告人' + name + '.*?利用.*?(?:职务上的便利|职务之便).*?(?:非法)?(?:收受|骗取).*?元', text):
        temp = ''.join(re.findall(r'被告人' + name + '.*?利用.*?(?:职务上的便利|职务之便).*?(?:非法)?(?:收受|骗取).*?元', text))
       # print(temp)
        final.append( '、'.join(re.findall(r'\d+\.?\d*万?(?=[美澳]*元)', temp)))
        final.append(temp)
    if final == [] :
        final.append("")
        final.append("")
    return  final


def clean_second_trial(panjue_list):
    if panjue_list != [] :
        panjue_list.reverse()
        throw=panjue_list.pop()
        panjue_list.reverse()
        if re.search(r'^本判决为终审判决', panjue_list[-1]) :
            panjue = get_judgement(panjue_list)
            

def get_correct(raw_list):
    for i in range(0,len(raw_list)):
        if '*' in raw_list[i]:
            raw_list[i].replace('*','X')
    return raw_list
    
    
def cleanOneDoc(result):
    defendant=[]
    judge_type=''
    defendant_list=[]
    defender_list=[]
    panjue_list=[]
    total_money=[]
    criminal_time=[]
    #二审所需初始化
    temp=re.findall('<div.*?>(.*?)</div>',result[1],re.M)
#    temp = get_correct(result[1])
    #print(temp)
                
    if result[2]=='一审':
        criminal_time=[]              
        suing_list=[]
        zhikong_list=[]
        shenli_list=[]
        index=float('inf')
        delete_index=float('inf')

        defendant_list=divide(temp,defendant_re)       
        defender_list=divide(temp,defender_re)
        suing_list=divide(temp,suing_re)
        zhikong_list=get_short_charge(temp,zhikong_re,zhikong_re_list)
        if suing_list!=[]:
            defendant_list=get_clear_defendant(defendant_list,suing_list[0],temp)
        if zhikong_list!=[]:
            defendant_list=get_clear_defendant(defendant_list,zhikong_list[0],temp)
        for j in range(0,len(defendant_list)):
            defendant.append(get_defendant(defendant_list[j]))
        defendant=get_final_defendant(defendant)
    #    print(defendant)
        for j in range(0, len(defendant)):
            if '*' in defendant[j][0]:
                defendant[j][0] = defendant[j][0].replace('*', "某")
     #   print(defendant)
        shenli_list=divide(temp, shenli_re, shenli_re1)
        get_all_criminal_time(defendant, shenli_list)   #提到12位了
        panjue_list = divide(temp,panjue_re,panjue_re1)
        if panjue_list!=[]:
            panjue_list.reverse()
            throw=panjue_list.pop()
            panjue_list.reverse()
        panjue = get_judgement(panjue_list)
        #提取工作单位从事实和指控列表中提取
        for j in range(0, len(defendant)):
            if defendant[j][3] == "" :
                defendant[j][3] = get_workplaces(defendant[j][0], shenli_list)
                if get_workplaces(defendant[j][0], zhikong_list) not in defendant[j][3]:
                    defendant[j][3] = defendant[j][3] + get_workplaces(defendant[j][0], zhikong_list)
            
            #如果被告人对指控事实不持异议，那么就可从指控事实里面找犯罪时间
            if defendant[j][9] == "" and re.search(r'被告人' + defendant[j][0] + '.*?(?:不持|亦无|无)异议', result[1]):
                defendant[j][9], defendant[j][10] = get_one_criminal_time(defendant[j][0], zhikong_list)
                defendant[j][11] = get_criminal_sentences(defendant[j][0], zhikong_list)
            #提取判决信息
            defendant[j] = defendant[j] + get_panjue(defendant[j][0], panjue)    #提取到14位
            #利用short_content来提取金额
            if result[3] != None:
                defendant[j] = defendant[j] + get_illegel_money(defendant[j][0], result[3])  #提到16位了
        
                           
    if result[2]=='二审':
        panjue = []
        yuan_facts = []
        yuanpan_list = [] 
        defendant_list = divide(temp, defendant_re_2)
        zhongjie_list = divide(temp, zhongjie_re)
        if zhongjie_list != []:
            defendant_list=get_clear_defendant(defendant_list,zhongjie_list[0],temp)
        for j in range(0,len(defendant_list)):
            defendant.append(get_defendant(defendant_list[j]))
        defendant = get_final_defendant(defendant)
        for j in range(0, len(defendant)):
            if '*' in defendant[j][0]:
                defendant[j][0].replace('*', "某")
        defender_list=divide(temp, defender_re)
        yuanpan_list=divide(temp, yuanpan_re, yuanpan_re1)
        shenli_list=divide(temp, shenli_re, shenli_re1)
        yuan_facts = divide(temp, yuan_fact_re, yuan_fact_re1)
        panjue_list=divide(temp,panjue_re_2,panjue_re1_2)
        if panjue_list!=[]:
            panjue_list.reverse()
            throw=panjue_list.pop()
            panjue_list.reverse()
        
            if re.search(r'^本判决为终审判决', panjue_list[-1]):
                get_all_criminal_time(defendant, shenli_list) 
                panjue = get_judgement(panjue_list)
                for j in range(0, len(defendant)):
                    defendant[j] = defendant[j] + get_panjue(defendant[j][0], panjue)
                    if defendant[j][3] == "" :
                        defendant[j][3] = get_workplaces(defendant[j][0], shenli_list)
                        
            elif re.search(r'^本裁定为终审裁定',panjue_list[-1]):
                panjues = ''.join(panjue_list)
                if re.search(r'维持原判|撤回上诉', panjues):
              #      print(yuan_facts)
                    get_all_criminal_time(defendant, yuan_facts)
              #      print(yuan_facts)
                    panjue = get_judgement(yuanpan_list)
                    for j in range(0, len(defendant)):
                        defendant[j] = defendant[j] + get_panjue(defendant[j][0], panjue)
                        if defendant[j][3] == "":
                            defendant[j][3] = get_workplaces(defendant[j][0], yuan_facts)
                            
                if re.search(r'发回.*?重新审判', panjues):
                    get_all_criminal_time(defendant, yuan_facts)
                    panjue = get_judgement(yuanpan_list)
                    for j in range(0, len(defendant)):
                        defendant[j] = defendant[j] + get_panjue(defendant[j][0], panjue)
                    pass
                    
        '''
        get_all_criminal_time(defendant, shenli_list)
        
        for j in range(0, len(defendant)):
            if defendant[j][3] == "" :
                defendant[j][3] = get_workplaces(defendant[j][0], shenli_list)
            defendant[j] = defendant[j] + get_panjue(defendant[j][0], panjue_list)
            defendant[j] = defendant[j] + get_illegel_money(defendant[j][0], result[3])
        '''
  #  print(defendant)
    for num in range(0,len(defendant)):
        defendant[num].append(defendant_list[num])    #17位
    
    for k in defendant:
        k.append('。'.join(panjue_list))     #18位
        k.reverse()
        k.append(result[0])         #0位
        k.reverse() 
    return defendant

def cleanAllDoc(results):
    total_defendant = []
    for i, result in enumerate(results):
        print(i)
        defendant = cleanOneDoc(result)
        total_defendant = total_defendant + defendant
    return total_defendant

def write_csv(filename, variables, info):
    with open(filename,'w',encoding='utf-8-sig') as aj:
        aj_csv=csv.writer(aj)
        aj_csv.writerow(variables)
        aj_csv.writerows(info)

#传入一个文本，来提取逮捕时间等信息
def get_treatment(text):
    temp=[]   #用于存储最后的时间和处理流程
    #用于存储要删除的索引
    time_list=[]
    treat_list=[]
    new_time=[]
    ti_index=0
    tr_index=0
    time_re=r'(?<!至)\d{4}年\d+月\d+日?(?!至)|\d{4}月\d+月\d+日?|[\u4e00-\u9fa5]年\d+月\d+日?|同日|当日|次日|(?<!（)现(?![暂居住])|[\u4e00-\u9fa5]月\d+日?|(?<![年\d])\d+月\d+日?|[\d|X]{4}年X月X日'
    treat_re=r'立案侦查|羁押|刑事拘留|(?<!执行)逮捕|(?<!决定)逮捕|取?保候审|在家|监视居住|决定逮捕|执行逮捕|批准逮捕|投案[自首]*|归案|传唤|取保侯审'
    temp1=re.findall(time_re,text)
    temp2=re.findall(treat_re,text)
    for t in temp1:
        new_time.append(t)
    new_time=change_date(new_time)
    if temp1==[] or temp2==[]:
        return temp
    while (len(temp1)-len(time_list))!=(len(temp2)-len(treat_list)):
        if (len(temp1)-len(time_list))>(len(temp2)-len(treat_list)):
            if text.find(temp1[ti_index])>text.find(temp2[tr_index]):
              #      print('1')
                treat_list.append(tr_index)
                text=get_text(text,temp2[tr_index])
                tr_index=tr_index+1
                if tr_index==len(temp2):
                    while ti_index<len(temp1):
                        time_list.append(ti_index)
                        ti_index=ti_index+1
            elif text.find(temp1[ti_index])<text.find(temp2[tr_index]):
               #     print('2')
                text=get_text(text,temp1[ti_index])
                if text.find(temp1[ti_index+1])>text.find(temp2[tr_index]):
                 #       print('2-1')
                    text=get_text(text,temp2[tr_index])
                    ti_index=ti_index+1
                    tr_index=tr_index+1
                    if tr_index==len(temp2):
                        while ti_index<len(temp1):
                            time_list.append(ti_index)
                            ti_index=ti_index+1
                else:
                   #     print('2-2')
                    time_list.append(ti_index)
                    ti_index=ti_index+1
        else:
            if (len(temp1)-len(time_list))<(len(temp2)-len(treat_list)):
                #print('3')
                if text.find(temp1[ti_index])<text.find(temp2[tr_index]):
                  #      print('3-1')
                    text=get_text(text,temp2[tr_index])
                    ti_index=ti_index+1
                    tr_index=tr_index+1
                    if ti_index==len(temp1):
                        while tr_index<len(temp2):
                            treat_list.append(tr_index)
                            tr_index=tr_index+1
                elif  text.find(temp1[ti_index])>text.find(temp2[tr_index]):
                    #    print('3-2')
                    text=get_text(text,temp2[tr_index])
                    if text.find(temp1[ti_index])<text.find(temp2[tr_index+1]):
                      #      print('3-3')
                        treat_list.append(tr_index)
                        text=get_text(text,temp2[tr_index+1])
                        tr_index=tr_index+2
                        ti_index=ti_index+1
                        if ti_index==len(temp1):
                            while tr_index<len(temp2):
                                treat_list.append(tr_index)
                                tr_index=tr_index+1
                    else:
                    #    print('3-4')
                        treat_list.append(tr_index)
                        treat_list.append(tr_index+1)
                        text=get_text(text,temp2[tr_index+1])
                        tr_index=tr_index+2
                        if tr_index==len(temp2):
                            while ti_index<len(temp1):
                                time_list.append(ti_index)
                                ti_index=ti_index+1
                
    time_temp=[]
    treat_temp=[]
    for i in range(0,len(temp1)):
        if i not in time_list:
            time_temp.append(new_time[i])
    for i in range(0,len(temp2)):
        if i not in treat_list:
            treat_temp.append(temp2[i])
    for i in range(0,len(time_temp)):
        temp.append(time_temp[i])
        temp.append(treat_temp[i])
    return temp

def saveAllCleanedDoc(filename, results):
    write_csv(filename, item, cleanAllDoc(results))
