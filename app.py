import os
import streamlit as st
import sqlite3
from datetime import datetime
from sqlalchemy import Column, Integer, String, Date, DateTime, Text, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# -------------------------------------------------------------------
# Streamlit rerun compatibility (works with old & new versions)
if hasattr(st, "rerun"):
    def rerun():
        st.rerun()
else:
    def rerun():
        st.experimental_rerun()
# -------------------------------------------------------------------

# Database setup
Base = declarative_base()

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String, nullable=False)
    results = relationship("LabResult", back_populates="patient")

class Doctor(Base):
    __tablename__ = "doctors"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    specialization = Column(String, nullable=False)

class LabResult(Base):
    __tablename__ = "lab_results"
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    test_type = Column(String, nullable=False)
    test_date = Column(Date, nullable=False)
    result_date = Column(Date, nullable=False)
    file_path = Column(String, nullable=False)
    notes = Column(Text)
    status = Column(String, default="pending")
    lab_technician = Column(String)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    patient = relationship("Patient", back_populates="results")

# Database connection
DATABASE_URL = "sqlite:///digi_lab.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(bind=engine)

# -------------------------------------------------------------------
# Utility functions
# -------------------------------------------------------------------
def add_patient(session, first_name, last_name, dob, gender):
    patient = Patient(
        first_name=first_name,
        last_name=last_name,
        date_of_birth=dob,
        gender=gender
    )
    session.add(patient)
    session.commit()
    return patient

def add_doctor(session, name, specialization):
    doctor = Doctor(name=name, specialization=specialization)
    session.add(doctor)
    session.commit()
    return doctor

def add_lab_result(session, patient_id, test_type, test_date, result_date, file_path, notes, technician):
    result = LabResult(
        patient_id=patient_id,
        test_type=test_type,
        test_date=test_date,
        result_date=result_date,
        file_path=file_path,
        notes=notes,
        lab_technician=technician,
        status="completed"
    )
    session.add(result)
    session.commit()
    return result

# -------------------------------------------------------------------
# Streamlit App
# -------------------------------------------------------------------
st.set_page_config(page_title="DigiLab - Digital Lab Result System", layout="wide")
st.title("🧪 DigiLab - Digital Lab Result System")

menu = ["Home", "Register Patient", "Register Doctor", "Upload Lab Result", "View Lab Results"]
choice = st.sidebar.selectbox("Navigation", menu)

session = SessionLocal()

# -------------------------------------------------------------------
# Pages
# -------------------------------------------------------------------
if choice == "Home":
    st.subheader("Welcome to DigiLab")
    st.write("This is a digital laboratory results management system.")

elif choice == "Register Patient":
    st.subheader("Register Patient")
    with st.form("patient_form"):
        first_name = st.text_input("First Name")
        last_name = st.text_input("Last Name")
        dob = st.date_input("Date of Birth")
        gender = st.selectbox("Gender", ["male", "female", "other"])
        submitted = st.form_submit_button("Register")
        if submitted:
            add_patient(session, first_name, last_name, dob, gender)
            st.success("Patient registered successfully!")
            rerun()

elif choice == "Register Doctor":
    st.subheader("Register Doctor")
    with st.form("doctor_form"):
        name = st.text_input("Full Name")
        specialization = st.text_input("Specialization")
        submitted = st.form_submit_button("Register")
        if submitted:
            add_doctor(session, name, specialization)
            st.success("Doctor registered successfully!")
            rerun()

elif choice == "Upload Lab Result":
    st.subheader("Upload Lab Result")
    patients = session.query(Patient).all()
    if not patients:
        st.warning("No patients found. Please register a patient first.")
    else:
        with st.form("lab_result_form"):
            patient_id = st.selectbox("Select Patient", [p.id for p in patients],
                                      format_func=lambda x: f"{session.query(Patient).get(x).first_name} {session.query(Patient).get(x).last_name}")
            test_type = st.text_input("Test Type")
            test_date = st.date_input("Test Date")
            result_date = st.date_input("Result Date")
            file = st.file_uploader("Upload Result File", type=["pdf", "jpg", "jpeg", "png", "doc", "docx", "txt"])
            notes = st.text_area("Notes")
            technician = st.text_input("Lab Technician")
            submitted = st.form_submit_button("Upload")
            if submitted:
                if file:
                    save_dir = "uploaded_results"
                    os.makedirs(save_dir, exist_ok=True)
                    file_path = os.path.join(save_dir, file.name)
                    with open(file_path, "wb") as f:
                        f.write(file.getbuffer())
                    add_lab_result(session, patient_id, test_type, test_date, result_date, file_path, notes, technician)
                    st.success("Lab result uploaded successfully!")
                    rerun()
                else:
                    st.error("Please upload a file!")

elif choice == "View Lab Results":
    st.subheader("View Lab Results")
    results = session.query(LabResult).all()
    if results:
        for result in results:
            with st.expander(f"Result: {result.test_type} | Patient: {result.patient.first_name} {result.patient.last_name}"):
                st.write(f"**Test Type:** {result.test_type}")
                st.write(f"**Test Date:** {result.test_date}")
                st.write(f"**Result Date:** {result.result_date}")
                st.write(f"**Status:** {result.status}")
                if result.lab_technician:
                    st.write(f"**Lab Technician:** {result.lab_technician}")
                if result.notes:
                    st.write(f"**Notes:** {result.notes}")
                if result.file_path and os.path.exists(result.file_path):
                    with open(result.file_path, "rb") as f:
                        st.download_button("Download Result File", f, file_name=os.path.basename(result.file_path))
    else:
        st.info("No lab results found.")
