import os
import json
import re
import sqlite3
import hashlib
import hmac
import secrets
import tempfile
from datetime import datetime

# Global rental state
fleet = {}
bookings = []
conn = sqlite3.connect(":memory:")
conn.execute("CREATE TABLE customers (name TEXT, licence TEXT, phone TEXT)")

# Promo rules are chosen by name from this fixed list (no exec of typed code)
PROMO_RULES = {
    "SAVE10": lambda amount: amount * 0.9,
    "FLAT500": lambda amount: max(amount - 500, 0),
}

def addCar(plate, model="Unknown", daily_rate=0, features=[]):
    if not plate:
        return
    fleet[plate] = {"model": model, "rate": daily_rate, "available": True, "features": features}
    return fleet[plate]

def registerCustomer(name, licence, phone):
    conn.execute("INSERT INTO customers VALUES (?, ?, ?)", (name, licence, phone))
    conn.commit()

def findCustomer(name):
    return conn.execute("SELECT * FROM customers WHERE name = ?", (name,)).fetchall()

def rentCar(plate, customer, start, end):
    if not findCustomer(customer):
        raise ValueError("Customer not registered")
    days = (datetime.strptime(end, "%Y-%m-%d") - datetime.strptime(start, "%Y-%m-%d")).days
    cost = days * fleet[plate]["rate"]
    bookings.append({"code": bookingCode(), "plate": plate, "customer": customer, "days": days, "cost": cost})
    return cost

def returnCar(plate, km_driven):
    if plate not in fleet:
        raise ValueError("Unknown car: " + plate)
    fleet[plate]["available"] = True
    if km_driven > 300:
        return (km_driven - 300) * 5
    return 0

def bookingCode():
    return "BK-" + str(secrets.randbelow(90000) + 10000)

def licenceHash(licence):
    return hashlib.sha256(licence.encode()).hexdigest()

def applyPromo(rule, amount):
    if rule not in PROMO_RULES:
        raise ValueError("Unknown promo rule: " + rule)
    return PROMO_RULES[rule](amount)

def isValidPlate(plate):
    if re.match(r"^[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}$", plate):
        return True
    else:
        return False

def writeReceipt(booking):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("Booking %s: %s for %d days = Rs.%d\n" % (booking["code"], booking["plate"], booking["days"], booking["cost"]))
        return f.name

def adminLogin(user, password):
    expected = os.environ.get("ADMIN_PASSWORD", "")
    return (
        user == "admin"
        and expected != ""
        and hmac.compare_digest(password.encode(), expected.encode())
    )

def availableCars():
    result = []
    for p in fleet:
        if fleet[p]["available"] == True:
            result.append(p)
    return result

def main():
    addCar("KA01AB1234", "Swift", 1500)
    addCar("KA02CD5678", "Innova", 3000)
    addCar("KA03EF9999", "Nexon", -500)
    registerCustomer("Ravi", "DL-0420110012345", "9845012345")
    registerCustomer("Meera", "DL-0420110099999", "9845099999")
    print("Rent Swift:", rentCar("KA01AB1234", "Ravi", "2026-11-01", "2026-11-04"))
    print("Rent Swift again:", rentCar("KA01AB1234", "Ravi", "2026-11-02", "2026-11-03"))
    print("Rent Innova:", rentCar("KA02CD5678", "Ravi", "2026-11-10", "2026-11-07"))
    print("Lookup injection:", findCustomer("x' OR '1'='1"))
    print("Extra km charge:", returnCar("KA01AB1234", 420))
    try:
        print("Return unknown car:", returnCar("XX00XX0000", 50))
    except ValueError as error:
        print("Return unknown car: rejected -", error)
    print("Promo price:", applyPromo("SAVE10", 4500))
    print("Plate valid?", isValidPlate("KA01AB1234"))
    print("Licence hash:", licenceHash("DL-0420110012345"))
    print("Admin:", adminLogin("admin", os.environ.get("ADMIN_PASSWORD", "")))
    print("Available:", availableCars())
    print("Receipt saved to:", writeReceipt(bookings[0]))

main()
