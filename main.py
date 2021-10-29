import sys
from time import sleep
import ddddocr
import requests
from prettytable import PrettyTable
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def get_driver(driver_path, headless=True):
    if headless:
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--headless')
        chrome_options.add_experimental_option('w3c', False)
        driver = webdriver.Chrome(executable_path=driver_path, options=chrome_options)
    else:
        driver = webdriver.Chrome(executable_path=driver_path)
    # driver.implicitly_wait(10)
    return driver


def get_check_code_image(driver, img_path):
    check_code_url = 'http://sep.ucas.ac.cn/changePic'
    headers = {
        'Host': 'sep.ucas.ac.cn',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36',
        'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
        'Referer': 'http://sep.ucas.ac.cn/',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9'
    }
    # set cookies
    c = driver.get_cookies()
    cookies = {}
    # get name and value item of cookie, convert to the dict used in requests
    for cookie in c:
        cookies[cookie['name']] = cookie['value']
    # download the check code image via get request
    response = requests.get(url=check_code_url, headers=headers, cookies=cookies)
    img_data = response.content
    with open(img_path, 'wb')as fp:
        fp.write(img_data)


def ocr(img_path):
    # recognize the image
    ocr = ddddocr.DdddOcr()
    with open(img_path, 'rb') as f:
        img_bytes = f.read()
    ocr_res = ocr.classification(img_bytes)
    return ocr_res


# find checkcode element, if find then fill in
def fill_in_check_code(driver):
    img_path = './img/code.png'
    code_element = driver.find_elements_by_name('certCode')
    if len(code_element) > 0:
        get_check_code_image(driver, img_path)
        code = ocr(img_path)
        # fill in the code
        code_element[0].send_keys(code)


def get_all_homework_from_course_website(driver):
    courses_links = driver.find_element_by_class_name('otherSitesCategorList').find_elements_by_tag_name('li')
    res = []
    for i in range(len(courses_links)):
        driver.find_element_by_link_text('我的课程').click()
        sleep(1)
        courses_links = driver.find_element_by_class_name('otherSitesCategorList').find_elements_by_tag_name('li')
        courses_link = courses_links[i]
        course_item = courses_link.find_element_by_class_name('fav-title')
        course_name = course_item.find_element_by_class_name('fullTitle').text
        # 跳转到当前课程
        course_item.find_element_by_tag_name('a').click()
        sleep(1)
        # 跳转到作业界面
        driver.find_element_by_link_text('作业').click()
        tables = driver.find_elements_by_tag_name('table')
        if len(tables) == 0:
            print("{}没有作业".format(course_name))
        else:
            homework_table = tables[0]
            homeworks = homework_table.find_elements_by_tag_name('tr')[1:]
            for homework in homeworks:
                infos = homework.find_elements_by_tag_name('td')[1:]
                infos = list(map(lambda x: x.text, infos))
                infos.insert(0, course_name)
                res.append(infos)
    return res


def print_table(lines):
    tb = PrettyTable(['课程名', '作业', '提交状态', '开始', '截止'], encoding=sys.stdout.encoding)
    tb.add_rows(lines)
    print(tb.get_string(sortby='截止', reversesort=False))


def course_list(username, password):
    # load driver
    chrome_driver_path = './driver/chromedriver.exe'
    driver = get_driver(chrome_driver_path, headless=False)
    # visit sep
    url = "http://sep.ucas.ac.cn/"
    driver.get(url)
    sleep(1)
    # fill in check code
    fill_in_check_code(driver)
    # fill in username and password
    username_element = driver.find_element_by_id('userName')
    username_element.send_keys(username)
    password_element = driver.find_element_by_id('pwd')
    password_element.send_keys(password)
    # login to sep
    driver.find_element_by_id('sb').click()
    sleep(1)
    hands = driver.window_handles  # 获取所有的句柄
    driver.switch_to.window(hands[-1])  # 转到新页面
    # move to course website
    driver.find_element_by_link_text('课程网站').click()
    sleep(1)
    # get all homework info
    homeworks = get_all_homework_from_course_website(driver)
    driver.close()
    # print results
    homework_need_done = list(filter(lambda x: '尚未提交' in x[2], homeworks))
    homework_done = list(filter(lambda x: '已提交' in x[2], homeworks))
    print('赶紧做作业：')
    print_table(homework_need_done)
    print('还好做完了：')
    print_table(homework_done)


if __name__ == '__main__':
    m_username = ''
    m_password = ''
    course_list(m_username, m_password)
