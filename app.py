import streamlit as st
import sqlite3
import os
import zipfile
import io
import plotly.express as px
from datetime import datetime



# Inisialisasi database
st.set_page_config(page_title="CISTECH", page_icon="assets/favicon.ico")

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

# Fungsi untuk mendapatkan semua project
def get_all_projects():
    with sqlite3.connect('project_management.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects")
        return cursor.fetchall()

# Fungsi untuk mendapatkan detail project
def get_project_details(project_id):
    with sqlite3.connect('project_management.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id=?", (project_id,))
        return cursor.fetchone()


st.image("cistech.png", width=450)
st.title("Dashboard Mapping Project TSCM ISO 9001-2015")

# Fungsi untuk menambahkan project baru
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
            status = st.selectbox("Status*", ["No Started", "On Going", "Completed", "Waiting BA"])
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

# Fungsi untuk mengedit project
def edit_project(project_id):
    project = get_project_details(project_id)
    if project:
        with st.form(key='edit_project_form'):
            st.subheader(f"Edit Project: {project[1]}")
            
            col1, col2 = st.columns(2)
            with col1:
                project_name = st.text_input("Project Name*", value=project[1])
                customer_name = st.text_input("Customer Name*", value=project[2])
                category = st.selectbox("Category*", ["Service", "Project"], index=0 if project[3] == "TSCM" else 1)
                pic = st.text_input("PIC*", value=project[4])
            
            with col2:
                status = st.selectbox("Status*", ["Planning", "On Going", "Completed", "Waiting BA"], 
                                    index=["Planning", "On Going", "Completed", "waiting BA"].index(project[5]))
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

# Fungsi untuk menghapus project
def delete_project(project_id):
    project = get_project_details(project_id)
    if project:
        st.warning(f"Are you sure you want to delete project: {project[1]}?")
        if st.button("Confirm Delete"):
            with sqlite3.connect('project_management.db') as conn:
                cursor = conn.cursor()
                # Hapus file terkait project
                cursor.execute("SELECT file_path FROM project_files WHERE project_id=?", (project_id,))
                files = cursor.fetchall()
                for file in files:
                    if os.path.exists(file[0]):
                        os.remove(file[0])
                
                # Hapus record file dari database
                cursor.execute("DELETE FROM project_files WHERE project_id=?", (project_id,))
                
                # Hapus project
                cursor.execute("DELETE FROM projects WHERE id=?", (project_id,))
                conn.commit()
            st.success("Project and all related files deleted successfully!")
    else:
        st.error("Project not found")

# Fungsi untuk menampilkan project
def view_projects():
    st.subheader("View All Projects")
    projects = get_all_projects()
    
    # Fungsi untuk menghitung progress
    def calculate_progress(status):
        if status == "Completed":
            return 100
        elif status == "Waiting BA":
            return 80
        elif status == "On Going":
            return 50
        else:
            return 0
    
    if projects:
        # Grafik progress semua project
        progress_data = []
        for project in projects:
            progress_data.append({
                "Project": project[1],
                "Progress": calculate_progress(project[5]),
                "Status": project[5]
            })
        
        fig = px.bar(progress_data, x="Project", y="Progress", color="Status",
                     title="Project Progress", text="Progress")
        fig.update_traces(texttemplate='%{text}%', textposition='outside')
        fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
        st.plotly_chart(fig, use_container_width=True)
        
        for project in projects:
            with st.expander(f"{project[1]} - {project[2]} ({project[5]})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Project Name:** {project[1]}")
                    st.write(f"**Customer:** {project[2]}")
                    st.write(f"**Category:** {project[3]}")
                    st.write(f"**PIC:** {project[4]}")
                    
                    # Progress bar untuk project ini
                    progress = calculate_progress(project[5])
                    st.progress(progress/100)
                    st.write(f"**Progress:** {progress}%")
                    
                
                with col2:
                    st.write(f"**Status:** {project[5]}")
                    st.write(f"**Start Date:** {project[6]}")
                    st.write(f"**End Date:** {project[7]}")
                    st.write(f"**PO Number:** {project[8]}")
                    st.write(f"**BAST Number:** {project[9]}")
                    
                   

# Fungsi tambahan untuk mendapatkan dokumen yang sudah diupload
def get_uploaded_docs(project_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT file_type FROM project_files WHERE project_id=?", (project_id,))
    uploaded_docs = [row[0] for row in cursor.fetchall()]
    conn.close()
    return uploaded_docs

# Fungsi untuk mengelola file project
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
            # Cek duplikasi file
            with sqlite3.connect('project_management.db') as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT file_name FROM project_files WHERE project_id=? AND file_category=?",
                    (selected_project_id, selected_category)
                )
                existing_file = cursor.fetchone()
                
                if existing_file:
                    # Hapus file lama jika sudah ada
                    cursor.execute(
                        "SELECT file_path FROM project_files WHERE project_id=? AND file_category=?",
                        (selected_project_id, selected_category)
                    )
                    old_file_path = cursor.fetchone()[0]
                    if os.path.exists(old_file_path):
                        os.remove(old_file_path)
                    
                    # Update record file di database
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
                    # Jika tidak ada file sebelumnya, buat baru
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
            # Buat ZIP semua file
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
            
            # Tampilkan daftar file
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

# Main App
init_db()

tabs = st.tabs(["View Projects", "Add Project", "Edit Project", "Delete Project", "Manage Files"])

with tabs[0]:
    view_projects()

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
