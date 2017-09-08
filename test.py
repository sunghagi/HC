#!/nas/HC/PYTHON3.6/bin/python3
#-*- coding: cp949 -*-    


import requests   
import bs4   


#����Ʈ���� �������� å ��ũ ��������    

response = requests.get('http://www.kyobobook.co.kr/bestSellerNew/bestseller.laf')   
#print(response.text)
soup = bs4.BeautifulSoup(response.text, "html.parser")   
book_page_urls = [a.attrs.get('href') for a in soup.select('div.title a[href^="http://www.kyobobook.co.kr/product/detailViewKor.laf"]')]  


#å���� ������ ��������   

for book_page_url in book_page_urls:   
   response = requests.get( book_page_url )   
   soup = bs4.BeautifulSoup(response.text, "html.parser")   

   title = soup.select('h1.title strong')[0].get_text().strip()
   author = soup.select('span.name  a')[0].get_text()

   print("%-40s / %-s" % (title, author))
