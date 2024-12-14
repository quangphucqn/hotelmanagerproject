import unittest

from sqlalchemy.sql.functions import count

from utils import find_booking_note
from hotelapp import app, login

def test_find_booking_note_success():
        customer_name = 'Lê Hoàng Phúc'
        phone_number = '0337367643'
        result = find_booking_note(customer_name, phone_number)
        if not result:
            print("cccccc")
        else:
             print(result)

if __name__ == '__main__':
    with app.app_context():
        test_find_booking_note_success()

