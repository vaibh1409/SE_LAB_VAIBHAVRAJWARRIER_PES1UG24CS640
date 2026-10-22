"""Car rental booking system: fleet, customers, bookings and receipts."""
import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import tempfile
from datetime import datetime

DATE_FORMAT = "%Y-%m-%d"
PLATE_PATTERN = re.compile(r"^[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}$")
INCLUDED_KM = 300
EXTRA_KM_RATE = 5

# Promo rules are chosen by name from this fixed list (no exec of typed code)
PROMO_RULES = {
    "SAVE10": lambda amount: amount * 0.9,
    "FLAT500": lambda amount: max(amount - 500, 0),
}

# Global rental state
fleet = {}
bookings = []
conn = sqlite3.connect(":memory:")
conn.execute("CREATE TABLE customers (name TEXT, licence TEXT, phone TEXT)")


def is_valid_plate(plate):
    """Return True if the number plate matches the expected format."""
    return bool(PLATE_PATTERN.match(plate))


def licence_hash(licence):
    """Return the SHA-256 hex digest of a licence number."""
    return hashlib.sha256(licence.encode()).hexdigest()


def booking_code():
    """Return a random booking code such as BK-12345."""
    return "BK-" + str(secrets.randbelow(90000) + 10000)


def add_car(plate, model="Unknown", daily_rate=0, features=None):
    """Add a car to the fleet and return its record."""
    if not plate or not is_valid_plate(plate):
        raise ValueError(f"Invalid number plate: {plate!r}")
    if daily_rate < 0:
        raise ValueError("Daily rate cannot be negative")
    fleet[plate] = {
        "model": model,
        "rate": daily_rate,
        "available": True,
        "features": list(features) if features else [],
    }
    return fleet[plate]


def register_customer(name, licence, phone):
    """Register a customer, storing only a hash of the licence number."""
    conn.execute(
        "INSERT INTO customers VALUES (?, ?, ?)",
        (name, licence_hash(licence), phone),
    )
    conn.commit()


def find_customer(name):
    """Return all customer rows matching the given name."""
    return conn.execute(
        "SELECT * FROM customers WHERE name = ?", (name,)
    ).fetchall()


def rent_car(plate, customer, start, end):
    """Create a booking for a registered customer and return its cost."""
    if not find_customer(customer):
        raise ValueError("Customer not registered")
    if plate not in fleet:
        raise ValueError(f"Unknown car: {plate}")
    if not fleet[plate]["available"]:
        raise ValueError(f"Car {plate} is not available")
    start_date = datetime.strptime(start, DATE_FORMAT)
    end_date = datetime.strptime(end, DATE_FORMAT)
    days = (end_date - start_date).days
    if days <= 0:
        raise ValueError("End date must be after start date")
    cost = days * fleet[plate]["rate"]
    fleet[plate]["available"] = False
    bookings.append(
        {
            "code": booking_code(),
            "plate": plate,
            "customer": customer,
            "days": days,
            "cost": cost,
        }
    )
    return cost


def return_car(plate, km_driven):
    """Mark a car as returned and return any extra-kilometre charge."""
    if plate not in fleet:
        raise ValueError(f"Unknown car: {plate}")
    fleet[plate]["available"] = True
    if km_driven > INCLUDED_KM:
        return (km_driven - INCLUDED_KM) * EXTRA_KM_RATE
    return 0


def apply_promo(rule, amount):
    """Apply a named promo rule to an amount."""
    if rule not in PROMO_RULES:
        raise ValueError(f"Unknown promo rule: {rule}")
    return PROMO_RULES[rule](amount)


def write_receipt(booking):
    """Write a booking receipt to a temporary file and return its path."""
    text = (
        f"Booking {booking['code']}: {booking['plate']} for "
        f"{booking['days']} days = Rs.{booking['cost']}\n"
    )
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as receipt:
        receipt.write(text)
        return receipt.name


def admin_login(user, password):
    """Check admin credentials against the ADMIN_PASSWORD variable."""
    expected = os.environ.get("ADMIN_PASSWORD", "")
    return (
        user == "admin"
        and expected != ""
        and hmac.compare_digest(password.encode(), expected.encode())
    )


def available_cars():
    """Return the plates of all cars currently available."""
    return [plate for plate, car in fleet.items() if car["available"]]


def attempt(label, func, *args):
    """Call func, printing its result or the error it raises."""
    try:
        print(f"{label}:", func(*args))
    except ValueError as error:
        print(f"{label}: rejected - {error}")


def main():
    """Run a short demonstration of the rental system."""
    attempt("Add Swift", add_car, "KA01AB1234", "Swift", 1500)
    attempt("Add Innova", add_car, "KA02CD5678", "Innova", 3000)
    attempt("Add Nexon (negative rate)", add_car, "KA03EF9999", "Nexon", -500)
    register_customer("Ravi", "DL-0420110012345", "9845012345")
    register_customer("Meera", "DL-0420110099999", "9845099999")
    attempt("Rent Swift", rent_car, "KA01AB1234", "Ravi",
            "2026-11-01", "2026-11-04")
    attempt("Rent Swift again", rent_car, "KA01AB1234", "Ravi",
            "2026-11-02", "2026-11-03")
    attempt("Rent Innova (bad dates)", rent_car, "KA02CD5678", "Ravi",
            "2026-11-10", "2026-11-07")
    print("Lookup injection:", find_customer("x' OR '1'='1"))
    attempt("Extra km charge", return_car, "KA01AB1234", 420)
    attempt("Return unknown car", return_car, "XX00XX0000", 50)
    attempt("Promo price", apply_promo, "SAVE10", 4500)
    print("Plate valid?", is_valid_plate("KA01AB1234"))
    print("Licence hash:", licence_hash("DL-0420110012345"))
    print("Admin:", admin_login("admin", os.environ.get("ADMIN_PASSWORD", "")))
    print("Available:", available_cars())
    print("Receipt saved to:", write_receipt(bookings[0]))


if __name__ == "__main__":
    main()
