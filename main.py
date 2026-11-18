from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import pymysql
import shutil
import os
from urllib.parse import quote

app = FastAPI()

# sesja
app.add_middleware(SessionMiddleware, secret_key="tajny_klucz_do_projektu_szkolnego")

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# łączenie z bazą danych
def get_db():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='car_rental_place_db',
        cursorclass=pymysql.cursors.DictCursor
    )

# filtrowanie samochodów po marce
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
    
    # POPRAWKA: request jako pierwszy argument
    return templates.TemplateResponse(request, "index.html", {
        "request": request,
        "cars": cars,
        "brands": brands,
        "selected_make": make
    })

# rejestracja użytkownika
@app.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse(request, "register.html", {"request": request})

@app.post("/register")
def register_user(username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    connection = get_db()
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO users (username, email, password, role)
            VALUES (%s, %s, %s, 'user')
        """, (username, email, password))
        connection.commit()
    connection.close()
    return RedirectResponse(url="/login", status_code=303)

# logowanie i wylogowywanie użytkownika
@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"request": request})

@app.post("/login")
def login_user(request: Request, email: str = Form(...), password: str = Form(...)):
    connection = get_db()
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM users WHERE email = %s AND password = %s",
            (email, password)
        )
        user = cursor.fetchone()

    connection.close()

    if user:
        request.session["user_id"] = user["id"]
        request.session["username"] = user["username"]
        request.session["role"] = user["role"]

        if user["role"] == "admin":
            return RedirectResponse(url="/admin", status_code=303)

        return RedirectResponse(url="/", status_code=303)

    return {"error": "Błędny e-mail lub hasło!"}


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)


@app.post("/reserve/{car_id}")
def reserve_car(
    request: Request,
    car_id: int,
    start_date: str = Form(...),
    end_date: str = Form(...)
):
    user_id = request.session.get("user_id")

    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    if end_date < start_date:
        return RedirectResponse(
            url=f"/?error={quote('Return date must be after the pick-up date.')}#fleet",
            status_code=303
        )

    connection = get_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id FROM reservations
                WHERE car_id = %s
                  AND status != 'Cancelled'
                  AND start_date <= %s
                  AND end_date >= %s
                LIMIT 1
            """, (car_id, end_date, start_date))

            conflict = cursor.fetchone()

            if conflict:
                error = (
                    "This car is already reserved for the selected dates. "
                    "Please choose different dates."
                )
                return RedirectResponse(
                    url=f"/?error={quote(error)}#fleet",
                    status_code=303
                )

            cursor.execute("""
                INSERT INTO reservations (user_id, car_id, start_date, end_date, status)
                VALUES (%s, %s, %s, %s, 'Confirmed')
            """, (user_id, car_id, start_date, end_date))

            connection.commit()
    finally:
        connection.close()

    return RedirectResponse(url="/my-reservations", status_code=303)

# panel użytkownika
@app.get("/my-reservations")
def my_reservations(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
        
    connection = get_db()
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT reservations.*, cars.brand, cars.model, cars.price_per_day, cars.image 
            FROM reservations 
            JOIN cars ON reservations.car_id = cars.id 
            WHERE reservations.user_id = %s
        """, (user_id,))
        reservations = cursor.fetchall()
    connection.close()
    
    return templates.TemplateResponse(request, "my_reservations.html", {
        "request": request, 
        "reservations": reservations,
        "username": request.session.get("username")
    })

# panel administratora
@app.get("/admin")
def admin_panel(request: Request):
    if request.session.get("role") != "admin":
        return RedirectResponse(url="/login", status_code=303)
        
    connection = get_db()
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM cars")
        cars = cursor.fetchall()
    connection.close()
    
    return templates.TemplateResponse(request, "admin.html", {"request": request, "cars": cars})

@app.post("/admin/add-car")
def add_car(
    request: Request, 
    brand: str = Form(...), 
    model: str = Form(...), 
    category: str = Form(...), 
    price_per_day: float = Form(...),
    image: UploadFile = File(...)
):
    if request.session.get("role") != "admin":
        return RedirectResponse(url="/login", status_code=303)
        
    image_filename = os.path.basename(image.filename)
    image_path = os.path.join("static", image_filename)
    with open(image_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
        
    connection = get_db()
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO cars (brand, model, category, price_per_day, image)
            VALUES (%s, %s, %s, %s, %s)
        """, (brand, model, category, price_per_day, image_filename))
        connection.commit()
    connection.close()
    
    return RedirectResponse(url="/admin", status_code=303)

# anulowanie rezerwacji
@app.post("/cancel/{reservation_id}")
def cancel_reservation(request: Request, reservation_id: int):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
        
    connection = get_db()
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM reservations WHERE id = %s AND user_id = %s", (reservation_id, user_id))
        connection.commit()
    connection.close()
    
    return RedirectResponse(url="/my-reservations", status_code=303)

@app.get("/cancel/{reservation_id}")
def cancel_reservation_page(request: Request, reservation_id: int):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    connection = get_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT reservations.*, cars.brand, cars.model
                FROM reservations
                JOIN cars ON reservations.car_id = cars.id
                WHERE reservations.id = %s
                  AND reservations.user_id = %s
            """, (reservation_id, user_id))
            reservation = cursor.fetchone()
    finally:
        connection.close()

    if not reservation:
        return RedirectResponse(url="/my-reservations", status_code=303)

    return templates.TemplateResponse(request, "cancel_reservation.html", {
        "request": request,
        "reservation": reservation
    })