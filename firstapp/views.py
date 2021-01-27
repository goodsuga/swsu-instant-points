from django.http import HttpResponse
from django.shortcuts import redirect

import requests
from bs4 import BeautifulSoup
from functional.streams import seq
import time
import re

def login(url, payload):
    # URL -> string, строка с ссылкой, куда надо отправлять ПОСТ-запрос на логин
    # payload -> dict, Необходимые для логина данные (login, password, click_autorize). Click_autorize должен быть пустой строкой
    sess = requests.Session()   # Сессия нужна, чтобы после логина сохранить доступ к данным
    req = sess.post(url, data=payload)  # пост запрос на логин
    if req.status_code == 200:  # если залогиниться удалось, сервер вернет код 200. Сохраним сессию для будущего использования
        return sess


def get_tds(tr):
    # tr -> DOM-элемент "строка таблицы", полученный через beautiful soup;
    # функция просто вернет innerText всех td=детей=tr
    delete_unnecessary = tr.find_all("td")  
    if len(delete_unnecessary) > 8:     # В строке с баллами будет минимум 8 td: 4 контрольные точки, в каждой 2 раздела (успеваеомсть, посещаемость)
        del delete_unnecessary[1]   # Удалим несколько ненужных полей. семестр, где проводится экзамен, заказ допуска, группа
        del delete_unnecessary[1]
        del delete_unnecessary[1]
        del delete_unnecessary[len(delete_unnecessary)-1]
    try:
        return list(map(lambda x: x.text, delete_unnecessary))  # Попытаемся вернуть innerText всех td. Если коллекция пустая, может быть выкинуто исключение
    except:
        return delete_unnecessary   # Собственно если оно случается, то просто вернем пустую коллекцию. Она отфильтруется в get_formated_rating

    
def get_formated_rating(url, session):
    # url -> string, ссылка на страницу с баллами.
    # session -> объект сессии, в которой произведен логин. Получать через login()
    r = session.get(url)    # Запрашиваем баллы, если все ок (200), то создае парсер и цепляем все табличные строчки, из каждой вытаскиваем innerText всех td
    if r.status_code == 200:    # Фильтруем, отбрасывая пустые коллекции
        soup = BeautifulSoup(r.text, 'lxml')
        return seq(soup.find_all("tr")).map(get_tds).filter(lambda lst: len(lst) > 0).to_list()
    
def make_stylish_entry(datarow):
    # datarow -> list<string>, список с уже готовыми к отрисовке данными из tr
    # 0 - имя предмета, 1 = тип контроля, 2-9 - контрольные точки, усп, пос, 10-12 - декан. препод. экзаменац./зачетные баллы 13 - сумма баллов
    try:
        coursename = re.sub(r"\(id\=\d+\)", "", datarow[0]) # Вырезаем нелепое (id=XXXXXX) из имени курса
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
                res += f"<div class='row'><div class='row_value' style='font-size: 26px; font-weight: bold; color: #FF3423;'>Баллов до 5: {85-points} (Оценка 2)</div></div>"
            elif points > 50 and points < 70:
                res += f"<div class='row'><div class='row_value' style='font-size: 26px; font-weight: bold; color: #FF8000;'>Баллов до 5: {85-points} (Оценка 3)</div></div>"
            elif points > 70 and points < 85:
                res += f"<div class='row'><div class='row_value' style='font-size: 26px; font-weight: bold; color: #FCD02F;'>Баллов до 5: {85-points} (Оценка 4)</div></div>"
            elif points >= 85:
                res += f"<div class='row'><div class='row_value' style='font-size: 26px; font-weight: bold; color: #22E107;'>Оценка 5</div></div>"
        elif datarow[1] == 'Зачет':
            # res += f"<div class='row'><div class='row_value'>До зачета</div></div>"
            points = int(datarow[13].strip())
            if points < 50:
                res += f"<div class='row'><div class='row_value' style='font-size: 26px; font-weight: bold; color: #FF3423;'>Баллов до зачета: {50-points}</div></div>"
            elif points >= 50:
                res += f"<div class='row'><div class='row_value' style='font-size: 26px; font-weight: bold; color: #22E107;'>Зачет</div></div>"
        return res + "</div>"
    except:
        return ""

def get_html_of_points(pointlist):
    # pointlist -> list<list<string>>, просто куча списков с спарсенными td-шками 
    a = "<div style='width: 100%; max-width: 600px; display: flex; flex-direction: column; justify-content: center; align-items: center; align-content: center;' id='table'>"
    a += "".join([make_stylish_entry(datarow) for datarow in pointlist]) + "</div>" # для каждой строки tr делаем стильную отрисовку
    return a

def begin_html():
    # Просто вспомогательная функция для простого откытия html-кода и загрузки jquery
    return '<html><head><body><script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>'

def handler404(request, exception):
    return redirect("".join(request.path.split("/")[0:-2])+"/failure")

def handler500(request):
    return redirect("".join(request.path.split("/")[0:-2])+"/failure")

def return_failure(request):
    # Просто отрисовать главную страницу 
    return HttpResponse(begin_html() + """
    <div style='width: 100%; display: flex; justify-content:center; align-content: center; align-items: center; flex-wrap: wrap;' id='wrapper'>
        <h1 style='font-family: Arial, Helvetica, sans-serif; width: 100%; text-align: center; font-size: 60px;'>Мгновенный просмотр баллов ЮЗГУ</h1>
        <div style='display: flex; flex-wrap: wrap; width: 100%; max-width: 1000px; align-items: stretch; align-content: stretch;'>
        <input style='border: 2px solid red; font-weight: bold; background-color: white; font-family: Arial, Helvetica, sans-serif; font-size: 20px; flex-grow: 1; min-width: 40%; height: 40px;' type='text' id='swsu_login' placeholder='Ваш логин в info.swsu' />
        <input  style='border: 2px solid red; font-weight: bold; background-color: white; font-family: Arial, Helvetica, sans-serif; font-size: 20px; flex-grow: 1; min-width: 40%; height: 40px;' type='password' id='swsu_password' placeholder='Ваш пароль в info.swsu' />
        <input  style='border: 2px solid red; font-weight: bold; background-color: white; font-family: Arial, Helvetica, sans-serif; font-size: 20px; flex-grow: 1; width: 5%; height: 40px;' type='text' id='semester_id' placeholder='Семестр (цифра)' />
        <button class='send' style='font-weight: bold; font-family: Arial, Helvetica, sans-serif; font-size: 20px; flex-grow: 1; min-width: 100%; height: 40px;' id='view_points_button' onclick='view_points()'>Посмотреть баллы</button>
        <button class='send' style='margin-top: 30px; margin-bottom: 0px; font-weight: bold; font-family: Arial, Helvetica, sans-serif; font-size: 20px; flex-grow: 1; min-width: 100%; height: 40px;' id='view_points_button' onclick='view_cached()'>Сохраненные баллы (если ЮЗГУ лежит)</button>
        </div>
    </div>
    <script>
        function view_points(){
            window.location.href = '/get_points?login=' + document.getElementById('swsu_login').value + "&password=" + document.getElementById('swsu_password').value + "&semester=" + document.getElementById('semester_id').value;
        }
    </script>
    <script>
        
        function view_cached(){
           // window.location.href = "/failure";
           var cached = window.localStorage.getItem('cached');
        if(cached != null && cached != ""){
            console.log('Кэш доступен');
            $("#wrap_cache").remove();
            $("h2").remove();
            $('body').append('<h2 style="margin-top: 30px; font-size: 24px; width: 100%; text-align: center;">Вам показана последняя сохраненная копия баллов</h2>');
            $('body').append('<div id="wrap_cache" style="display: flex; width: 100%; justify-content: center;"></div>')
            $("#wrap_cache").append("<div id='cachedview' style='height: 20000px;'></div>");
            $('#cachedview').html(cached);
            $('#cachedview').attr('style', 'width: 100%; max-width: 600px; display: flex; flex-direction: column; justify-content: center; align-items: center; align-content: center;');
        } else { console.log("Кэш пуст"); }
        }
        
        if(window.localStorage.getItem('cached') == null || window.localStorage.getItem('cached') == ""){
            $('.send').last().remove();
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
    """ + "</body></html>") 

def get_points(request):
    # get_points?login=...&password=...&semester=... - такой должна быть ссылка при отсылке get-запроса на страницу
    _login = request.GET.get("login", False)
    _password = request.GET.get("password", False)
    _semester = request.GET.get("semester", False)
    if _login and _password and _semester:  # работаем дальше, только если все три параеметра были переданы (и если семестр - это число)
        _semester = int(_semester)  
        login_uri = "https://info.swsu.ru/index.php?action=auth" 
        payload = {'login': _login, "password": _password, "click_autorize": ""}    # готовим данные для логина
        rating_uri = f"https://info.swsu.ru/index.php?action=list_stud_reiting&semestr=00000000{_semester+1}"   # сейчас семестр в ссылке равен собственно семестру + 1
        _session = login(login_uri, payload)
        opt = get_formated_rating(rating_uri, _session)
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
                <script>
                    if(document.getElementsByTagName("body")[0].innerHTML.length > 0){
                        try{
                            if(document.getElementById('table').innerHTML != ""){
                                window.localStorage.setItem('cached', document.getElementById('table').innerHTML);
                            }
                        } catch { }
                    }
                </script>
                """
                + "</body></html>")

    raise Exception("Все пошло не так!")
    return redirect("".join(request.path.split("/")[0:-2])+"/failure") # если где-то по пути что-то пошло не так, просто вернуть ошибку

def index(request):
    # Просто отрисовать главную страницу 
    return HttpResponse(begin_html() + """
    <div style='width: 100%; display: flex; justify-content:center; align-content: center; align-items: center; flex-wrap: wrap;' id='wrapper'>
        <h1 style='font-family: Arial, Helvetica, sans-serif; width: 100%; text-align: center; font-size: 60px;'>Мгновенный просмотр баллов ЮЗГУ</h1>
        <div style='display: flex; flex-wrap: wrap; width: 100%; max-width: 1000px; align-items: stretch; align-content: stretch;'>
        <input style='font-weight: bold; background-color: white; font-family: Arial, Helvetica, sans-serif; font-size: 20px; flex-grow: 1; min-width: 40%; height: 40px;' type='text' id='swsu_login' placeholder='Ваш логин в info.swsu' />
        <input  style='font-weight: bold; background-color: white; font-family: Arial, Helvetica, sans-serif; font-size: 20px; flex-grow: 1; min-width: 40%; height: 40px;' type='password' id='swsu_password' placeholder='Ваш пароль в info.swsu' />
        <input  style='font-weight: bold; background-color: white; font-family: Arial, Helvetica, sans-serif; font-size: 20px; flex-grow: 1; width: 5%; height: 40px;' type='text' id='semester_id' placeholder='Семестр (цифра)' />
        <button class='send' style='font-weight: bold; font-family: Arial, Helvetica, sans-serif; font-size: 20px; flex-grow: 1; min-width: 100%; height: 40px;' id='view_points_button' onclick='view_points()'>Посмотреть баллы</button>
        <button class='send' style='margin-top: 30px; margin-bottom: 0px; font-weight: bold; font-family: Arial, Helvetica, sans-serif; font-size: 20px; flex-grow: 1; min-width: 100%; height: 40px;' id='view_points_button' onclick='view_cached()'>Сохраненные баллы (если ЮЗГУ лежит)</button>
        </div>
    </div>
    <script>
        function view_points(){
            window.location.href = '/get_points?login=' + document.getElementById('swsu_login').value + "&password=" + document.getElementById('swsu_password').value + "&semester=" + document.getElementById('semester_id').value;
        }
    </script>
    <script>
        
        function view_cached(){
           // window.location.href = "/failure";
           var cached = window.localStorage.getItem('cached');
        if(cached != null && cached != ""){
            console.log('Кэш доступен');
            $("#wrap_cache").remove();
            $("h2").remove();
            $('body').append('<h2 style="margin-top: 30px; font-size: 24px; width: 100%; text-align: center;">Вам показана последняя сохраненная копия баллов</h2>');
            $('body').append('<div id="wrap_cache" style="display: flex; width: 100%; justify-content: center;"></div>')
            $("#wrap_cache").append("<div id='cachedview' style='height: 20000px;'></div>");
            $('#cachedview').html(cached);
            $('#cachedview').attr('style', 'width: 100%; max-width: 600px; display: flex; flex-direction: column; justify-content: center; align-items: center; align-content: center;');
        } else { console.log("Кэш пуст"); }
        }
        
        if(window.localStorage.getItem('cached') == null || window.localStorage.getItem('cached') == ""){
            $('.send').last().remove();
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
    """ + "</body></html>") 