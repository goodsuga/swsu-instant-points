from django.http import HttpResponse
from django.shortcuts import redirect

import requests
from bs4 import BeautifulSoup
from functional.streams import seq
import time
import re

def login(url, payload):
    try:
        sess = requests.Session()
        req = sess.post(url, data=payload)
        if req.status_code == 200:
            return sess
        else:
            return None
    except:
        return None

def get_rating_options(url, session):
    try:
        r = session.get(url)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'lxml')
            return [(r"https://info.swsu.ru"+entry['href'], entry.text) for entry in
                     soup.find("div", {"class": "block-list"}).find_all('a')]
        else:
            return None
    except:
        return None
    
def get_tds(tr):
    delete_unnecessary = tr.find_all("td")
    if len(delete_unnecessary) > 8:
        del delete_unnecessary[1]
        del delete_unnecessary[1]
        del delete_unnecessary[1]
        del delete_unnecessary[len(delete_unnecessary)-1]
    try:
        return list(map(lambda x: x.text, delete_unnecessary))
    except:
        return delete_unnecessary

    
def get_formated_rating(url, session):
    try:
        r = session.get(url)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'lxml')
            return seq(soup.find_all("tr")).map(get_tds).filter(lambda lst: len(lst) > 0).to_list()
    except:
        return None
    
def make_stylish_entry(datarow):
    try:
        coursename = re.sub(r"\(id\=\d+\)", "", datarow[0])
        res = f"<div class='subject'><div class='row'><div style='font-size: 22px; font-weight: bold;' class='row_value'>{coursename}"
        if datarow[1] == 'Экзамен':
            res += f" [Экзамен]</div></div>"
        elif datarow[1] == 'Зачет':
            res += f" [Зачет]</div></div>"
        res += f"<div class='row'><div class='row_value'>1.пос</div><div class='row_value'>1.усп</div><div class='row_value'>2.пос</div><div class='row_value'>2.усп</div><div class='row_value'>3.пос</div><div class='row_value'>3.усп</div><div class='row_value'>4.пос</div><div class='row_value'>4.усп</div></div>"
        res += f"<div class='row'><div class='row_value'>{datarow[2]}</div><div class='row_value'>{datarow[3]}</div><div class='row_value'>{datarow[4]}</div><div class='row_value'>{datarow[5]}</div><div class='row_value'>{datarow[6]}</div><div class='row_value'>{datarow[7]}</div><div class='row_value'>{datarow[8]}</div><div class='row_value'>{datarow[9]}</div></div>"
        res += f"<div class='row'><div class='row_value'>Деканатские</div><div class='row_value'>Преподавательские</div><div class='row_value'>Баллы за экзамен/зачет</div></div>"
        res += f"<div class='row'><div class='row_value'>{datarow[10]}</div><div class='row_value'>{datarow[11]}</div><div class='row_value'>{datarow[12]}</div></div>"
        res += f"<div class='row'><div class='row_value' style='font-weight: bold; font-size: 20px; margin-top: 30px;'>Итого: {datarow[13]}</div></div>"
        #res += f"<div class='row'><div class='row_value'>{datarow[13]}</div></div>"
        if datarow[1] == 'Экзамен':
            # res += f"<div class='row'><div class='row_value'>До 5</div></div>"
            points = int(datarow[13].strip())
            if points < 50:
                res += f"<div class='row'><div class='row_value' style='font-size: 26px; font-weight: bold; color: red;'>Баллов до 5: {85-points} (Оценка 2)</div></div>"
            elif points > 50 and points < 75:
                res += f"<div class='row'><div class='row_value' style='font-size: 26px; font-weight: bold; color: yellow;'>Баллов до 5: {85-points} (Оценка 3)</div></div>"
            elif points > 75 and points < 85:
                res += f"<div class='row'><div class='row_value' style='font-size: 26px; font-weight: bold; color: lightgreen;'>Баллов до 5: {85-points} (Оценка 4)</div></div>"
            elif points >= 85:
                res += f"<div class='row'><div class='row_value' style='font-size: 26px; font-weight: bold; color: green;'>Оценка 5</div></div>"
        elif datarow[1] == 'Зачет':
            # res += f"<div class='row'><div class='row_value'>До зачета</div></div>"
            points = int(datarow[13].strip())
            if points < 50:
                res += f"<div class='row'><div class='row_value' style='font-size: 26px; font-weight: bold; color: red;'>Баллов до зачета: {50-points}</div></div>"
            elif points >= 50:
                res += f"<div class='row'><div class='row_value' style='font-size: 26px; font-weight: bold; color: green;'>Зачет</div></div>"
        return res + "</div>"
    except:
        return ""

def get_html_of_points(pointlist):
    a = "<div style='width: 100%; max-width: 600px; display: flex; flex-direction: column; justify-content: center; align-items: center; align-content: center;'>"
    a += "".join([make_stylish_entry(datarow) for datarow in pointlist]) + "</div>"
    return a
    
def attach_styles():
    with open("styles.css") as r:
        return f"<style>{r.read()}</style>"

def begin_html():
    return '<html><head><body><script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>'

def return_failure(request):
     return HttpResponse(begin_html() + """
    <div style='width: 100%; height: 100%; display: flex; justify-content:center; align-content: center; align-items: center; flex-wrap: wrap;'>
        <h1 style='font-family: Arial, Helvetica, sans-serif; width: 100%; text-align: center; font-size: 60px;'>Мгновенный просмотр баллов ЮЗГУ</h1>
        <div style='display: flex; flex-wrap: wrap; width: 100%; max-width: 1000px; align-items: stretch; align-content: stretch;'>
        <input style='border: 2px solid red; font-weight: bold; background-color: white; font-family: Arial, Helvetica, sans-serif; font-size: 18px; flex-grow: 1; width: 40%; height: 40px;' type='text' id='swsu_login' placeholder='Ваш логин в info.swsu' />
        <input  style='border: 2px solid red; font-weight: bold; background-color: white; font-family: Arial, Helvetica, sans-serif; font-size: 18px; flex-grow: 1; width: 40%; height: 40px;' type='password' id='swsu_password' placeholder='Ваш пароль в info.swsu' />
        <input  style='border: 2px solid red; font-weight: bold; background-color: white; font-family: Arial, Helvetica, sans-serif; font-size: 18px; flex-grow: 1; width: 15%; height: 40px;' type='text' id='semester_id' placeholder='Семестр (цифра)' />
        <button class='send' style='font-weight: bold; font-family: Arial, Helvetica, sans-serif; font-size: 20px; flex-grow: 1; min-width: 100%; height: 40px;' id='view_points_button' onclick='view_points()'>Посмотреть баллы</button>
        </div>
    </div>
    <script>
        function view_points(){
            window.location.href = '/get_points?login=' + document.getElementById('swsu_login').value + "&password=" + document.getElementById('swsu_password').value + "&semester=" + document.getElementById('semester_id').value
        }
    </script>
    <style>
        .send{
            background-color: white;
            border: 1px solid black;
        }
        .send:hover{
            cursor: pointer;
            background-color: #647175;
        }
    </style>
    """ + "</body></html>")
def get_points(request):
    _login = request.GET.get("login", False)
    _password = request.GET.get("password", False)
    _semester = request.GET.get("semester", False)
    if _login and _password and _semester:
        try:
            _semester = int(_semester)
        except:
            return redirect("".join(request.path.split("/")[0:-2])+"/failure")
        login_uri = "https://info.swsu.ru/index.php?action=auth"
        payload = {'login': _login, "password": _password, "click_autorize": ""}
        rating_uri = f"https://info.swsu.ru/index.php?action=list_stud_reiting&semestr=00000000{_semester+1}" 
        _session = login(login_uri, payload)
        if _session:
            opt = get_formated_rating(rating_uri, _session)
            if opt:
                return HttpResponse("<html><body style='display: flex; flex-direction: column; align-items: center;'>" 
                + f"<h1 style='font-family: Arial, Helvetica, sans-serif; width: 100%; text-align: center; font-size: 60px;'>Ваши баллы за {_semester} семестр</h1>" 
                + get_html_of_points(opt)
                + """
                <style>
                    .row{
                        width: 100%;
                        flex-grow: 1;
                        display: flex;
                    }
                    .row_value{
                        flex-grow: 1;
                        word-wrap: break-word;
                        padding: 3px 3px 3px 3px;
                        text-align: center;
                        margin-bottom: 5px;
                        font-family: Arial, Helvetica, sans-serif;
                    }
                    .subject{
                        margin-bottom: 30px;
                        width: 100%;
                        background-color: #f2f2f2;
                        padding: 7px 7px 7px 7px;
                    }
                </style>
                """
                + "</body></html>")

    return redirect("".join(request.path.split("/")[0:-2])+"/failure")

def index(request):
    return HttpResponse(begin_html() + """
    <div style='width: 100%; height: 100%; display: flex; justify-content:center; align-content: center; align-items: center; flex-wrap: wrap;'>
        <h1 style='font-family: Arial, Helvetica, sans-serif; width: 100%; text-align: center; font-size: 60px;'>Мгновенный просмотр баллов ЮЗГУ</h1>
        <div style='display: flex; flex-wrap: wrap; width: 100%; max-width: 1000px; align-items: stretch; align-content: stretch;'>
        <input style='font-weight: bold; background-color: white; font-family: Arial, Helvetica, sans-serif; font-size: 20px; flex-grow: 1; min-width: 40%; height: 40px;' type='text' id='swsu_login' placeholder='Ваш логин в info.swsu' />
        <input  style='font-weight: bold; background-color: white; font-family: Arial, Helvetica, sans-serif; font-size: 20px; flex-grow: 1; min-width: 40%; height: 40px;' type='password' id='swsu_password' placeholder='Ваш пароль в info.swsu' />
        <input  style='font-weight: bold; background-color: white; font-family: Arial, Helvetica, sans-serif; font-size: 20px; flex-grow: 1; width: 5%; height: 40px;' type='text' id='semester_id' placeholder='Семестр (цифра)' />
        <button class='send' style='font-weight: bold; font-family: Arial, Helvetica, sans-serif; font-size: 20px; flex-grow: 1; min-width: 100%; height: 40px;' id='view_points_button' onclick='view_points()'>Посмотреть баллы</button>
        </div>
    </div>
    <script>
        function view_points(){
            window.location.href = '/get_points?login=' + document.getElementById('swsu_login').value + "&password=" + document.getElementById('swsu_password').value + "&semester=" + document.getElementById('semester_id').value
        }
    </script>
    <style>
        .send{
            background-color: white;
            border: 1px solid black;
        }
        .send:hover{
            cursor: pointer;
            background-color: #647175;
        }
    </style>
    """ + "</body></html>")