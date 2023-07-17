import time
import re
import json
import os
import shutil
import requests
import datetime
import lxml
from bs4 import BeautifulSoup
from selenium import webdriver
from progress.bar import IncrementalBar
from tqdm import tqdm

num_pages = 35
url = 'https://www.marathonbet.ru/su/popular/Football+-+11'
dict = {}
links = []
dictMon = {
    'янв': '01',
    'фев': '02',
    'мар': '03',
    'апр': '04',
    'май': '05',
    'июн': '06',
    'июл': '07',
    'авг': '08',
    'сен': '09',
    'окт': '10',
    'ноя': '11',
    'дек': '12'
}

count1 = int(input('Матчи между собой -> '))
count2 = int(input('Последние матчи команд -> '))
coef = float(input('2.5 or 3.5 -> '))
dateUntil = input('Дата (дд.мм) -> ')
dateUntil = datetime.datetime.strptime(dateUntil, '%d.%m')
findingMatches = []

def checkDate(href):
    dateCur = href.find('td', class_='date date-short').text[3:9]
    dateCur = dateCur.replace(' ', '')
    dateCur = dateCur.replace(dateCur[2:6], '.' + dictMon[dateCur[2:6]])
    dateCur = datetime.datetime.strptime(dateCur, '%d.%m')

    if dateCur < dateUntil:
        return True

    return False

def remove_slashes():
    for it in range(num_pages):
        with open(f'data/{it}.html') as file:
            src = file.read()
        with open(f'data/{it}.html', 'w') as file:
            file.write(src.replace('\\', ''))

def get_html():
    for it in range(num_pages):
        req = requests.get(f'https://www.marathonbet.ru/su/popular/Football+-+11?page={it}&pageAction=getPage').text
        with open(f'data/{it}.html', 'w') as file:
            file.write(req)


def get_href():
    for it in range(1, num_pages):
        with open(f'data/{it}.html') as file:
            src = file.read()
        soup = BeautifulSoup(src, 'lxml')
        hrefs = soup.find_all('table', class_='member-area-content-table')
        for href in hrefs:
            try:
                if checkDate(href):
                    links.append('https://www.marathonbet.ru' + href.find('a', class_='member-link').get('href'))
            except:
                continue

    print(f'Всего матчей: {len(links)}')

def get_stat():
    options = webdriver.ChromeOptions()
    options.add_argument('log-level=3')
    options.headless = True
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    num_range = 0

    for link in tqdm(links):
        try:
            driver.get(link)
            time.sleep(2)
            driver.find_element('class name', 'statistics-button-ico').click()
            time.sleep(2)
            htmlCode = driver.find_element('class name', 'content').get_attribute('innerHTML')
            with open(f'data2/{num_range}.html', 'w', encoding="utf-8") as file:
                file.write(htmlCode)
            num_range += 1
        except:
            continue

def fillDict():
    with open('index.html', encoding='utf-8') as file:
        src = file.read()

    soup = BeautifulSoup(src, 'lxml')
    allCards = soup.find_all('div', class_='bg coupon-row')

    for it in allCards:
        try:
            names = it.find_all('span')
            date = it.find('td', class_='date date-short')
            dict[f'{names[0].text}-{names[1].text} ({str(date)[43:][:12]})'] = 'https://www.marathonbet.ru/' + it.find('a', class_='member-link').get('href')
        except:
            continue

    with open(f"data.json", "w", encoding="utf-8") as file:
        json.dump(dict, file, indent=4, ensure_ascii=False)

def parse():
    num_range = len(os.listdir('data2'))
    for it in tqdm(range(1, num_range)):
        try:
            countSelf = 0
            countFirst = 0
            countSecond = 0
            with open(f'data2/{it}.html', encoding="utf-8") as file:
                src = file.read()
            soup = BeautifulSoup(src, 'lxml')
            selfMatches = soup.find('div', class_='h2h-matches').find_all('span', class_='statistics-cell__main-score')
            lastMatchesFirst = soup.find('div', class_='member-statistics').find_all('span', class_='statistics-cell__main-score')
            lastMatchesSecond = soup.find('div', class_='member-statistics member-statistics_right').find_all('span', class_='statistics-cell__main-score')
            for match in selfMatches:
                summa = 0
                for s in re.findall(r'\d+', match.text):
                    summa += int(s)
                if summa < coef:
                    countSelf += 1
            for match in lastMatchesFirst:
                summa = 0
                for s in re.findall(r'\d+', match.text):
                    summa += int(s)
                if summa < coef:
                    countFirst += 1
            for match in lastMatchesSecond:
                summa = 0
                for s in re.findall(r'\d+', match.text):
                    summa += int(s)
                if summa < coef:
                    countSecond += 1

            if (countSelf >= count1) and (countFirst >= count2) and (countSecond >= count2):
                names = soup.find_all('a', class_='member-link')
                date = soup.find('td', class_='date date-short').text.replace('\n', '')
                findingMatches.append(names[0].find("span").text + ' - ' + names[1].find("span").text + ' (' + date[2:-2] + ')')
        except:
            continue


def clearFile():
    if os.path.exists('data'):
        shutil.rmtree('data')

    if os.path.exists('data2'):
        shutil.rmtree('data2')

    if os.path.exists('index.html'):
        os.remove('index.html')

    os.makedirs('data')
    os.makedirs('data2')


def main():
    a = int(input('Собирать заново?\n\t1 - Да\n\t2 - Нет\n'))
    if a == 1:
        print('Clearing files...')
        clearFile()
        print('Getting html...')
        get_html()
        print('Formatting files...')
        remove_slashes()
        print('Getting links...')
        get_href()
        print('Getting statistic...')
        get_stat()
        print('Finding...')
        parse()
        for it in findingMatches:
            print(it)
    else:
        print('\nFinding...')
        parse()
        for it in findingMatches:
            print(it)

    if len(findingMatches) == 0:
        input('Нет матчей')
    else:
        input('Программа завершилась...')

if __name__ == '__main__':
    main()