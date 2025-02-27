import streamlit as st
import pandas as pd
import os
import json
import subprocess
from streamlit_extras.switch_page_button import switch_page
import shutil


st.set_page_config(layout="wide",initial_sidebar_state="collapsed")


tab_1,tab_2 = st.tabs(["Upload New File","Analysis"])


with tab_1:
    # Title of the app
    st.header("Excel File Uploader")
    
    with st.form("IMPORTANT NOTE"):
        st.write("**IMPORTANT NOTE**:")
        st.text("Make Sure the File Uploaded headers have columns meet the Below Conditions")
        st.text("1. Time Stamp Column Should be in mm/dd/yyyy hh:mi:ss Format with Column Header as 'TIME_STAMP'.")
        st.text("2. All the circuit column headers should have prefix 'C_' following by the number indicating the circuit.")
        st.text("3. Temperation Column should be TEMP_OUT and TEMP_GATE")
        st.text("4. Humidity Column should be HUMID_OUT and HUMID_GATE")
        acknowledge_bt = st.form_submit_button("Acknowledge")

    # Upload a single Excel file
    uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"])

    if uploaded_file is not None:
        # To read the uploaded excel file
        try:
            df = pd.read_excel(uploaded_file)

            # Display the data in the file
            st.write("Data Loaded successfully! Here's a preview:")
            st.dataframe(df)  # Show first few rows of the dataframe

            project_name = st.text_input("Enter Analysis Name:",value = None)
            
            # Save the file to the backend
            if project_name is not None:
                try:
                    os.mkdir(f'{project_name}')
                except Exception as e:
                    pass
                
                with open(f"{project_name}/{uploaded_file.name}", "wb") as f:
                    f.write(uploaded_file.getbuffer())

                st.success("File saved successfully to the backend!")
                
                total_systems = st.number_input("Enter No of Systems",min_value=0,max_value=100,value=None)

                columns = list(df.columns)

                filtered_column = [item for item in columns if item.startswith("C_")]
                
                analysis_system_details = {}
                
                i1,i2,i3 = st.columns([1.8,1.7,3])
                
                same_inst_date = i1.checkbox("Installation Dates are same for all System")
                
                if same_inst_date:
                    installation_date = i2.date_input("Enter Installation Date",value=None)
                    if total_systems and installation_date is not None:
                        for system in range(1,total_systems+1):
                            analysis_system_details[f"Installation Date System {system}"] = str(installation_date)
                    
                f1,f2,f3 = st.columns([2,1,2])

                if total_systems:
                    st.divider()
                    st.write(":green[ENTER CIRCUITS NUMBER FOR EACH SYSTEMS]")
                    for system in range(0,total_systems):
                        circuits = f1.multiselect(f"Enter Circuit Numbers for System {system+1}",filtered_column,placeholder="Choose multiple Circuits")
                        if same_inst_date is False:
                            installation_date = f2.date_input("Enter Installation Date",key=f"{system}date_input",value=None)
                            if installation_date is not None:
                                analysis_system_details[f"Installation Date System {system+1}"] = str(installation_date)
                        analysis_system_details[f"System {system+1}"] = circuits
                    st.write(analysis_system_details) 
                    
                    save_to_json = st.text_input("Enter 'Save' to Save Details:",value=None)
                    
                    if save_to_json == 'Save':
                        file_name = str(uploaded_file.name)
                        analysis_system_details_json = json.dumps(analysis_system_details)
                        file_name = file_name.replace('xlsx','json')
                        with open(f"{project_name}/{file_name}", "w") as file:
                            file.write(analysis_system_details_json)
                        st.success("Successfully Updated! Kindly Check with Analysis Tab for the Saved Data")
                        with open('folders.json','r') as folders_json:
                            data = json.load(folders_json)
                            
                        with open('folders.json','w') as folders_json:
                            data[project_name] = [uploaded_file.name,file_name]
                            st.write(data)
                            json_data = json.dumps(data)
                            folders_json.write(json_data)

        except Exception as e:
            st.error(f"Error uploading file: {e}")
    else:
        st.info("Please upload an Excel file.")


@st.dialog("Edit System Data")
def edit_system_data(project_name):
    
    json_file = [file for file in os.listdir(project_name) if file.endswith('.json')]
    with open(f"{project_name}/{json_file[0]}", "r") as json_file_data:
        data = json.load(json_file_data)
        json_file_data.close()
        
    json_file_name = json_file[0]
        
    excel_file = [file for file in os.listdir(project_name) if file.endswith('.xlsx')]
    df = pd.read_excel(f"{project_name}/{excel_file[0]}")
    
    columns_list = list(df.columns)
    
   
    filtered_column = [item for item in columns_list if item.startswith("C_")]
    
    i1,i2 = st.columns([1,1])
    
    same_inst_date = i1.checkbox("Installation Dates are same for all System")
                
    # if same_inst_date:
    #     installation_date = i2.date_input("Enter Installation Date",value=None)
    #     if total_systems and installation_date is not None:
    #         for system in range(1,total_systems+1):
    #             analysis_system_details[f"Installation Date System {system}"] = str(installation_date)
    
    analysis_system_details = {}
    
    f1,f2 = st.columns([2,1])
    
    for key,value in data.items():
        if key.startswith('System'):
            circuits = f1.multiselect(f"Enter Circuits For {key}",default=value,options=filtered_column)
            analysis_system_details[key] = circuits
            # if same_inst_date is False:
            #     installation_date = f2.date_input("Enter Installation Date",key=f"{system}date_input",value=None)
            #     if installation_date is not None:
            #         analysis_system_details[f"Installation Date System {system+1}"] = str(installation_date)
            
    save_to_json = st.text_input("Enter 'Save' to Save Details:",value=None,key=f"text_input_{project_name}")
                    
    if save_to_json == 'Save':
        analysis_system_details_json = json.dumps(analysis_system_details,default="str")
        with open(f"{project_name}/{json_file_name}", "w") as file:
            file.write(analysis_system_details_json)
            file.close()
        st.success("Successfully Updated! Changes Made")
        


with tab_2:
    with open("folders.json",'r') as folder_json_file:
        folders_json = json.load(folder_json_file)
    
    folders = list(folders_json.keys())
    
    # st.write(folders)
        
    folders_actual_list = [name for name in os.listdir('.') if os.path.isdir(name)]
    
    folders_actual_list = [item for item in folders_actual_list if item != "pages"]
    
    folders_deleted = [item for item in folders_actual_list if item not in folders]
    
    # st.write(folders_deleted)
    
    for deleted_folder in folders_deleted:
        shutil.rmtree(deleted_folder)
    
    for folder in folders:
        with st.expander(f"{folder}"):
            c2,c3,c4 = st.columns([1,1,7])
            analysis_button = c2.button("Check Analysis",key=f"analyse_{folder}")
            delete_button = c3.button("Delete Analysis",key=f"delete_{folder}")
            
                
            if analysis_button:
                st.session_state.project_name = folder
                switch_page("analysis")
                
            if delete_button:
                with open('folders.json','w') as folder_json_file:
                    del folders_json[folder]
                    st.write(folders_json)
                    json_data = json.dumps(folders_json)
                    folder_json_file.write(json_data)
                st.rerun()
                    
                
                
                
    
      
    
                
        