import streamlit as st
import pandas as pd
import pyqrcode
from io import BytesIO
from PIL import Image
import cv2
from pyzbar import pyzbar

st.title("Registrant Attendance System")


# Sample Registrant Data (replace with your actual data source)
registrants_data = {
    'ID': [1001, 1002, 1003, 1004, 1005],
    'Name': ['Alice Smith', 'Bob Johnson', 'Charlie Brown', 'Diana Prince', 'Ethan Hunt'],
    'Status': ['Registered', 'Registered', 'Registered', 'Registered', 'Registered']
}
df_registrants = pd.DataFrame(registrants_data)

def generate_qr_code(data):
    """
    Generates a QR code image from the provided data.

    Parameters:
    data (str): The data to encode in the QR code.

    Returns:
    BytesIO: The QR code image in a BytesIO buffer.
    """
    qr = pyqrcode.create(data)
    buffer = BytesIO()
    qr.png(buffer, scale=6)
    buffer.seek(0)
    return buffer

def decode_qr_code(frame):
    """
    Decodes QR codes in the given image frame.

    Parameters:
    frame (numpy.ndarray): The image frame to scan for QR codes.

    Returns:
    list: A list of decoded QR code data.
    """
    decoded_objects = pyzbar.decode(frame)
    qr_codes = [obj.data.decode('utf-8') for obj in decoded_objects]
    return qr_codes

def create_qr_code():
    st.subheader("Generate QR Code for Registrant ID")
    registrant_id_qr = st.number_input("Enter Registrant ID to generate QR Code", min_value=1000, step=1)

    if registrant_id_qr:
        qr_image = generate_qr_code(str(registrant_id_qr))
        img = Image.open(qr_image)

        st.image(img, caption=f"QR Code for ID: {registrant_id_qr}", use_column_width=False)

        st.download_button(
            label="Download QR Code",
            data=qr_image,
            file_name=f"qrcode_{registrant_id_qr}.png",
            mime="image/png"
        )

def scan_qr_code_for_attendance(df):
    st.subheader("Scan QR Code to Mark Attendance")
    st.write("Click 'Start Scanning' to use your camera to scan a QR code.")

    if "scanning_attendance" not in st.session_state:
        st.session_state.scanning_attendance = False
    if "decoded_id" not in st.session_state:
        st.session_state.decoded_id = None

    def start_scanning_attendance():
        st.session_state.scanning_attendance = True

    def stop_scanning_attendance():
        st.session_state.scanning_attendance = False

    if not st.session_state.scanning_attendance:
        if st.button('Start Scanning', key='start_scan_attendance', on_click=start_scanning_attendance):
            pass # start_scanning_attendance is handled by button click

    if st.session_state.scanning_attendance:
        cap = cv2.VideoCapture(0)
        stframe_attendance = st.empty()
        id_scanned = None # To store the scanned ID

        while st.session_state.scanning_attendance:
            ret, frame = cap.read()
            if not ret:
                st.write("Failed to capture image.")
                break

            qr_codes = decode_qr_code(frame)

            stframe_attendance.image(frame, channels="BGR")

            if qr_codes:
                try:
                    scanned_id = int(qr_codes[0]) # Assuming QR code contains the ID as integer
                    id_scanned = scanned_id
                    st.session_state.decoded_id = scanned_id
                    st.success(f"QR Code Scanned! ID: {scanned_id}")
                    break # Stop scanning after successful decode
                except ValueError:
                    st.warning("QR Code does not contain a valid Registrant ID.")
                    break # Stop scanning if not a valid ID

        if st.button('Stop Scanning', key='stop_scan_attendance', on_click=stop_scanning_attendance):
            cap.release()
            cv2.destroyAllWindows()

        if id_scanned:
            update_attendance(df, id_scanned)
            st.session_state.scanning_attendance = False # Reset scanning state after processing


def update_attendance(df, registrant_id):
    """
    Updates the attendance status in the DataFrame for a given registrant ID.

    Parameters:
    df (pd.DataFrame): The registrant DataFrame.
    registrant_id (int): The ID of the registrant who attended.
    """
    if registrant_id in df['ID'].values:
        df.loc[df['ID'] == registrant_id, 'Status'] = 'Attended'
        st.success(f"Attendance marked for Registrant ID: {registrant_id}")
    else:
        st.error(f"Registrant ID: {registrant_id} not found.")


def main():
    st.title("Registrant Attendance System")

    global df_registrants # Use the global DataFrame

    st.subheader("Registrant List")
    st.dataframe(df_registrants)

    st.sidebar.title("Actions")
    action = st.sidebar.radio("Choose an action", ["Generate QR Code", "Mark Attendance"])

    if action == "Generate QR Code":
        create_qr_code()
    elif action == "Mark Attendance":
        scan_qr_code_for_attendance(df_registrants) # Pass the dataframe

    # Display updated table after attendance marking (important to refresh)
    st.subheader("Updated Registrant List")
    st.dataframe(df_registrants)


if __name__ == "__main__":
    main()