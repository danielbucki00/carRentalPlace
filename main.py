from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import pymysql

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

# konfiguracja szablonów
templates = Jinja2Templates(directory="templates")

# łączenie z bazą danych
def get_db():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='car_rental_db',
        cursorclass=pymysql.cursors.DictCursor
    )

# główna strona 
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
    
    # przekazanie danych do htmla
    return templates.TemplateResponse("index.html", {
        "request": request,
        "cars": cars,
        "brands": brands,
        "selected_make": make
    })

# logowanie 
@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


#blokada podwójnych rezerwacji
@app.post("/reserve/{car_id}")
def reserve_car(car_id: int, start_date: str = Form(...), end_date: str = Form(...)):
    connection = get_db()
    with connection.cursor() as cursor:
        
        # 1. Sprawdzanie czy daty nie kolidują z inną rezerwacją tego auta
        cursor.execute("""
            SELECT * FROM reservations 
            WHERE car_id = %s 
            AND status != 'Cancelled'
            AND NOT (end_date < %s OR start_date > %s)
        """, (car_id, start_date, end_date))
        
        conflict = cursor.fetchone()
        
        if conflict:
            connection.close()
            # Zwracamy prosty komunikat o konflikcie
            return {"error": " Wybrany samochód jest już zajęty w tym terminie! Wróć i wybierz inne daty."}
        
        # 2. Jeśli termin jest wolny – zapisujemy rezerwację w bazie
        user_id = 1  # Na razie na sztywno, potem zastąpimy zalogowanym użytkownikiem
        cursor.execute("""
            INSERT INTO reservations (user_id, car_id, start_date, end_date, status)
            VALUES (%s, %s, %s, %s, 'Confirmed')
        """, (user_id, car_id, start_date, end_date))
        
        connection.commit()
    
    connection.close()
    
    return RedirectResponse(url="/", status_code=303)