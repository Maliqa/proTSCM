import streamlit as st
from PIL import Image
import pandas as pd
import sqlite3
import datetime
import os
import plotly.express as px
import plotly.graph_objects as go
import zipfile
import io

st.set_page_config(page_title="CISTECH", page_icon="assets/favicon.ico")

# --- Database Functions ---
def init_db():
    with sqlite3.connect('project_mapping.db') as conn:
        c = conn.cursor()
        c.execute('''
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
                location TEXT,
                nomor_ba TEXT
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS project_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                file_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id),
                 UNIQUE (project_id, file_name)
            )
        ''')
        conn.commit()

@st.cache_resource
def get_connection():
    return sqlite3.connect('project_mapping.db', check_same_thread=False)
def get_connection():
    return sqlite3.connect('project_files.db')


def get_all_projects():
    try:
        with get_connection() as conn:
            df = pd.read_sql("SELECT * FROM projects", conn)
        return df
    except Exception as e:
        st.error(f"Error fetching projects: {e}")
        return pd.DataFrame()

def add_project(project_name, customer_name, category, pic, status, date_start, date_end, no_po, location, nomor_ba):
    try:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("INSERT INTO projects (project_name, customer_name, category, pic, status, date_start, date_end, no_po, location, nomor_ba) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                      (project_name, customer_name, category, pic, status, date_start.strftime('%Y-%m-%d'), date_end.strftime('%Y-%m-%d'), no_po, location, nomor_ba))
            conn.commit()
            st.success("Project added successfully!")
    except sqlite3.Error as e:
        st.error(f"Error adding project: {e}")

def update_project(id, project_name, customer_name, category, pic, status, date_start, date_end, no_po, location, nomor_ba):
    try:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("UPDATE projects SET project_name=?, customer_name=?, category=?, pic=?, status=?, date_start=?, date_end=?, no_po=?, location=?, nomor_ba=? WHERE id=?",
                      (project_name, customer_name, category, pic, status, date_start.strftime('%Y-%m-%d'), date_end.strftime('%Y-%m-%d'), no_po, location, nomor_ba, id))
            conn.commit()
            st.success("Project updated successfully!")
    except sqlite3.Error as e:
        st.error(f"Error updating project: {e}")

def delete_project(id):
    try:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM projects WHERE id=?", (id,))
            conn.commit()
            st.success("Project deleted successfully!")
    except sqlite3.Error as e:
        st.error(f"Error deleting project: {e}")

def get_all_project_files(project_id):
    try:
        with get_connection() as conn:
            df = pd.read_sql(f"SELECT * FROM project_files WHERE project_id = {project_id}", conn)
        return df
    except Exception as e:
        st.error(f"Error fetching project files: {e}")
        return pd.DataFrame()

def delete_file(file_id):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM project_files WHERE id=?", (file_id,))
            row = cursor.fetchone()
            if row is not None and os.path.exists(row[3]):
                os.remove(row[3])
                cursor.execute("DELETE FROM project_files WHERE id=?", (file_id,))
                conn.commit()
                st.success("File deleted successfully!")
            else:
                st.error("File does not exist.")
    except Exception as e:
        st.error(f"Error deleting file: {e}")
        


def upload_file(project_id, uploaded_file, file_category):
    if uploaded_file is not None:
        directory = f"files/project_{project_id}/{file_category}/"
        os.makedirs(directory, exist_ok=True)
        filepath = os.path.join(directory, uploaded_file.name)

        # Check if file already exists
        if os.path.exists(filepath):
            st.error(f"File '{uploaded_file.name}' already exists for this project. Please rename the file.")
            return  # Stop further processing

        with open(filepath, "wb") as f:
            f.write(uploaded_file.getbuffer())
        # ... (rest of your upload_file function remains the same) ...
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO project_files (project_id, file_name, file_path, file_category) VALUES (?, ?, ?, ?)",
                           (project_id, uploaded_file.name, filepath, file_category))
            conn.commit()
        st.success("File uploaded successfully!")

def download_all_files(project_id):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT file_path FROM project_files WHERE project_id = ?", (project_id,))
            files = cursor.fetchall()

        zip_filename = f"project_{project_id}_files.zip"
        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            for file_path in files:
                zipf.write(file_path[0], arcname=os.path.basename(file_path[0]))

        with open(zip_filename, 'rb') as f:
            st.download_button(
                label="Download All Files",
                data=f.read(),
                file_name=zip_filename,
                mime='application/zip'
            )
        st.success("Zip file created and ready for download.")

    except Exception as e:
        st.error(f"Error downloading files: {e}")


# --- Streamlit App ---
init_db()
st.image("cistech.png", width=550) # Remember to place cistech.png in the same directory
st.title("Dashboard Mapping Project TSCM")

tabs = st.tabs(["View Projects", "Add Project", "Edit Project", "Delete Project", "Manage Files"])

with tabs[0]:
    df = get_all_projects()
    if not df.empty:
        display_df = df.rename(columns={
            'project_name': 'Project',
            'customer_name': 'Customer',
            'category': 'Category',
            'pic': 'PIC',
            'status': 'Status',
            'date_start': 'Start Date',
            'date_end': 'End Date',
            'no_po': 'PO Number',
            'location': 'Location',
            'nomor_ba': 'Nomor BA'
        }).set_index('id')

        status_to_progress = {
            "Not Started": 0,
            "Waiting BA": 60,
            "Not Report": 80,
            "In Progress": 40,
            "On Hold": 20,
            "Completed": 100
        }
        display_df['Progress'] = display_df['Status'].map(status_to_progress)

        st.dataframe(display_df)

        for idx, row in display_df.iterrows():
            st.write(f"**{row['Project']}** - Progress: {row['Progress']}%")
            st.progress(int(row['Progress']))

        fig = go.Figure(data=[
            go.Bar(
                x=display_df['Project'],
                y=display_df['Progress'],
                marker_color='lightskyblue'
            )
        ])
        fig.update_layout(
            title='Progress Project',
            xaxis_title='Project',
            yaxis_title='Progress (%)',
            yaxis=dict(range=[0, 100])
        )
        st.plotly_chart(fig)

with tabs[1]:
    st.subheader("Tambah Project Baru")
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            project_name = st.text_input("Project Name")
            customer_name = st.text_input("Customer Name")
            category = st.text_input("Category")
            pic = st.text_input("PIC")
            location = st.text_input("Location")
        with col2:
            status = st.selectbox("Status", ["Not Started", "Waiting BA", "Not Report", "In Progress", "Completed"])
            date_col1, date_col2 = st.columns(2)
            with date_col1:
                date_start = st.date_input("Start Date", value=datetime.date.today())
            with date_col2:
                date_end = st.date_input("End Date", value=datetime.date.today())
            no_po = st.text_input("PO Number")
            nomor_ba = st.text_input("Nomor BA")
    if st.button("Add Project", key="add_project_button"):
        if project_name and customer_name and category and pic:
            add_project(project_name, customer_name, category, pic, status, date_start, date_end, no_po, location, nomor_ba)
        else:
            st.error("Harap isi semua field wajib (Project Name, Customer Name, Category, PIC)")

with tabs[2]:
    st.subheader("Edit Project")
    df = get_all_projects()
    if not df.empty:
        project_options = df['project_name'] + " (ID: " + df['id'].astype(str) + ")"
        selected = st.selectbox("Pilih Project", project_options)
        selected_id = int(selected.split("ID: ")[1].replace(")", ""))
        selected_project = df[df['id'] == selected_id].iloc[0]

        project_name = st.text_input("Project Name", value=selected_project['project_name'])
        customer_name = st.text_input("Customer Name", value=selected_project['customer_name'])
        category = st.text_input("Category", value=selected_project['category'])
        pic = st.text_input("PIC", value=selected_project['pic'])
        status = st.selectbox("Status", ["Not Started", "Waiting BA", "Not Report", "In Progress", "On Hold", "Completed"], index=["Not Started", "Waiting BA", "Not Report", "In Progress", "On Hold", "Completed"].index(selected_project['status']))
        date_start = st.date_input("Start Date", value=datetime.datetime.strptime(selected_project['date_start'], "%Y-%m-%d"))
        date_end = st.date_input("End Date", value=datetime.datetime.strptime(selected_project['date_end'], "%Y-%m-%d"))
        no_po = st.text_input("PO Number", value=selected_project['no_po'] if pd.notnull(selected_project['no_po']) else "")
        location = st.text_input("Location", value=selected_project['location'] if pd.notnull(selected_project['location']) else "")
        nomor_ba = st.text_input("Nomor BA", value=selected_project['nomor_ba'] if pd.notnull(selected_project['nomor_ba']) else "")

        if st.button("Update Project"):
            update_project(selected_id, project_name, customer_name, category, pic, status, date_start, date_end, no_po, location, nomor_ba)

with tabs[3]:
    st.subheader("Delete Project")
    df = get_all_projects()
    if not df.empty:
        project_options = df['project_name'] + " (ID: " + df['id'].astype(str) + ")"
        selected = st.selectbox("Pilih Project untuk Dihapus", project_options)
        selected_id = int(selected.split("ID: ")[1].replace(")", ""))
        if st.button("Delete Project"):
            delete_project(selected_id)

with tabs[4]:  # Manage Files
    st.subheader("Manage Files for Each Project")
    df_projects = get_all_projects()
    if not df_projects.empty:
        project_options = df_projects[['id', 'project_name', 'customer_name']]
        selected_project = st.selectbox(
            "Choose a Project to Manage Files",
            project_options['id'].tolist(),
            format_func=lambda x: f"{project_options[project_options['id'] == x]['project_name'].iloc[0]} - {project_options[project_options['id'] == x]['customer_name'].iloc[0]}"
        )

        file_categories = ["From Request", "Form Tim Project", "SPK", "BAST", "Form Tim Schedule", "Report"]
        selected_category = st.selectbox("Select File Category", file_categories)

        uploaded_file = st.file_uploader(
            f"Upload {selected_category} File Here",
            type=['pdf', 'docx', 'xls', 'xlsx', 'png', 'jpg', 'jpeg']
        )

        if st.button("Upload New File"):
            upload_file(selected_project, uploaded_file, selected_category)

        if st.button("Download All Files"):
            download_all_files(selected_project)


        files_df = get_all_project_files(selected_project)
        for _, row in files_df.iterrows():
            col1, col2, col3 = st.columns([6, 2, 1])
            col1.write(row['file_name'])
            col2.download_button(
                label="Download",
                data=open(row['file_path'], 'rb').read(),
                file_name=row['file_name'],
                mime='application/octet-stream',
                key=f'download-{row.id}'
            )
            col3.button(
                label="Delete",
                key=row.id,
                on_click=delete_file,
                args=(row.id,)
            )

        
       
            
          
           
                  
           
                
                    
                    
                  
                
