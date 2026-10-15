
import json
import os
from datetime import datetime, date
from collections import deque


DATA_FILE = "community_health_data.json"


class Patient:
    """Stores information about a registered patient."""

    total_patients = 0

    def __init__(self, patient_id, name, age, phone):
        self.patient_id = patient_id
        self.name = name
        self.age = age
        self.phone = phone

    def to_dict(self):
        return {
            "patient_id": self.patient_id,
            "name": self.name,
            "age": self.age,
            "phone": self.phone
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            data["patient_id"],
            data["name"],
            data["age"],
            data["phone"]
        )

    @staticmethod
    def valid_age(age):
        return age.isdigit() and 0 <= int(age) <= 120


class Appointment:
    """Manages an individual clinic appointment."""

    def __init__(
        self, appointment_id, patient_id, appointment_date,
        appointment_time, reason, status="Booked"
    ):
        self.appointment_id = appointment_id
        self.patient_id = patient_id
        self.appointment_date = appointment_date
        self.appointment_time = appointment_time
        self.reason = reason
        self.status = status

    def to_dict(self):
        return {
            "appointment_id": self.appointment_id,
            "patient_id": self.patient_id,
            "appointment_date": self.appointment_date,
            "appointment_time": self.appointment_time,
            "reason": self.reason,
            "status": self.status
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            data["appointment_id"],
            data["patient_id"],
            data["appointment_date"],
            data["appointment_time"],
            data["reason"],
            data.get("status", "Booked")
        )


class CommunityHealthConnect:
    """A community clinic registration and appointment platform."""

    def __init__(self):
        self.patients = {}
        self.appointments = {}
        self.next_patient_id = 1
        self.next_appointment_id = 1
        self.load_data()

    # ---------- DATA STORAGE ----------

    def save_data(self):
        """Save system records locally in JSON format."""
        data = {
            "patients": [
                patient.to_dict()
                for patient in self.patients.values()
            ],
            "appointments": [
                appointment.to_dict()
                for appointment in self.appointments.values()
            ],
            "next_patient_id": self.next_patient_id,
            "next_appointment_id": self.next_appointment_id
        }

        temporary_file = DATA_FILE + ".tmp"

        try:
            with open(temporary_file, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4)

            os.replace(temporary_file, DATA_FILE)

        except OSError:
            print("Warning: Could not save the records.")
            if os.path.exists(temporary_file):
                os.remove(temporary_file)

    def load_data(self):
        """Restore saved records when the program starts."""
        if not os.path.exists(DATA_FILE):
            return

        try:
            with open(DATA_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)

            self.patients = {
                p["patient_id"]: Patient.from_dict(p)
                for p in data.get("patients", [])
            }

            self.appointments = {
                a["appointment_id"]: Appointment.from_dict(a)
                for a in data.get("appointments", [])
            }

            self.next_patient_id = max(
                data.get("next_patient_id", 1),
                max(self.patients.keys(), default=0) + 1
            )

            self.next_appointment_id = max(
                data.get("next_appointment_id", 1),
                max(self.appointments.keys(), default=0) + 1
            )

            print("Saved records loaded successfully.")

        except (OSError, json.JSONDecodeError, KeyError, TypeError):
            print(
                "Warning: Saved data could not be read. "
                "Check the JSON file before continuing."
            )

    # ---------- HELPER METHODS ----------

    @staticmethod
    def heading(title):
        print("\n" + "=" * 48)
        print(f"  {title}")
        print("=" * 48)

    @staticmethod
    def ask_nonempty(prompt):
        while True:
            value = input(prompt).strip()

            if value:
                return value

            print("This field cannot be empty.")

    def get_patient(self, patient_id):
        return self.patients.get(patient_id)

    def appointment_datetime(self, appointment):
        return datetime.strptime(
            f"{appointment.appointment_date} "
            f"{appointment.appointment_time}",
            "%Y-%m-%d %H:%M"
        )

    # ---------- PATIENT REGISTRATION ----------

    def register_patient(self):
        self.heading("REGISTER A NEW PATIENT")

        name = self.ask_nonempty("Patient name: ")

        age = input("Patient age: ").strip()

        if not Patient.valid_age(age):
            print("Invalid age. Enter a number between 0 and 120.")
            return

        phone = self.ask_nonempty("Phone number: ")

        patient_id = self.next_patient_id

        patient = Patient(
            patient_id,
            name,
            int(age),
            phone
        )

        self.patients[patient_id] = patient
        self.next_patient_id += 1

        self.save_data()

        print("\nPatient registered successfully!")
        print(f"Unique Patient ID: HC{patient_id:04d}")

    # ---------- APPOINTMENT BOOKING ----------

    def book_appointment(self):
        self.heading("BOOK A CLINIC APPOINTMENT")

        if not self.patients:
            print("Register a patient before booking an appointment.")
            return

        try:
            patient_id = int(
                input("Enter patient ID number (e.g. 1): ")
            )
        except ValueError:
            print("Patient ID must be a number.")
            return

        patient = self.get_patient(patient_id)

        if patient is None:
            print("Patient not found.")
            return

        appointment_date = input(
            "Appointment date (YYYY-MM-DD): "
        ).strip()

        try:
            selected_date = datetime.strptime(
                appointment_date, "%Y-%m-%d"
            ).date()

            if selected_date < date.today():
                print("You cannot book an appointment in the past.")
                return

        except ValueError:
            print("Invalid date format.")
            return

        appointment_time = input(
            "Appointment time (HH:MM, 24-hour format): "
        ).strip()

        try:
            datetime.strptime(appointment_time, "%H:%M")
        except ValueError:
            print("Invalid time. Example: 09:30 or 14:00.")
            return

        reason = self.ask_nonempty(
            "General appointment reason: "
        )

        # Prevent double-booking a time slot.
        for existing in self.appointments.values():
            if (
                existing.appointment_date == appointment_date
                and existing.appointment_time == appointment_time
                and existing.status == "Booked"
            ):
                print(
                    "That time slot is already booked. "
                    "Please choose another time."
                )
                return

        appointment_id = self.next_appointment_id

        appointment = Appointment(
            appointment_id,
            patient_id,
            appointment_date,
            appointment_time,
            reason
        )

        self.appointments[appointment_id] = appointment
        self.next_appointment_id += 1

        self.save_data()

        print("\nAppointment successfully booked!")
        print(f"Appointment ID: AP{appointment_id:04d}")
        print(f"Patient: {patient.name}")
        print(f"Date: {appointment_date}")
        print(f"Time: {appointment_time}")

    # ---------- SEARCH AND DISPLAY ----------

    def view_patients(self):
        self.heading("REGISTERED PATIENTS")

        if not self.patients:
            print("No patients registered yet.")
            return

        for patient in self.patients.values():
            print("-" * 35)
            print(f"ID: HC{patient.patient_id:04d}")
            print(f"Name: {patient.name}")
            print(f"Age: {patient.age}")
            print(f"Phone: {patient.phone}")

    def search_patient(self):
        self.heading("SEARCH PATIENT")

        search_term = input(
            "Enter patient ID or name: "
        ).strip()

        if not search_term:
            print("Enter an ID or name to search.")
            return

        matches = [
            patient for patient in self.patients.values()
            if (
                search_term.lower() == str(patient.patient_id).lower()
                or search_term.lower() == f"hc{patient.patient_id:04d}".lower()
                or search_term.lower() in patient.name.lower()
            )
        ]

        if not matches:
            print("No matching patient found.")
            return

        for patient in matches:
            print(
                f"\nHC{patient.patient_id:04d} | "
                f"{patient.name} | Age: {patient.age} | "
                f"Phone: {patient.phone}"
            )

            for appointment in self.appointments.values():
                if appointment.patient_id == patient.patient_id:
                    print(
                        f"  Appointment AP{appointment.appointment_id:04d}: "
                        f"{appointment.appointment_date} "
                        f"at {appointment.appointment_time} "
                        f"({appointment.status})"
                    )

    def view_appointments(self):
        self.heading("ALL APPOINTMENTS")

        if not self.appointments:
            print("No appointments available.")
            return

        ordered = sorted(
            self.appointments.values(),
            key=lambda a: (a.appointment_date, a.appointment_time)
        )

        for appointment in ordered:
            patient = self.get_patient(appointment.patient_id)
            patient_name = patient.name if patient else "Unknown"

            print("-" * 40)
            print(f"Appointment: AP{appointment.appointment_id:04d}")
            print(f"Patient: {patient_name}")
            print(
                f"When: {appointment.appointment_date} "
                f"at {appointment.appointment_time}"
            )
            print(f"Reason: {appointment.reason}")
            print(f"Status: {appointment.status}")

    # ---------- CLINIC QUEUE ----------

    def manage_queue(self):
        self.heading("CLINIC QUEUE")

        queue = deque(
            sorted(
                [
                    a for a in self.appointments.values()
                    if (
                        a.appointment_date == date.today().isoformat()
                        and a.status in ("Booked", "Waiting", "In Progress")
                    )
                ],
                key=lambda a: a.appointment_time
            )
        )

        if not queue:
            print("No active appointments for today.")
            return

        print("\nToday's queue:")

        for position, appointment in enumerate(queue, start=1):
            patient = self.get_patient(appointment.patient_id)
            name = patient.name if patient else "Unknown"

            print(
                f"{position}. AP{appointment.appointment_id:04d} | "
                f"{name} | {appointment.appointment_time} | "
                f"{appointment.status}"
            )

        print("\nQueue actions:")
        print("1. Mark appointment as Waiting")
        print("2. Start appointment")
        print("3. Mark appointment as Completed")
        print("0. Return to menu")

        choice = input("Choose action: ").strip()

        if choice == "0":
            return

        try:
            appointment_id = int(
                input("Enter appointment ID number: ")
            )
        except ValueError:
            print("Invalid appointment ID.")
            return

        appointment = self.appointments.get(appointment_id)

        if appointment is None:
            print("Appointment not found.")
            return

        if appointment.appointment_date != date.today().isoformat():
            print("Only today's appointments can be managed in this queue.")
            return

        if choice == "1" and appointment.status == "Booked":
            appointment.status = "Waiting"

        elif choice == "2" and appointment.status in ("Booked", "Waiting"):
            appointment.status = "In Progress"

        elif choice == "3" and appointment.status == "In Progress":
            appointment.status = "Completed"

        else:
            print(
                "That action is not available for the appointment's "
                "current status."
            )
            return

        self.save_data()
        print(f"Appointment status updated to: {appointment.status}")

    # ---------- CANCELLATION ----------

    def cancel_appointment(self):
        self.heading("CANCEL APPOINTMENT")

        try:
            appointment_id = int(
                input("Enter appointment ID number: ")
            )
        except ValueError:
            print("Invalid appointment ID.")
            return

        appointment = self.appointments.get(appointment_id)

        if appointment is None:
            print("Appointment not found.")
            return

        if appointment.status in ("Cancelled", "Completed"):
            print(
                f"This appointment is already {appointment.status.lower()}."
            )
            return

        confirm = input(
            "Confirm cancellation? (yes/no): "
        ).strip().lower()

        if confirm == "yes":
            appointment.status = "Cancelled"
            self.save_data()
            print("Appointment cancelled successfully.")
        else:
            print("Cancellation abandoned.")

    # ---------- REMINDERS ----------

    def view_reminders(self):
        self.heading("UPCOMING APPOINTMENTS & REMINDERS")

        today = date.today()
        upcoming = []

        for appointment in self.appointments.values():
            if appointment.status not in ("Booked", "Waiting"):
                continue

            try:
                appointment_date = datetime.strptime(
                    appointment.appointment_date, "%Y-%m-%d"
                ).date()
            except ValueError:
                continue

            days_remaining = (appointment_date - today).days

            if 0 <= days_remaining <= 7:
                upcoming.append((days_remaining, appointment))

        if not upcoming:
            print("No booked appointments in the next seven days.")
            return

        for days_remaining, appointment in sorted(
            upcoming,
            key=lambda item: (
                item[1].appointment_date,
                item[1].appointment_time
            )
        ):
            patient = self.get_patient(appointment.patient_id)
            name = patient.name if patient else "Unknown"

            if days_remaining == 0:
                reminder = "TODAY"
            elif days_remaining == 1:
                reminder = "TOMORROW"
            else:
                reminder = f"IN {days_remaining} DAYS"

            print(f"\n[{reminder}]")
            print(f"Patient: {name}")
            print(f"Date: {appointment.appointment_date}")
            print(f"Time: {appointment.appointment_time}")
            print(
                "Reminder: Please confirm your appointment "
                "with the clinic."
            )

        print(
            "\nThese are on-screen reminders only; "
            "no SMS or phone notifications are sent."
        )

    # ---------- DASHBOARD ----------

    def dashboard(self):
        self.heading("COMMUNITY HEALTH DASHBOARD")

        total_patients = len(self.patients)
        total_appointments = len(self.appointments)

        booked = sum(
            a.status == "Booked"
            for a in self.appointments.values()
        )
        waiting = sum(
            a.status == "Waiting"
            for a in self.appointments.values()
        )
        in_progress = sum(
            a.status == "In Progress"
            for a in self.appointments.values()
        )
        completed = sum(
            a.status == "Completed"
            for a in self.appointments.values()
        )
        cancelled = sum(
            a.status == "Cancelled"
            for a in self.appointments.values()
        )

        today_appointments = sum(
            a.appointment_date == date.today().isoformat()
            and a.status not in ("Cancelled", "Completed")
            for a in self.appointments.values()
        )

        print(f"Registered patients:       {total_patients}")
        print(f"Total appointments:        {total_appointments}")
        print(f"Booked:                    {booked}")
        print(f"Waiting:                   {waiting}")
        print(f"Currently in progress:     {in_progress}")
        print(f"Completed:                 {completed}")
        print(f"Cancelled:                 {cancelled}")
        print(f"Active appointments today: {today_appointments}")

    # ---------- MAIN MENU ----------

    def run(self):
        while True:
            print("\n" + "*" * 48)
            print("       COMMUNITY HEALTH CONNECT")
            print("   Accessible Community Clinic Management")
            print("*" * 48)
            print("1.  Register a patient")
            print("2.  Book an appointment")
            print("3.  View registered patients")
            print("4.  Search for a patient")
            print("5.  View all appointments")
            print("6.  Manage today's clinic queue")
            print("7.  Cancel an appointment")
            print("8.  View appointment reminders")
            print("9.  View clinic dashboard")
            print("0.  Exit")
            print("-" * 48)

            choice = input("Select an option: ").strip()

            actions = {
                "1": self.register_patient,
                "2": self.book_appointment,
                "3": self.view_patients,
                "4": self.search_patient,
                "5": self.view_appointments,
                "6": self.manage_queue,
                "7": self.cancel_appointment,
                "8": self.view_reminders,
                "9": self.dashboard
            }

            if choice == "0":
                self.save_data()
                print("\nThank you for using Community Health Connect.")
                print("Your records have been saved locally.")
                break

            action = actions.get(choice)

            if action:
                action()
            else:
                print("Invalid choice. Select a number from 0 to 9.")


if __name__ == "__main__":
    system = CommunityHealthConnect()
    system.run()
