from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import pymysql

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"),name="static")

# konfiguracja szablonów
templates = Jinja2Templates(directory="templates")

#łączenie z bazą danych
def get_db():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='car_rental_db',
        cursorclass=pymysql.cursors.DictCursor
    )

#główna
@app.get("/")
def home(request: Request, make: str = "All makes"):
    connection = get_db()
    with connection.cursor() as cursor:
        
        if make and make != "All makes":
            cursor.execute("SELECT * FROM cars WHERE brand = %s", (make,))
        else:
            cursor.execute("SELECT * FROM cars")
        cars = cursor.fetchall()
        
        
        cursor.execute("SELECT DISTINCT brand FROM cars")
        brands = [row['brand'] for row in cursor.fetchall()]
        
    connection.close()
    
    #przekazanie danych do htmla
    return templates.TemplateResponse("index.html", {
        "request": request,
        "cars": cars,
        "brands": brands,
        "selected_make": make
    })

#logowanie
@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})