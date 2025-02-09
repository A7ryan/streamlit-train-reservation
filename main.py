import streamlit as st
import sqlite3
import pandas as pd

# Database
conn = sqlite3.connect('railway.db', check_same_thread=False)
c = conn.cursor()


def create_db():
    c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS employees (employee_id TEXT, password TEXT, designation TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS trains (train_number TEXT PRIMARY KEY, train_name TEXT, departure_date TEXT, start_destination TEXT, end_destination TEXT)")
    conn.commit()

create_db()


def add_train(train_number, train_name, departure_date, start_destination, end_destination):
    c.execute("INSERT INTO trains (train_number, train_name, departure_date, start_destination, end_destination) VALUES (?, ?, ?, ?, ?)",
              (train_number, train_name, departure_date, start_destination, end_destination))
    conn.commit()
    create_seat_table(train_number)


def create_seat_table(train_number):
    c.execute(f"""
        CREATE TABLE IF NOT EXISTS seats_{train_number} (
            seat_number INTEGER PRIMARY KEY,
            seat_type TEXT,
            booked INTEGER DEFAULT 0,
            passenger_name TEXT,
            passenger_age INTEGER,
            passenger_gender TEXT
        )
    """)
    conn.commit()

    # Add 50 Seats
    for i in range(1, 51):
        seat_type = categorize_seat(i)
        c.execute(f"INSERT INTO seats_{train_number} (seat_number, seat_type, booked) VALUES (?, ?, ?)", (i, seat_type, 0))
    conn.commit()


def categorize_seat(seat_number):
    if seat_number % 10 in [0, 4, 5, 9]:
        return "Window"
    elif seat_number % 10 in [2, 3, 6, 7]:
        return "Aisle"
    else:
        return "Middle"


def view_trains():
    c.execute("SELECT * FROM trains")
    trains = c.fetchall()
    return trains


def view_seats(train_number):
    c.execute(f"SELECT seat_number, seat_type, booked, COALESCE(passenger_name, 'N/A') FROM seats_{train_number}")
    return c.fetchall()


def book_ticket(train_number, passenger_name, passenger_gender, passenger_age, seat_type):
    c.execute(f"SELECT seat_number FROM seats_{train_number} WHERE booked=0 AND seat_type=? ORDER BY seat_number ASC", (seat_type,))
    seat = c.fetchone()

    if seat:
        seat_number = seat[0]
        c.execute(f"""
            UPDATE seats_{train_number}
            SET booked=1, passenger_name=?, passenger_age=?, passenger_gender=?
            WHERE seat_number=?
        """, (passenger_name, passenger_age, passenger_gender, seat_number))
        conn.commit()
        st.success(f"Ticket Booked! Seat Number: {seat_number}")
    else:
        st.error("No available seats of this type.")


def cancel_ticket(train_number, seat_number):
    c.execute(f"""
        UPDATE seats_{train_number}
        SET booked=0, passenger_name=NULL, passenger_age=NULL, passenger_gender=NULL
        WHERE seat_number=?
    """, (seat_number,))
    conn.commit()
    st.success("Ticket Cancelled Successfully!")


def delete_train(train_number):
    c.execute("DELETE FROM trains WHERE train_number=?", (train_number,))
    c.execute(f"DROP TABLE IF EXISTS seats_{train_number}")
    conn.commit()
    st.success("Train Deleted Successfully!")


st.title("Railway Reservation System")

menu = st.sidebar.selectbox("Choose Option", ["Add Train", "View Trains", "Book Ticket", "Cancel Ticket", "View Seats", "Delete Train"])


if menu == "Add Train":
    st.subheader("Add a New Train")
    with st.form("add_train"):
        train_number = st.text_input("Train Number")
        train_name = st.text_input("Train Name")
        departure_date = st.date_input("Departure Date")
        start_destination = st.text_input("Start Destination")
        end_destination = st.text_input("End Destination")
        submit = st.form_submit_button("Add Train")

        if submit and train_number and train_name and start_destination and end_destination:
            add_train(train_number, train_name, str(departure_date), start_destination, end_destination)
            st.success("Train Added Successfully!")

elif menu == "View Trains":
    st.subheader("All Trains")
    trains = view_trains()
    if trains:
        df = pd.DataFrame(trains, columns=["Train Number", "Train Name", "Departure Date", "Start Destination", "End Destination"])
        st.dataframe(df)
    else:
        st.warning("No trains available.")

elif menu == "Book Ticket":
    st.subheader("Book a Ticket")
    train_number = st.text_input("Enter Train Number")
    seat_type = st.selectbox("Seat Type", ["Aisle", "Middle", "Window"])
    passenger_name = st.text_input("Passenger Name")
    passenger_age = st.number_input("Passenger Age", min_value=1, max_value=100)
    passenger_gender = st.selectbox("Passenger Gender", ["Male", "Female"])

    if st.button("Book Ticket"):
        if train_number and passenger_name and passenger_age:
            book_ticket(train_number, passenger_name, passenger_gender, passenger_age, seat_type)

elif menu == "Cancel Ticket":
    st.subheader("Cancel a Ticket")
    train_number = st.text_input("Enter Train Number")
    seat_number = st.number_input("Enter Seat Number", min_value=1)

    if st.button("Cancel Ticket"):
        if train_number and seat_number:
            cancel_ticket(train_number, seat_number)

elif menu == "View Seats":
    st.subheader("View Train Seats")
    train_number = st.text_input("Enter Train Number")
    if st.button("View Seats"):
        if train_number:
            seats = view_seats(train_number)
            df = pd.DataFrame(seats, columns=["Seat Number", "Type", "Booked", "Passenger Name"])
            st.dataframe(df)

elif menu == "Delete Train":
    st.subheader("Delete a Train")
    train_number = st.text_input("Enter Train Number")

    if st.button("Delete Train"):
        if train_number:
            delete_train(train_number)
