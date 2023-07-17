import time
import json
import os
import requests
import datetime
import lxml
from bs4 import BeautifulSoup
from selenium import webdriver
import selenium.common.exceptions

a = int(input('1 - Футбол\n2 - Хоккей\n'))
url = 'https://...' if a == 1 else 'https://...'

headers = {
    "Accept": "application/json, text/plain, */*",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.174 YaBrowser/22.1.3.848 Yowser/2.5 Safari/537.36"
}

SLEEP_TIME = 2
nowYear = '.' + datetime.datetime.now().strftime('%y')
dictH = {}
dictG = {}
diffForm = float(input('Разница форм -> '))
diffPos = float(input('Разница мест -> '))
numWins = float(input('Количество побед -> '))
cfStart = float(input('Коэф. с -> '))
cfUntil = float(input('Коэф. до -> '))
dateUntil = input('Дата конца -> ')


def getDate(driver):
    return driver.find_elements('class name', 'statistic__date')[-1].text


def reformatDate(driver):
    bufDate = getDate(driver)
    if bufDate == 'Завтра':
        return datetime.datetime.now() + datetime.timedelta(days=1)
    elif bufDate == 'Сегодня' or bufDate.find('Через') != -1 or bufDate.find('Т') != -1 or bufDate.find(
            'Пер.') != -1 or bufDate.find('П') != -1:
        return datetime.datetime.now()
    else:
        return datetime.datetime.strptime(bufDate + nowYear, '%d.%m.%y')


def checkDate(date, driver):
    currentDate = reformatDate(driver)
    untilDate = datetime.datetime.strptime(date + nowYear, '%d.%m.%y')

    return currentDate <= untilDate


def getHtmlCode():
    driver = webdriver.Chrome()
    driver.maximize_window()
    driver.get(url)

    while checkDate(dateUntil, driver):
        try:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(SLEEP_TIME)
        except selenium.common.exceptions.StaleElementReferenceException:
            continue

    htmlCode = driver.find_element('class name', 'content').get_attribute('innerHTML')

    with open("index.html", "a", encoding="utf-8") as file:
        file.write(htmlCode)


def checkCfH(soup, item):
    cf = item.find('div', class_='coefficient__td').text
    if cf == '−/−':
        cf = '0'

    return cf


def checkCfG(soup, item):
    cf = item.find("div", class_="coefficient").find_all("div", class_="coefficient__td")[2].text
    if cf == '−/−':
        cf = '0'

    return cf


def getLinks(soup, item):
    return "https://s5.sir.sportradar.com/winline/ru/" + item.find('div',
                                                                   class_='icon__item icon__info ng-star-inserted').find(
        'a').get('href')[6:]


def getNames(soup, item):
    names = item.find_all("span")
    return names[0].text + ' - ' + names[2].text


def checkTime(soup, item):
    if item.find('div', class_='statistic__date').text.find('Т') == -1 and item.find('div',
                                                                                     class_='statistic__date').text.find(
        'Пер.') == -1:
        return True


def fillDictH(soup):
    items = soup.find_all('div', class_='table__item')
    for item in items:
        try:
            date = item.find('div', class_='statistic__date').text
            if cfStart <= float(checkCfH(soup, item)) <= cfUntil and checkTime(soup, item):
                dictH[getNames(soup, item) + ' ' + checkCfH(soup, item) + ' ' + date] = getLinks(soup, item)
        except AttributeError:
            continue


def fillDictG(soup):
    items = soup.find_all('div', class_='table__item')
    for item in items:
        try:
            date = item.find('div', class_='statistic__date').text
            if cfStart <= float(checkCfG(soup, item)) <= cfUntil and checkTime(soup, item):
                dictG[getNames(soup, item) + ' ' + checkCfG(soup, item) + ' ' + date] = getLinks(soup, item)
        except AttributeError:
            continue


def fillJson():
    with open('index.html', encoding='utf-8') as file:
        src = file.read()

    soup = BeautifulSoup(src, 'lxml')
    fillDictH(soup)
    fillDictG(soup)

    with open(f"dataH.json", "w", encoding="utf-8") as file:
        json.dump(dictH, file, indent=4, ensure_ascii=False)

    with open(f"dataG.json", "w", encoding="utf-8") as file:
        json.dump(dictG, file, indent=4, ensure_ascii=False)


def checkStatistic(href, hg):
    src = requests.get(href, headers=headers).text
    soup = BeautifulSoup(src, 'lxml')

    all_form_match = soup.find_all("div", class_="row flex-xs-nowrap no-margin form-left form-box-container")
    all_form = soup.find_all("div", class_="col-sm-5 graphics-text-regular-color")
    form_left = all_form[0].find("p", class_="text-center").text
    form_right = all_form[1].find("p", class_="text-center").text

    match_left = all_form_match[0].find_all("text", {"font-size": "40"})
    match_right = all_form_match[1].find_all("text", {"font-size": "40"})

    pos_left = all_form[0].find("text", class_="graphics-text-primary-fill size-m").text
    pos_right = all_form[1].find("text", class_="graphics-text-secondary-fill size-m").text
    vol = 0

    if hg == 'h':
        try:
            for i in match_left:
                if i.text == "В":
                    vol += 1
        except IndexError:
            pass

        if vol >= numWins and (
                int(form_left[0:len(form_left) - 1]) - int(form_right[0:len(form_right) - 1])) >= diffForm and (
                int(pos_right[1:len(pos_right)]) - int(pos_left[1:len(pos_left)])) >= diffPos:
            return True

    elif hg == 'g':
        try:
            for i in match_right:
                if i.text == "В":
                    vol += 1
        except IndexError:
            pass

        if vol >= numWins and (
                int(form_right[0:len(form_right) - 1]) - int(form_left[0:len(form_left) - 1])) >= diffForm and (
                int(pos_left[1:len(pos_left)]) - int(pos_right[1:len(pos_right)])) >= diffPos:
            return True

    return False


def parse():
    with open(f"dataH.json", encoding="utf-8") as file:
        allMatchH = json.load(file)

    with open(f"dataG.json", encoding="utf-8") as file:
        allMatchG = json.load(file)

    print('Хозяева:')
    for name, href in allMatchH.items():
        try:
            if checkStatistic(href, 'h'):
                print(name)
        except AttributeError:
            continue
        except IndexError:
            continue

    print('Гости:')
    for name, href in allMatchG.items():
        try:
            if checkStatistic(href, 'g'):
                print(name)
        except AttributeError:
            continue
        except IndexError:
            continue

    print('Программа завершилась')


def clearFile():
    if os.path.exists('dataG.json'):
        os.remove('dataG.json')

    if os.path.exists('dataH.json'):
        os.remove('dataH.json')

    if os.path.exists('index.html'):
        os.remove('index.html')


def main():
    clearFile()
    getHtmlCode()
    fillJson()
    parse()

    a = input('Нажмите любую клавишу, чтобы закрыть окно.')


if __name__ == '__main__':
    main()
