# -*- coding: utf-8 -*-

import urlparse, requests, os, re, time
from bs4 import BeautifulSoup
from pymongo import Connection

link_pool_dic = {}    # 暫存連結清單裡的連結
new_link_dic = {}    # 暫存清單連結裡面沒有的新連結
retry_dic = {}    # 暫存連結失敗的連結
doc_id_dic = {}    # 暫存 mongoDB 中已存在的 document id

def get_catalog_linklist (index_link, path):
    page_format = 'http://www.nownews.com%s/'
    result = requests.get(index_link) 
    response = result.text.encode('utf8')
    soup = BeautifulSoup(response)
    catalog_link = soup.findAll('li',{'class':'navtop-button'})[1:]
    print 'start to get catalog links',
    for num in catalog_link:
        catalog =  num.a['href']
        catalog_url = page_format%catalog+'r/'
        get_news_list(catalog_url, path)
        #print catalog_url

def get_news_list (catalog_url, path):
    page_format = catalog_url+'%d'
    file_name = catalog_url.split('cat/')[1].split('/r')[0]    
    start = 1
    print 'start to get news link list',
    for page in range(start,2):
        try:        
            content_link = page_format%start
            result = requests.get(content_link)
            response = result.text.encode('utf8')
            soup = BeautifulSoup(response)
            get_links = soup.find('ul',{'id':'result-list'}).findAll('h2')        
            if len(get_links)>0:
                for news_link in get_links:
                    check_list (news_link, file_name, path)                
            else:
                break
            start = start+1
            time.sleep(5)
        except:
            print catalog_url
            print 'stop at page' + str(page)
    f = open(path+file_name+"_list.txt", 'w') 
    for  overwrite_link in new_link_dic:        
        f.write(overwrite_link + "\n")
    f.close()


def check_list (link, name, path):    
    file_list = os.listdir(path)
    filename = name + "_list.txt"
    if filename not in file_list:
        f= open(path+filename, "w") 
        f.write(link.a['href'] + "\n")
        f.close()
    else:
        f= open(path+filename, "r")
        for line in f.readlines():
            caseno =  line.strip().split('n/')[1]
            link_pool_dic[caseno] = 1
        f.close()   
        check_links = link.a['href'].split('n/')[1]
        if check_links not in link_pool_dic:
            new_link_dic[link.a['href']] = 1

def retry_get_info():
    for retry_link in retry_dic:
            try:
                result = requests.get(retry_link)
                response = result.text.encode('utf8')
                soup = BeautifulSoup(response)
                title = soup.find('div',{'class':'news_story'}).find('h1').text
                content = soup.find('div',{'class':'story_content'}).findAll('p')[1:-1]
                time_clean = soup.find('div',{'id':'reporter_info'}).find('p').text.encode('utf8')
                date = time_clean.strip().replace('年','/').replace('月','/').replace('日','').replace('\n','').replace(' ','')
                keywords = content.text.replace('\n',' ')
                photo = soup.find('div',{'class':'autozoom'}).findAll('img')
                photo_link = photo[0]['src']
                data_insert(title, date, content, retry_link, filename, keywords, photo_link)
                time.sleep(5) 
                print '.',
            except:
                print retry_link

def get_news_contents (path):
    dirs = os.listdir(path)
    print 'start to get news content',
    for filename in dirs:
        con=''
        f = open(path+filename,'r')
        for line in f.readlines(): 
            try:
                news_link = line.strip()
                result = requests.get(news_link)
                response = result.text.encode('utf8')
                soup = BeautifulSoup(response)                
                title = soup.find('div',{'class':'news_story'}).find('h1').text                
                content = soup.find('div',{'class':'story_content'}).findAll('p')[1:-1]               
                for a in content:
                    con = con + a.text.replace('\n','').replace('\r','').strip()
                time_clean = soup.find('div',{'id':'reporter_info'}).find('p').text.encode('utf8')
                date = time_clean.strip().replace('年','/').replace('月','/').replace('日','').replace('\n','').replace(' ','')                
                content_kw = soup.find('div',{'class':'story_content'}).findAll('p')[-1]
                keywords = content_kw.text.replace('\n',' ')                
                photo = soup.find('div',{'class':'autozoom'}).findAll('img')
                photo_link = photo[0]['src']                
                data_insert(title, date, con, news_link, filename, keywords, photo_link)
                time.sleep(5)
                print '.',
            except:
                retry_dic[news_link]=1
                #print news_link
        f.close()
        retry_get_info()

def data_insert (title, date, content, news_link, filename, keywords, photo_link):
    con = Connection() 
    db = con.news
    nownews_news = db.nownews

    doc_catalog = filename.split('_')[0]
    doc_id = news_link.split('n/')[1].replace('/','')
    
    for a in nownews_news.find(): 
        doc_id_dic[a.values()[7]] = 1

    if doc_id not in doc_id_dic:
        data = {"_id":doc_id,
                    "title":title,
                   "date":date,
                   "catalog":doc_catalog,
                   "from":"nownews",
                   "news_link":news_link,
                   "content":content,
                   "keywords":keywords,
                   "photo_link":photo_link}
        nownews_news.insert(data)

get_catalog_linklist('http://www.nownews.com/','nownews/')
get_news_contents('nownews/')  
