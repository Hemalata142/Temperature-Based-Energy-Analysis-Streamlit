import streamlit as st
import json
import pandas as pd
import os
from matplotlib.colors import LinearSegmentedColormap
import altair as alt
import datetime
import numpy as np

@st.cache_data
def load_data(project_name):
    json_file = [file for file in os.listdir(project_name) if file.endswith('.json')]
    with open(f"{project_name}/{json_file[0]}", "r") as json_file_data:
        data = json.load(json_file_data)
        
    excel_file = [file for file in os.listdir(project_name) if file.endswith('.xlsx')]
    df = pd.read_excel(f"{project_name}/{excel_file[0]}")
    return data, df

# Define project_name
project_name = st.session_state.get("project_name")
pd.set_option("styler.render.max_elements", 455838)

st.title(f":green[{project_name} Analysis]")

# Load data and cache it
data, df = load_data(project_name)

# Preprocess the data
df['Time_stamp'] = pd.to_datetime(df['TIME_STAMP'], format="%m/%d/%Y %H:%M:%S", errors='coerce')
df["Hour"] = df["Time_stamp"].dt.hour
df["week_day"] = df["Time_stamp"].dt.day_name()
df["date"] = df["Time_stamp"].dt.date
df["day"] = df["Time_stamp"].dt.day
df["month"] = df["Time_stamp"].dt.month_name()

# Sum system columns and calculate averages
for key, value in data.items():
    if key.startswith("System"):
        df[f"{key}_KW_SUM"] = df[value].sum(axis=1)
        df[f"{key}_KW_SUM_Average"] = df.groupby(['Hour', 'date'])[f"{key}_KW_SUM"].transform('mean')

# Custom color map
custom_cmap = LinearSegmentedColormap.from_list('custom_cmap', ['green','yellow', 'orange', 'red'])

c1,space,c2 = st.columns([1,0.20,1])
# Pagination control
page_size = c1.slider("Select number of rows per page", min_value=100, max_value=1000, step=100, value=100)
page_num = c2.number_input("Page number", min_value=1, max_value=(len(df) // page_size) + 1, step=1)

# Calculate the start and end rows
start_idx = (page_num - 1) * page_size
end_idx = start_idx + page_size

# Paginate the DataFrame
df_page = df.iloc[start_idx:end_idx]

# Apply gradient only to the visible page of data
styled_df = df_page.style.background_gradient(cmap=custom_cmap)

# Display the paginated DataFrame
st.write(styled_df)

columns_list = data.keys()

columns_list = [i for i in columns_list if i.startswith('System')]

tabs = st.tabs(columns_list)



def show_input_values(system_number,df_raw,json_data):
    c1,c2,c3,c4,c5 = st.columns([1,1,1,1,1])
    
    # st.write(df_raw)

    with c1:
        ds_hour_list = st.multiselect(f"Deselect Hour of the Day for System {system_number}",options=list(set(df_raw["Hour"])))
        m_round = st.number_input(
            f":green[Enter mRound Value for ∆T Filtered Data {system_number}]", value=0.5, placeholder="Type a number...",step=0.5
        )
        
    with c2:
        ds_day_list = st.multiselect(f"Deselect Specific Days of Month for System {system_number}",options=list(set(df_raw["day"])))
        instl_dt = st.date_input(f":green[Installation Date System {system_number}]",value=json_data[f"Installation Date System {system_number}"])
        
    with c3:
        ds_month_list = st.multiselect(f"Deselect Months for System {system_number}",options=list(set(df_raw["month"])))
        
    with c4:
        ds_weekday_list = st.multiselect(f"Deselect Weekdays for System {system_number}",options=list(set(df_raw["week_day"])))
        
    with c5:
        ds_dates_list = st.multiselect(f"Deselect Specific Dates for System {system_number}",options=list(set(df_raw["date"])))
        
    df_filtered = df_raw.copy()
    
    # Filter out the deselected hours
    if ds_hour_list:
        df_filtered = df_filtered[~df_filtered["Hour"].isin(ds_hour_list)]

    # Filter out the deselected days of the month
    if ds_day_list:
        df_filtered = df_filtered[~df_filtered["day"].isin(ds_day_list)]

    # Filter out the deselected years
    if ds_month_list:
        df_filtered = df_filtered[~df_filtered["month"].isin(ds_month_list)]

    # Filter out the deselected weekdays
    if ds_weekday_list:
        df_filtered = df_filtered[~df_filtered["week_day"].isin(ds_weekday_list)]

    # Filter out the deselected specific dates
    if ds_dates_list:
        df_filtered = df_filtered[~df_filtered["date"].isin(ds_dates_list)]
        
        
    df_filtered["∆T"] = df_filtered["TEMP_OUT"] - df_filtered["TEMP_GATE"]
    df_filtered["∆T M_ROUND"] = df_filtered["∆T"].apply(
                    lambda x: m_round * round(x/m_round) if not np.isnan(x) else np.nan
                )
    
    df_filtered["TEMP_OUT M_ROUND"] = df_filtered["TEMP_OUT"].apply(
                    lambda x: m_round * round(x/m_round) if not np.isnan(x) else np.nan
                )
    
    df_filtered["TEMP_GATE M_ROUND"] = df_filtered["TEMP_GATE"].apply(
                    lambda x: m_round * round(x/m_round) if not np.isnan(x) else np.nan
                )
    
    
    def compare_date(x):
        if pd.to_datetime(x) > pd.to_datetime(instl_dt):
            return "Post Installation"
        else:
            return "Pre Installation"
        
        
    df_filtered['Installation_Type'] = df_filtered["Time_stamp"].apply(lambda x: compare_date(x)) 
    
    
    # st.write(df_filtered)
        

    st.write(":blue[NO. Of Rows : ]",f":red[{str(len(df_filtered))}]")
    st.write(":blue[Total NO. Of Rows Removed : ]",f":red[{str(len(df_raw) - len(df_filtered))}]")
    
    return df_filtered
    
    

for i,tab in enumerate(tabs):
    with tab:
        system_number = i+1
        
        df_filtered = show_input_values(system_number,df,data)
        
        tab1,tab2,tab3,tab4 = st.tabs(["General Analysis","Pre/Post Installation Analysis on ∆T","Pre/Post Installation Analysis on TEMP_OUT","Pre/Post Installation Analysis on TEMP_GATE"])

        with tab1:
            for system_id,circuit_list in data.items():
                if system_id.startswith(f'System {system_number}'):
                    x1,x2 = st.columns([1,1])
                    
                    with x1:
                        df_filtered_hour = df_filtered.groupby('Hour').agg( 
                                                                    avg_kwh=(f"{system_id}_KW_SUM_Average", 'mean'),
                                                                    count=(f"{system_id}_KW_SUM_Average", 'size')
                                                                    ).reset_index()
                        
                        bar_chart = alt.Chart(df_filtered_hour).mark_bar().encode(
                                        x=alt.X('Hour:O', title='Hour of Day'),
                                        y=alt.Y('avg_kwh:Q', title='Average kWh'),
                                        color=alt.Color('avg_kwh:Q', scale=alt.Scale(scheme='viridis'), title='Average kWh'),  # Custom color scale
                                        tooltip=[alt.Tooltip('Hour:O', title='Hour'), 
                                                alt.Tooltip('avg_kwh:Q', title='Average kWh'),
                                                alt.Tooltip('count:Q', title='Data Points Count')]  # Adding count to the tooltip
                                    ).properties(
                                        title='AVERAGE KWH VS HOUR',
                                        width=600,
                                        height=400
                                    )
                                    
                        st.altair_chart(bar_chart, use_container_width=True)
                        
                        df_filtered_hour = df_filtered.groupby('week_day').agg( 
                                                                    avg_kwh=(f"{system_id}_KW_SUM_Average", 'mean'),
                                                                    count=(f"{system_id}_KW_SUM_Average", 'size')
                                                                    ).reset_index()
                        
                        bar_chart = alt.Chart(df_filtered_hour).mark_bar().encode(
                                        x=alt.X('week_day:O', title='Week'),
                                        y=alt.Y('avg_kwh:Q', title='Average kWh'),
                                        color=alt.Color('avg_kwh:Q', scale=alt.Scale(scheme='viridis'), title='Average kWh'),  # Custom color scale
                                        tooltip=[alt.Tooltip('week_day:O', title='Week'), 
                                                alt.Tooltip('avg_kwh:Q', title='Average kWh'),
                                                alt.Tooltip('count:Q', title='Data Points Count')]  # Adding count to the tooltip
                                    ).properties(
                                        title='AVERAGE KWH VS WEEKDAY',
                                        width=600,
                                        height=400
                                    )
                                    
                        st.altair_chart(bar_chart, use_container_width=True)
                        
                    with x2:
                        df_filtered_hour = df_filtered.groupby('date').agg( 
                                                                    avg_kwh=(f"{system_id}_KW_SUM_Average", 'mean'),
                                                                    count=(f"{system_id}_KW_SUM_Average", 'size')
                                                                    ).reset_index()
                        
                        bar_chart = alt.Chart(df_filtered_hour).mark_bar().encode(
                                        x=alt.X('date:T', title='Date'),
                                        y=alt.Y('avg_kwh:Q', title='Average kWh'),
                                        color=alt.Color('avg_kwh:Q', scale=alt.Scale(scheme='viridis'), title='Average kWh'),  # Custom color scale
                                        tooltip=[alt.Tooltip('date:T', title='Date'), 
                                                alt.Tooltip('avg_kwh:Q', title='Average kWh'),
                                                alt.Tooltip('count:Q', title='Data Points Count')]  # Adding count to the tooltip
                                    ).properties(
                                        title='AVERAGE KWH VS DATE',
                                        width=600,
                                        height=400
                                    )
                                    
                        st.altair_chart(bar_chart, use_container_width=True)
                        
                        df_filtered_hour = df_filtered.groupby('day').agg( 
                                                                    avg_kwh=(f"{system_id}_KW_SUM_Average", 'mean'),
                                                                    count=(f"{system_id}_KW_SUM_Average", 'size')
                                                                    ).reset_index()
                        
                        bar_chart = alt.Chart(df_filtered_hour).mark_bar().encode(
                                        x=alt.X('day:O', title='Day'),
                                        y=alt.Y('avg_kwh:Q', title='Average kWh'),
                                        color=alt.Color('avg_kwh:Q', scale=alt.Scale(scheme='viridis'), title='Average kWh'),  # Custom color scale
                                        tooltip=[alt.Tooltip('day:O', title='Day'), 
                                                alt.Tooltip('avg_kwh:Q', title='Average kWh'),
                                                alt.Tooltip('count:Q', title='Data Points Count')]  # Adding count to the tooltip
                                    ).properties(
                                        title='AVERAGE KWH VS Day',
                                        width=600,
                                        height=400
                                    )
                                    
                        st.altair_chart(bar_chart, use_container_width=True)
        
        with tab2:
            
            slider,space2 = st.columns([1,0.5])
            
            df_filtered_tab2 = df_filtered.copy()
            
            range_slider = slider.slider(f":green[Select Temperature Range for System {system_number}]", df_filtered_tab2["∆T M_ROUND"].min(), df_filtered_tab2["∆T M_ROUND"].max(),(df_filtered_tab2["∆T M_ROUND"].min(),df_filtered_tab2["∆T M_ROUND"].max()),0.25)
            
            if range_slider:
                df_filtered_tab2 = df_filtered_tab2[df_filtered_tab2['∆T M_ROUND'] >= range_slider[0]]
                df_filtered_tab2 = df_filtered_tab2[df_filtered_tab2['∆T M_ROUND'] <= range_slider[1]]
                
                df_raw_line_raw_plant = df_filtered_tab2.groupby(['Installation_Type','∆T M_ROUND']).agg(
                        avg_kwh=(f'System {system_number}_KW_SUM_Average', 'mean'),
                        count=(f'System {system_number}_KW_SUM_Average', 'size')
                    ).reset_index()
                
                chart_plant_room = alt.Chart(df_raw_line_raw_plant).mark_line(point=True, interpolate='cardinal').encode(
                        y='avg_kwh:Q',
                        x='∆T M_ROUND:Q',
                        color=alt.Color('Installation_Type:N', scale=alt.Scale(range=['#13661e', '#e81a07'])) ,
                        tooltip=[alt.Tooltip('Installation_Type:N', title='Installation_Type'), 
                                    alt.Tooltip('avg_kwh:Q', title='Average kWh'),
                                    alt.Tooltip('∆T M_ROUND:Q', title='Temperature'),
                                    alt.Tooltip('count:Q', title='Data Points Count')]
                    ).properties(
                        title="AVERAGE ENERGY CONSUMPTIONS SYSTEM 1 VS ∆T TEMPERATURE PRE & POST INSTALLATION",
                        width=600,
                        height=400
                    ).configure_view(
                        strokeOpacity=0  # Remove the border lines around the chart
                    ).configure_axis(
                        grid=True       # Remove gridlines if needed to make the chart cleaner
                    )
                    
                st.altair_chart(chart_plant_room, use_container_width=True)
                
                pivot_sys_1 = pd.pivot_table(df_filtered_tab2, 
                            index='∆T M_ROUND', 
                            columns='Installation_Type', 
                            values=f'System {system_number}_KW_SUM_Average', 
                            aggfunc=['mean', 'count'])
                try:
                    pivot_sys_1.columns = ['avg_kwh_post', 'avg_kwh_pre', 'count_post', 'count_pre']
                    pivot_sys_1 = pivot_sys_1.reset_index()
                    
                    v1,v2 = st.columns([1,1])
                    
                    with v1:
                        st.write(":green[Avg KWH Pre vs Post at each Temperature]")
                        st.write(pivot_sys_1)
                    
                    with v2:
                        df_raw_total_savings_plant = df_filtered_tab2.groupby(['Installation_Type']).agg(
                                avg_kwh=(f'System {system_number}_KW_SUM_Average', 'mean'),
                                data_points=(f'System {system_number}_KW_SUM_Average','size')
                            ).reset_index()
                        
                        st.write(":green[Savings Pre Installation VS Post Installation]")
                        st.write(df_raw_total_savings_plant)
                        post_kwh = float(df_raw_total_savings_plant[df_raw_total_savings_plant["Installation_Type"] == "Post Installation"]["avg_kwh"])
                        pre_kwh = float(df_raw_total_savings_plant[df_raw_total_savings_plant["Installation_Type"] == "Pre Installation"]["avg_kwh"])
                        savings = ((pre_kwh - post_kwh)/pre_kwh)*100
                        st.header(f":blue[TOTAL SAVINGS:] :green[{round(savings,2)}%]")
                except Exception as e:
                    pivot_sys_1.columns = ['avg_kwh_pre', 'count_pre']
                    pivot_sys_1 = pivot_sys_1.reset_index()
                    
                    v1,v2 = st.columns([1,1])
                    
                    with v1:
                        st.write(":green[Avg KWH Pre vs Post at each Temperature]")
                        st.write(pivot_sys_1)
                
                    with v2:
                        df_raw_total_savings_plant = df_filtered_tab2.groupby(['Installation_Type']).agg(
                                avg_kwh=(f'System {system_number}_KW_SUM_Average', 'mean'),
                                data_points=(f'System {system_number}_KW_SUM_Average','size')
                            ).reset_index()
                        
                        st.write(":green[Savings Pre Installation VS Post Installation]")
                        st.write(df_raw_total_savings_plant)

        with tab3:
            slider,space2 = st.columns([1,0.5])
            
            df_filtered_tab3 = df_filtered.copy()
            
            range_slider = slider.slider(f":green[Select TEMP_OUT Temperature Range for System {system_number}]", df_filtered_tab3["TEMP_OUT M_ROUND"].min(), df_filtered_tab3["TEMP_OUT M_ROUND"].max(),(df_filtered_tab3["TEMP_OUT M_ROUND"].min(),df_filtered_tab3["TEMP_OUT M_ROUND"].max()),0.25)
            
            if range_slider:
                df_filtered_tab3 = df_filtered_tab3[df_filtered_tab3['TEMP_OUT M_ROUND'] >= range_slider[0]]
                df_filtered_tab3 = df_filtered_tab3[df_filtered_tab3['TEMP_OUT M_ROUND'] <= range_slider[1]]
                
                df_raw_line_raw_plant = df_filtered_tab3.groupby(['Installation_Type','TEMP_OUT M_ROUND']).agg(
                        avg_kwh=(f'System {system_number}_KW_SUM_Average', 'mean'),
                        count=(f'System {system_number}_KW_SUM_Average', 'size')
                    ).reset_index()
                
                chart_plant_room = alt.Chart(df_raw_line_raw_plant).mark_line(point=True, interpolate='cardinal').encode(
                        y='avg_kwh:Q',
                        x='TEMP_OUT M_ROUND:Q',
                        color=alt.Color('Installation_Type:N', scale=alt.Scale(range=['#13661e', '#e81a07'])) ,
                        tooltip=[alt.Tooltip('Installation_Type:N', title='Installation_Type'), 
                                    alt.Tooltip('avg_kwh:Q', title='Average kWh'),
                                    alt.Tooltip('TEMP_OUT M_ROUND:Q', title='Temperature'),
                                    alt.Tooltip('count:Q', title='Data Points Count')]
                    ).properties(
                        title="AVERAGE ENERGY CONSUMPTIONS SYSTEM 1 VS TEMP_OUT TEMPERATURE PRE & POST INSTALLATION",
                        width=600,
                        height=400
                    ).configure_view(
                        strokeOpacity=0  # Remove the border lines around the chart
                    ).configure_axis(
                        grid=True       # Remove gridlines if needed to make the chart cleaner
                    )
                    
                st.altair_chart(chart_plant_room, use_container_width=True)
                
                pivot_sys_1 = pd.pivot_table(df_filtered_tab3, 
                            index='TEMP_OUT M_ROUND', 
                            columns='Installation_Type', 
                            values=f'System {system_number}_KW_SUM_Average', 
                            aggfunc=['mean', 'count'])
                try:
                    pivot_sys_1.columns = ['avg_kwh_post', 'avg_kwh_pre', 'count_post', 'count_pre']
                    pivot_sys_1 = pivot_sys_1.reset_index()
                    
                    v1,v2 = st.columns([1,1])
                    
                    with v1:
                        st.write(":green[Avg KWH Pre vs Post at each Temperature]")
                        st.write(pivot_sys_1)
                    
                    with v2:
                        df_raw_total_savings_plant = df_filtered_tab3.groupby(['Installation_Type']).agg(
                                avg_kwh=(f'System {system_number}_KW_SUM_Average', 'mean'),
                                data_points=(f'System {system_number}_KW_SUM_Average','size')
                            ).reset_index()
                        
                        st.write(":green[Savings Pre Installation VS Post Installation]")
                        st.write(df_raw_total_savings_plant)
                        post_kwh = float(df_raw_total_savings_plant[df_raw_total_savings_plant["Installation_Type"] == "Post Installation"]["avg_kwh"])
                        pre_kwh = float(df_raw_total_savings_plant[df_raw_total_savings_plant["Installation_Type"] == "Pre Installation"]["avg_kwh"])
                        savings = ((pre_kwh - post_kwh)/pre_kwh)*100
                        st.header(f":blue[TOTAL SAVINGS:] :green[{round(savings,2)}%]")
                except Exception as e:
                    pivot_sys_1.columns = ['avg_kwh_pre', 'count_pre']
                    pivot_sys_1 = pivot_sys_1.reset_index()
                    
                    v1,v2 = st.columns([1,1])
                    
                    with v1:
                        st.write(":green[Avg KWH Pre vs Post at each Temperature]")
                        st.write(pivot_sys_1)
                
                    with v2:
                        df_raw_total_savings_plant = df_filtered_tab3.groupby(['Installation_Type']).agg(
                                avg_kwh=(f'System {system_number}_KW_SUM_Average', 'mean'),
                                data_points=(f'System {system_number}_KW_SUM_Average','size')
                            ).reset_index()
                        
                        st.write(":green[Savings Pre Installation VS Post Installation]")
                        st.write(df_raw_total_savings_plant)
        with tab4:
            slider,space2 = st.columns([1,0.5])
            
            df_filtered_tab3 = df_filtered.copy()
            
            range_slider = slider.slider(f":green[Select TEMP_GATE Temperature Range for System {system_number}]", df_filtered_tab3["TEMP_GATE M_ROUND"].min(), df_filtered_tab3["TEMP_GATE M_ROUND"].max(),(df_filtered_tab3["TEMP_GATE M_ROUND"].min(),df_filtered_tab3["TEMP_GATE M_ROUND"].max()),0.25)
            
            if range_slider:
                df_filtered_tab3 = df_filtered_tab3[df_filtered_tab3['TEMP_GATE M_ROUND'] >= range_slider[0]]
                df_filtered_tab3 = df_filtered_tab3[df_filtered['TEMP_GATE M_ROUND'] <= range_slider[1]]
                
                df_raw_line_raw_plant = df_filtered_tab3.groupby(['Installation_Type','TEMP_GATE M_ROUND']).agg(
                        avg_kwh=(f'System {system_number}_KW_SUM_Average', 'mean'),
                        count=(f'System {system_number}_KW_SUM_Average', 'size')
                    ).reset_index()
                
                chart_plant_room = alt.Chart(df_raw_line_raw_plant).mark_line(point=True, interpolate='cardinal').encode(
                        y='avg_kwh:Q',
                        x='TEMP_GATE M_ROUND:Q',
                        color=alt.Color('Installation_Type:N', scale=alt.Scale(range=['#13661e', '#e81a07'])) ,
                        tooltip=[alt.Tooltip('Installation_Type:N', title='Installation_Type'), 
                                    alt.Tooltip('avg_kwh:Q', title='Average kWh'),
                                    alt.Tooltip('TEMP_GATE M_ROUND:Q', title='Temperature'),
                                    alt.Tooltip('count:Q', title='Data Points Count')]
                    ).properties(
                        title="AVERAGE ENERGY CONSUMPTIONS SYSTEM 1 VS TEMP_GATE TEMPERATURE PRE & POST INSTALLATION",
                        width=600,
                        height=400
                    ).configure_view(
                        strokeOpacity=0  # Remove the border lines around the chart
                    ).configure_axis(
                        grid=True       # Remove gridlines if needed to make the chart cleaner
                    )
                    
                st.altair_chart(chart_plant_room, use_container_width=True)
                
                pivot_sys_1 = pd.pivot_table(df_filtered_tab3, 
                            index='TEMP_GATE M_ROUND', 
                            columns='Installation_Type', 
                            values=f'System {system_number}_KW_SUM_Average', 
                            aggfunc=['mean', 'count'])
                try:
                    pivot_sys_1.columns = ['avg_kwh_post', 'avg_kwh_pre', 'count_post', 'count_pre']
                    pivot_sys_1 = pivot_sys_1.reset_index()
                    
                    v1,v2 = st.columns([1,1])
                    
                    with v1:
                        st.write(":green[Avg KWH Pre vs Post at each Temperature]")
                        st.write(pivot_sys_1)
                    
                    with v2:
                        df_raw_total_savings_plant = df_filtered_tab3.groupby(['Installation_Type']).agg(
                                avg_kwh=(f'System {system_number}_KW_SUM_Average', 'mean'),
                                data_points=(f'System {system_number}_KW_SUM_Average','size')
                            ).reset_index()
                        
                        st.write(":green[Savings Pre Installation VS Post Installation]")
                        st.write(df_raw_total_savings_plant)
                        post_kwh = float(df_raw_total_savings_plant[df_raw_total_savings_plant["Installation_Type"] == "Post Installation"]["avg_kwh"])
                        pre_kwh = float(df_raw_total_savings_plant[df_raw_total_savings_plant["Installation_Type"] == "Pre Installation"]["avg_kwh"])
                        savings = ((pre_kwh - post_kwh)/pre_kwh)*100
                        st.header(f":blue[TOTAL SAVINGS:] :green[{round(savings,2)}%]")
                except Exception as e:
                    pivot_sys_1.columns = ['avg_kwh_pre', 'count_pre']
                    pivot_sys_1 = pivot_sys_1.reset_index()
                    
                    v1,v2 = st.columns([1,1])
                    
                    with v1:
                        st.write(":green[Avg KWH Pre vs Post at each Temperature]")
                        st.write(pivot_sys_1)
                
                    with v2:
                        df_raw_total_savings_plant = df_filtered_tab3.groupby(['Installation_Type']).agg(
                                avg_kwh=(f'System {system_number}_KW_SUM_Average', 'mean'),
                                data_points=(f'System {system_number}_KW_SUM_Average','size')
                            ).reset_index()
                        
                        st.write(":green[Savings Pre Installation VS Post Installation]")
                        st.write(df_raw_total_savings_plant)
            
                            
                        