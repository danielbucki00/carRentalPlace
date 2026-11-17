# CarRentalPlace 🚗

## O projekcie

CarRentalPlace to aplikacja internetowa służąca do wypożyczania samochodów przez internet. Użytkownicy mogą przeglądać dostępne pojazdy, sprawdzać ich ceny i rezerwować je na wybrany termin. Administrator zarządza samochodami oraz rezerwacjami.

## Technologie

- **Frontend:** HTML, CSS, JavaScript, Tailwind CSS, Jinja2
- **Backend:** Python, FastAPI, Uvicorn
- **Baza danych:** MySQL
- **Biblioteki:** PyMySQL, Starlette Session Middleware
- **Środowisko bazy danych:** XAMPP / MySQL

## Główne funkcje

### Użytkownik

- Rejestracja i logowanie
- Wylogowywanie z konta
- Przeglądanie dostępnych samochodów
- Filtrowanie samochodów po marce
- Wyświetlanie cen za dzień
- Rezerwacja samochodu na wybrany termin
- Sprawdzanie konfliktów terminów rezerwacji
- Podgląd własnych rezerwacji
- Anulowanie własnych rezerwacji
- Tryb jasny i ciemny

### Administrator

- Dodawanie nowych samochodów
- Zarządzanie samochodami i rezerwacjami

## Uruchomienie projektu

1. Zainstaluj Python, Node.js oraz XAMPP.
2. W XAMPP uruchom usługę **MySQL**.
3. Otwórz phpMyAdmin i utwórz bazę danych `car_rental_db`.
4. Zaimportuj plik `car_rental_place_db.sql`.
5. Zainstaluj zależności Pythona:

   ```bash
   pip install fastapi uvicorn jinja2 python-multipart itsdangerous pymysql
   ```
6. Zainstaluj zależności Tailwind:
    ```bash 
    npm install
    ```
7. Uruchom kompilator Tailwind:
    ```bash
    npx @tailwindcss/cli -i ./static/css/input.css -o ./static/css/app.css --watch
    ```
8. W drugim terminalu uruchom aplikację:
    ```bash
    uvicorn main:app --reload
    ```
9. Otwórz aplikację w przeglądarce: http://127.0.0.1:8000