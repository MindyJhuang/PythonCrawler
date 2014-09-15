# -*- coding: utf-8 -*-
 
import urlparse, requests, os, re, time
from bs4 import BeautifulSoup
from pymongo import Connection

catalog_dic = {'/list/aall-1.aspx':'','http://cnavideo.cna.com.tw':'','/newsphotolist/aspt-1.aspx':''}
link_pool_dic = {}
new_link_dic = {}
con_id = {}
retry_dic = {}

def get_catalog_link (homepage):
    result = requests.get(homepage)
    response = result.text.encode('utf8')
    soup = BeautifulSoup(response)
    catalog_link = soup.select('.sf-menu li')
    for num in catalog_link:
        if num.find('span') is not None:
            catalog = num.find('a')['href']
            if catalog not in catalog_dic:
                url = urlparse.urljoin('http://www.cna.com.tw',catalog.split('1')[0])
                get_news_link(url)

def get_news_link (url):
    get_url = url+'%d.aspx'
    fomate = "%s_list.txt"
    file_name = fomate%get_url.split('list/')[1].split('-')[0]    
    for page in range (1,5):
        news_url = get_url%page
        result = requests.get(news_url)
        response = result.text.encode('utf8')
        soup = BeautifulSoup(response)
        link_list = soup.find('div',{'class':'block block_p7'}).findAll('a')
        if len(link_list) > 0:
            for links in link_list:
                news_link = urlparse.urljoin('http://www.cna.com.tw',links['href'])
                check_link(news_link, file_name)
                #print news_link
        else:
            break
    f = open("cna/"+file_name, 'w')       
    for overwrite_link in new_link_dic: 
        f.write(overwrite_link + "\n")
    f.close()   

def check_link (news_link, file_name):
    dirs = os.listdir('cna/')
    if file_name not in dirs:
        f = open("cna/"+file_name, 'w')
        f.write(news_link + "\n")
        f.close()
    else:
        f = open("cna/"+file_name, 'r')
        for line in f.readlines(): 
            link_pool_dic[line]=1
        f.close()
        if news_link not in link_pool_dic:
            new_link_dic[news_link] = 1

def retry_get_info():
    for retry_link in retry_dic:
        result = requests.get(retry_link)
        response = result.text.encode('utf8')
        soup = BeautifulSoup(response)
        title = soup.find('h2').text

        filename = retry_link.split('news/')[1].split('/')[0]+'_list.txt'    
        time_clean = soup.find('div',{'class':'date'}).contents[0].replace('\n','').replace('\r','').replace('        ','')
        date = time_clean.encode('utf8').split('：')[1]
        content = soup.find('div',{'class':'box_2'}).text.replace('\n','')[:-7]
        data_insert(title, date, content, retry_link, filename)
        time.sleep(5) 

def get_news_contents (path):
    dirs = os.listdir(path)
    for filename in dirs:
        f = open(path+filename,'r')
        for line in f.readlines(): 
            try:
                news_link = line.strip()
                result = requests.get(news_link)
                response = result.text.encode('utf8')
                soup = BeautifulSoup(response)
                title = soup.find('h2').text
                time_clean = soup.find('div',{'class':'date'}).contents[0].replace('\n','').replace('\r','').replace('        ','')
                date = time_clean.encode('utf8').split('：')[1]
                content = soup.find('div',{'class':'box_2'}).text.replace('\n','')[:-7]
                data_insert(title, date, content, news_link, filename)
                time.sleep(5)
                print '.'
            except:
                retry_dic[news_link]=1
                #print news_link
        f.close()
        retry_get_info()

def data_insert (title, date, content, news_link, filename):
    con = Connection()
    db = con.news
    cna_news = db.cna    
   
    doc_catalog = filename.split('_')[0]
    doc_id = news_link.split(doc_catalog+'/')[1].split('-')[0]
    
    for a in cna_news.find():
        con_id[a.values()[6]] = 1

    if doc_id not in con_id:
        data = {"_id":doc_id,
                    "title":title,
                   "date":date,
                   "catalog":doc_catalog,
                   "from":"中央社",
                   "news_link":news_link,
                   "content":content}
        cna_news.insert(data)

get_catalog_link('http://www.cna.com.tw/')
get_news_contents('cna/')
