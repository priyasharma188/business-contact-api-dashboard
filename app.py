from flask import (
    Flask, render_template, request,
    redirect, url_for, send_from_directory, flash
)
import requests
import pandas as pd
import os
import uuid

app = Flask(__name__)
app.secret_key = "business-contact-dashboard"

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "csv", "xlsx"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ---------------- REAL API ----------------

API_URL = "https://randomuser.me/api/?results=20"


def get_api_contacts():
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()

        data = response.json()

        contacts = []

        for user in data["results"]:
            contacts.append({
                "name": f"{user['name']['first']} {user['name']['last']}",
                "email": user["email"],
                "phone": user["phone"],
                "company": "API Contact",
                "country": user["location"]["country"],
                "source": "REST API"
            })

        return contacts

    except Exception as error:
        print("API Error:", error)
        return []


# ---------------- FILE HELPERS ----------------

def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def get_uploaded_files():

    files = []

    for filename in os.listdir(UPLOAD_FOLDER):

        filepath = os.path.join(UPLOAD_FOLDER, filename)

        if os.path.isfile(filepath):

            extension = filename.rsplit(".", 1)[-1].upper()

            size = os.path.getsize(filepath)

            size_kb = round(size / 1024, 2)

            files.append({
                "name": filename,
                "type": extension,
                "size": f"{size_kb} KB"
            })

    return files


# ---------------- HOME ----------------

@app.route("/")
def home():

    contacts = get_api_contacts()

    search = request.args.get("search", "").strip().lower()

    if search:

        contacts = [
            contact
            for contact in contacts
            if search in contact["name"].lower()
            or search in contact["email"].lower()
            or search in contact["country"].lower()
        ]

    files = get_uploaded_files()

    return render_template(
        "index.html",
        contacts=contacts,
        files=files,
        search=search
    )


# ---------------- UPLOAD ----------------

@app.route("/upload", methods=["POST"])
def upload_file():

    if "file" not in request.files:

        flash("Please select a file.")

        return redirect(url_for("home"))

    file = request.files["file"]

    if file.filename == "":

        flash("No file selected.")

        return redirect(url_for("home"))

    if not allowed_file(file.filename):

        flash("Only PDF, CSV and Excel files are allowed.")

        return redirect(url_for("home"))

    original_name = file.filename

    extension = original_name.rsplit(".", 1)[1].lower()

    # Unique filename prevents overwriting
    unique_name = f"{uuid.uuid4().hex}.{extension}"

    filepath = os.path.join(
        UPLOAD_FOLDER,
        unique_name
    )

    file.save(filepath)

    flash(f"File uploaded successfully: {original_name}")

    return redirect(url_for("home"))


# ---------------- VIEW / DOWNLOAD FILE ----------------

@app.route("/files/<filename>")
def view_file(filename):

    return send_from_directory(
        UPLOAD_FOLDER,
        filename,
        as_attachment=False
    )


# ---------------- DOWNLOAD FILE ----------------

@app.route("/download/<filename>")
def download_file(filename):

    return send_from_directory(
        UPLOAD_FOLDER,
        filename,
        as_attachment=True
    )


# ---------------- DELETE FILE ----------------

@app.route("/delete/<filename>", methods=["POST"])
def delete_file(filename):

    filepath = os.path.join(
        UPLOAD_FOLDER,
        filename
    )

    if os.path.exists(filepath):

        os.remove(filepath)

        flash("File deleted successfully.")

    else:

        flash("File not found.")

    return redirect(url_for("home"))


# ---------------- EXPORT API DATA ----------------

@app.route("/export")
def export_csv():

    contacts = get_api_contacts()

    df = pd.DataFrame(contacts)

    export_path = os.path.join(
        UPLOAD_FOLDER,
        "business_contacts_export.csv"
    )

    df.to_csv(
        export_path,
        index=False
    )

    return send_from_directory(
        UPLOAD_FOLDER,
        "business_contacts_export.csv",
        as_attachment=True
    )


if __name__ == "__main__":
    app.run(debug=True)