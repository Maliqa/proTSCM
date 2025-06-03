import streamlit as st
import sqlite3
import os
import zipfile
import io
import plotly.express as px
from datetime import datetime

# Inisialisasi database
st.set_page_config(page_title="CISTECH", page_icon="assets/favicon.ico", layout="wide")

def init_db():
    conn = sqlite3.connect('project_management.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT NOT NULL,
            customer_name TEXT NOT NULL,
            category TEXT NOT NULL,
            pic TEXT NOT NULL,
            status TEXT NOT NULL,
            date_start TEXT NOT NULL,
            date_end TEXT NOT NULL,
            no_po TEXT,
            no_bast TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS project_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_category TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects (id)
        )
    ''')
    conn.commit()
    conn.close()

def get_all_projects():
    with sqlite3.connect('project_management.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects")
        return cursor.fetchall()

def get_project_details(project_id):
    with sqlite3.connect('project_management.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id=?", (project_id,))
        return cursor.fetchone()

def search_projects(search_term):
    with sqlite3.connect('project_management.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE project_name LIKE ? OR customer_name LIKE ?", ('%' + search_term + '%', '%' + search_term + '%'))
        return cursor.fetchall()

# Tampilan header
st.image("cistech.png", width=450)

st.image("cistech.png", width=450)
st.markdown('<h1>Dashboard Mapping Project TSCM-<small>ISO 9001-2015</small></h1>', unsafe_allow_html=True)

def add_project():
    with st.form(key='add_project_form'):
        st.subheader("Add New Project")
        col1, col2 = st.columns(2)
        with col1:
            project_name = st.text_input("Project Name*")
            customer_name = st.text_input("Customer Name*")
            category = st.selectbox("Category*", ["SERVICE", "PROJECT"])
            pic = st.text_input("PIC*")
        with col2:
            status = st.selectbox("Status*", ["Not Started", "On Going", "Completed", "Waiting BA"])
            date_start = st.date_input("Start Date*")
            date_end = st.date_input("End Date*")
            no_po = st.text_input("PO Number")
            no_bast = st.text_input("BAST Number")
        if st.form_submit_button("Save Project"):
            if project_name and customer_name and category and pic and status and date_start and date_end:
                with sqlite3.connect('project_management.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO projects (
                            project_name, customer_name, category, pic, status,
                            date_start, date_end, no_po, no_bast
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        project_name, customer_name, category, pic, status,
                        date_start.strftime('%Y-%m-%d'), date_end.strftime('%Y-%m-%d'),
                        no_po, no_bast
                    ))
                    conn.commit()
                st.success("Project added successfully!")
            else:
                st.error("Please fill all required fields (*)")

def edit_project(project_id):
    project = get_project_details(project_id)
    if project:
        with st.form(key='edit_project_form'):
            st.subheader(f"Edit Project: {project[1]}")
            col1, col2 = st.columns(2)
            with col1:
                project_name = st.text_input("Project Name*", value=project[1])
                customer_name = st.text_input("Customer Name*", value=project[2])
                category = st.selectbox("Category*", ["SERVICE", "PROJECT"], index=0 if project[3] == "SERVICE" else 1)
                pic = st.text_input("PIC*", value=project[4])
            with col2:
                status = st.selectbox("Status*", ["Not Started", "On Going", "Completed", "Waiting BA"], index=["Not Started", "On Going", "Completed", "Waiting BA"].index(project[5]))
                date_start = st.date_input("Start Date*", value=datetime.strptime(project[6], '%Y-%m-%d').date())
                date_end = st.date_input("End Date*", value=datetime.strptime(project[7], '%Y-%m-%d').date())
                no_po = st.text_input("PO Number", value=project[8])
                no_bast = st.text_input("BAST Number", value=project[9])
            if st.form_submit_button("Update Project"):
                with sqlite3.connect('project_management.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE projects SET
                            project_name=?, customer_name=?, category=?, pic=?, status=?,
                            date_start=?, date_end=?, no_po=?, no_bast=?
                        WHERE id=?
                    ''', (
                        project_name, customer_name, category, pic, status,
                        date_start.strftime('%Y-%m-%d'), date_end.strftime('%Y-%m-%d'),
                        no_po, no_bast, project_id
                    ))
                    conn.commit()
                st.success("Project updated successfully!")
    else:
        st.error("Project not found")

def delete_project(project_id):
    project = get_project_details(project_id)
    if project:
        st.warning(f"Are you sure you want to delete project: {project[1]}?")
        if st.button("Confirm Delete"):
            with sqlite3.connect('project_management.db') as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT file_path FROM project_files WHERE project_id=?", (project_id,))
                files = cursor.fetchall()
                for file in files:
                    if os.path.exists(file[0]):
                        os.remove(file[0])
                cursor.execute("DELETE FROM project_files WHERE project_id=?", (project_id,))
                cursor.execute("DELETE FROM projects WHERE id=?", (project_id,))
                conn.commit()
            st.success("Project and all related files deleted successfully!")
    else:
        st.error("Project not found")

def view_projects_kanban():
    st.subheader("Board")
    
    # Search functionality
    search_term = st.text_input("Search Projects...")
    if search_term:
        projects = search_projects(search_term)
    else:
        projects = get_all_projects()
    
    # Define status columns
    statuses = ["Not Started", "On Going", "Waiting BA", "Completed"]
    columns = st.columns(len(statuses))
    
    for idx, status in enumerate(statuses):
        with columns[idx]:
            st.subheader(status)
            filtered_projects = [p for p in projects if p[5] == status]
            
            for project in filtered_projects:
                with st.expander(f"{project[1]} - {project[2]}"):
                    st.write(f"**Customer:** {project[2]}")
                    st.write(f"**Category:** {project[3]}")
                    st.write(f"**PIC:** {project[4]}")
                    st.write(f"**Start Date:** {project[6]}")
                    st.write(f"**End Date:** {project[7]}")
                    
                    # Progress bar based on status
                    progress = 0
                    if status == "Not Started":
                        progress = 0
                    elif status == "On Going":
                        progress = 50
                    elif status == "Waiting BA":
                        progress = 80
                    elif status == "Completed":
                        progress = 100
                    
                    st.progress(progress)
                    st.write(f"**PO Number:** {project[8] if project[8] else 'N/A'}")
                    st.write(f"**BAST Number:** {project[9] if project[9] else 'N/A'}")

def manage_files():
    st.subheader("Manage Project Files")
    projects = get_all_projects()
    if projects:
        project_options = {f"{p[1]} - {p[2]}": p[0] for p in projects}
        selected_project_name = st.selectbox("Choose Project", list(project_options.keys()))
        selected_project_id = project_options[selected_project_name]
        required_files = [
            "Form Request",
            "Form Tim Project",
            "Form Time Schedule",
            "SPK",
            "BAST",
            "Report"
        ]
        st.markdown("### Upload Required Documents")
        selected_category = st.selectbox("Select Document Type", required_files)
        uploaded_file = st.file_uploader(
            f"Upload {selected_category}",
            type=['pdf', 'doc', 'docx', 'xls', 'xlsx', 'jpg', 'jpeg', 'png']
        )
        if st.button("Upload Document") and uploaded_file:
            with sqlite3.connect('project_management.db') as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT file_name FROM project_files WHERE project_id=? AND file_category=?",
                    (selected_project_id, selected_category)
                )
                existing_file = cursor.fetchone()
                if existing_file:
                    cursor.execute(
                        "SELECT file_path FROM project_files WHERE project_id=? AND file_category=?",
                        (selected_project_id, selected_category)
                    )
                    old_file_path = cursor.fetchone()[0]
                    if os.path.exists(old_file_path):
                        os.remove(old_file_path)
                    directory = f"files/project_{selected_project_id}/"
                    os.makedirs(directory, exist_ok=True)
                    filepath = os.path.join(directory, uploaded_file.name)
                    with open(filepath, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    cursor.execute(
                        "UPDATE project_files SET file_name=?, file_path=? WHERE project_id=? AND file_category=?",
                        (uploaded_file.name, filepath, selected_project_id, selected_category)
                    )
                    conn.commit()
                    st.success(f"File {selected_category} berhasil diupdate!")
                else:
                    directory = f"files/project_{selected_project_id}/"
                    os.makedirs(directory, exist_ok=True)
                    filepath = os.path.join(directory, uploaded_file.name)
                    with open(filepath, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    cursor.execute(
                        "INSERT INTO project_files (project_id, file_name, file_path, file_category) VALUES (?, ?, ?, ?)",
                        (selected_project_id, uploaded_file.name, filepath, selected_category)
                    )
                    conn.commit()
                    st.success(f"File {selected_category} berhasil diupload!")
        st.markdown("### Uploaded Documents")
        with sqlite3.connect('project_management.db') as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, file_name, file_path, file_category FROM project_files WHERE project_id=?",
                (selected_project_id,)
            )
            files = cursor.fetchall()
        if files:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
                for file in files:
                    if os.path.exists(file[2]):
                        zipf.write(file[2], arcname=file[1])
            zip_buffer.seek(0)
            st.download_button(
                label="Download All Files (ZIP)",
                data=zip_buffer,
                file_name=f"{selected_project_name.replace(' ', '_')}_files.zip",
                mime="application/zip"
            )
            for file in files:
                col1, col2, col3 = st.columns([6, 2, 1])
                col1.write(f"{file[3]}: {file[1]}")
                if os.path.exists(file[2]):
                    col2.download_button(
                        label="Download",
                        data=open(file[2], "rb").read(),
                        file_name=file[1],
                        mime="application/octet-stream",
                        key=f"download_{file[0]}"
                    )
                else:
                    col2.warning("File not found")
        else:
            st.info("No documents uploaded yet for this project")
    else:
        st.info("No projects available. Please add a project first.")

init_db()

tabs = st.tabs(["Board", "Add Project", "Edit Project", "Delete Project", "Manage Files"])

with tabs[0]:
    view_projects_kanban()

with tabs[1]:
    add_project()

with tabs[2]:
    st.subheader("Edit Project")
    projects = get_all_projects()
    if projects:
        project_options = {f"{p[1]} - {p[2]}": p[0] for p in projects}
        selected_project = st.selectbox("Select Project to Edit", list(project_options.keys()))
        edit_project(project_options[selected_project])
    else:
        st.info("No projects available to edit")

with tabs[3]:
    st.subheader("Delete Project")
    projects = get_all_projects()
    if projects:
        project_options = {f"{p[1]} - {p[2]}": p[0] for p in projects}
        selected_project = st.selectbox("Select Project to Delete", list(project_options.keys()))
        delete_project(project_options[selected_project])
    else:
        st.info("No projects available to delete")

with tabs[4]:
    manage_files()
