import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import pytz


# Set page configuration
st.set_page_config(
    page_title="Afra & Rira Care Scheduler",
    page_icon="👶👶",
    layout="wide"
)

# Adding date and time
import time
from datetime import datetime, timedelta

# set a function for due tasks 
def check_due_tasks():
    """Check for tasks that are due or overdue and show notifications"""
    now = get_current_time()
    due_tasks = []
    
    for task_name, task_data in st.session_state.tasks.items():
        next_time = str_to_time(task_data['next_time'])
        time_diff = (next_time - now).total_seconds() / 60
        
        # Check if baby field exists (for backward compatibility)
        baby = task_data.get('baby', 'Both')  # Default to 'Both' if not specified
        
        # If task is due within 2 minutes or overdue
        if time_diff <= 2:
            due_tasks.append({
                'task': task_name,
                'baby': baby,
                'time': next_time.strftime('%I:%M %p'),
                'overdue': time_diff < 0
            })
    
    return due_tasks


# Initialize session state variables if they don't exist
if 'tasks' not in st.session_state:
    st.session_state.tasks = {}
    
if 'timezone' not in st.session_state:
    st.session_state.timezone = "Asia/Tehran"  # Default timezone

# Function to save data to a file
def save_data():
    data = {
        'tasks': st.session_state.tasks,
        'timezone': st.session_state.timezone
    }
    with open('baby_scheduler_data.json', 'w') as f:
        json.dump(data, f)

# Function to load data from a file
def load_data():
    if os.path.exists('baby_scheduler_data.json'):
        with open('baby_scheduler_data.json', 'r') as f:
            data = json.load(f)
            st.session_state.tasks = data.get('tasks', {})
            st.session_state.timezone = data.get('timezone', "Asia/Tehran")

# Load data at startup
load_data()

# Get current time in selected timezone
def get_current_time():
    tz = pytz.timezone(st.session_state.timezone)
    return datetime.now(tz)

# Get common timezones for dropdown
def get_common_timezones():
    common_timezones = [
        "Asia/Tehran", "US/Eastern", "US/Central", "US/Mountain", "US/Pacific",
        "Europe/London", "Europe/Paris", "Asia/Tokyo", "Australia/Sydney"
    ]
    return common_timezones

# Helper functions for time handling
def time_to_str(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def str_to_time(s):
    if s:
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.timezone(st.session_state.timezone))
    return None

# App title and introduction
st.title("👶👶 Afra & Rira Care Scheduler")

# Add image of the twins
try:
    st.image("twins.jpg", caption="Rira and Afra", use_container_width=True)
except:
    st.warning("Please add a file named 'twins_photo.jpg' to the same folder as this app.")

st.markdown("""
This app helps you track and schedule care tasks for your twins.
Add tasks like medications, feedings, and other care activities.
""")

# Sidebar for settings
with st.sidebar:
    st.header("Settings")
    selected_timezone = st.selectbox(
        "Timezone", 
        options=get_common_timezones(),
        index=get_common_timezones().index(st.session_state.timezone)
    )
    
    if selected_timezone != st.session_state.timezone:
        st.session_state.timezone = selected_timezone
        save_data()
        st.rerun()
    
    st.markdown("---")
    st.header("Add New Task")
    
    # Form for adding a new task
    with st.form("new_task_form"):
        task_name = st.text_input("Task Name", placeholder="Medicine name, feeding, etc.")
        task_type = st.selectbox("Task Type", ["Medicine", "Vitamin", "Feeding", "Diaper Change", "Other"])
        
        baby_selection = st.radio("For which baby?", ["Afra", "Rira", "Both"])

        interval_unit = st.selectbox("Interval Unit", ["Hours", "Minutes"])
        if interval_unit == "Hours":
            interval_value = st.number_input("Interval (Hours)", min_value=1, max_value=24, value=4)
            interval_minutes = interval_value * 60
        else:
            interval_value = st.number_input("Interval (Minutes)", min_value=10, max_value=1440, value=30)
            interval_minutes = interval_value
        
        doses_per_day = st.number_input("Doses/Times Per Day (Optional)", min_value=1, max_value=24, value=6)
        
        notes = st.text_area("Notes (Optional)", placeholder="Special instructions, dosage, etc.")
        
        submit_button = st.form_submit_button("Add Task")
        
        if submit_button and task_name:
            now = get_current_time()
            st.session_state.tasks[task_name] = {
                "type": task_type,
                "baby": baby_selection,
                "interval_minutes": interval_minutes,
                "doses_per_day": doses_per_day,
                "notes": notes,
                "last_time": time_to_str(now),
                "next_time": time_to_str(now + timedelta(minutes=interval_minutes)),
                "completed_today": 0
            }
            save_data()
            st.success(f"Task '{task_name}' added successfully!")

# Main content area
st.header("Current Tasks")

# Get current time for calculations
now = get_current_time()
st.write(f"Current time: {now.strftime('%A, %B %d, %Y %I:%M %p')}")

# create a container for notifications that we'll update
notification_container = st.empty()

# auto-refresh for checking notifications
if st.button("Check for Due Tasks", key="check_notifications"):
    st.rerun()

# Check for due tasks and display notifications
due_tasks = check_due_tasks()
if due_tasks:
    with notification_container.container():
        st.markdown("### ⚠️ Tasks Due Now!")
        for task in due_tasks:
            status = "OVERDUE" if task['overdue'] else "DUE NOW"
            st.error(f"**{status}**: {task['task']} for {task['baby']} at {task['time']}")
            
            # buttons to mark as complete or snooze
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Complete", key=f"notify_complete_{task['task']}"):
                    now = get_current_time()
                    task_data = st.session_state.tasks[task['task']]
                    st.session_state.tasks[task['task']]['last_time'] = time_to_str(now)
                    st.session_state.tasks[task['task']]['next_time'] = time_to_str(
                        now + timedelta(minutes=task_data['interval_minutes'])
                    )
                    st.session_state.tasks[task['task']]['completed_today'] += 1
                    save_data()
                    st.rerun()
            
            with col2:
                if st.button(f"Snooze 15 min", key=f"notify_snooze_{task['task']}"):
                    now = get_current_time()
                    st.session_state.tasks[task['task']]['next_time'] = time_to_str(
                        now + timedelta(minutes=15)
                    )
                    save_data()
                    st.rerun()
        
        # sound alert for notifications
        st.markdown(
            """
            <audio autoplay>
                <source src="https://www.soundjay.com/buttons/sounds/button-1.mp3" type="audio/mpeg">
            </audio>
            """,
            unsafe_allow_html=True
        )

if not st.session_state.tasks:
    st.info("No tasks added yet. Use the sidebar to add a new task.")
else:
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["All Tasks", "Timeline", "Completed Today"])
    
    with tab1:
        # Display all tasks in a table
        for task_name, task_data in st.session_state.tasks.items():
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.subheader(task_name)
                st.caption(f"Type: {task_data['type']} | For: {task_data.get('baby', 'Both')}")
                if task_data['notes']:
                    st.text(task_data['notes'])
            
            with col2:
                last_time = str_to_time(task_data['last_time'])
                next_time = str_to_time(task_data['next_time'])
                
                st.markdown(f"**Last done:** {last_time.strftime('%I:%M %p')}")
                
                # Color code the next time based on urgency
                time_diff = (next_time - now).total_seconds() / 60
                if time_diff < 0:
                    st.markdown(f"**Next due:** :red[{next_time.strftime('%I:%M %p')} (Overdue)]")
                elif time_diff < 30:
                    st.markdown(f"**Next due:** :orange[{next_time.strftime('%I:%M %p')} (Soon)]")
                else:
                    st.markdown(f"**Next due:** {next_time.strftime('%I:%M %p')}")
                
                st.text(f"Done today: {task_data['completed_today']}/{task_data['doses_per_day']}")
            
            with col3:
                # Buttons for task actions
                if st.button(f"Complete Now", key=f"complete_{task_name}"):
                    now = get_current_time()
                    st.session_state.tasks[task_name]['last_time'] = time_to_str(now)
                    st.session_state.tasks[task_name]['next_time'] = time_to_str(now + timedelta(minutes=task_data['interval_minutes']))
                    st.session_state.tasks[task_name]['completed_today'] += 1
                    save_data()
                    st.rerun()
                
                if st.button(f"Reschedule", key=f"reschedule_{task_name}"):
                    now = get_current_time()
                    st.session_state.tasks[task_name]['next_time'] = time_to_str(now + timedelta(minutes=task_data['interval_minutes']))
                    save_data()
                    st.rerun()
                
                if st.button(f"Delete", key=f"delete_{task_name}"):
                    del st.session_state.tasks[task_name]
                    save_data()
                    st.rerun()
            
            st.divider()
    
    with tab2:
        # Create a timeline of upcoming tasks
        upcoming_tasks = []
        for task_name, task_data in st.session_state.tasks.items():
            next_time = str_to_time(task_data['next_time'])
            upcoming_tasks.append({
                'task': task_name,
                'type': task_data['type'],
                'next_time': next_time,
                'time_diff_minutes': (next_time - now).total_seconds() / 60
            })
        
        # Sort by upcoming time
        upcoming_tasks.sort(key=lambda x: x['next_time'])
        
        # Create a timeline
        st.subheader("Upcoming Schedule")
        for task in upcoming_tasks:
            time_diff = task['time_diff_minutes']
            if time_diff < 0:
                st.markdown(f"**:red[OVERDUE]**: {task['task']} ({task['type']}) - {task['next_time'].strftime('%I:%M %p')}")
            elif time_diff < 30:
                st.markdown(f"**:orange[SOON]**: {task['task']} ({task['type']}) - {task['next_time'].strftime('%I:%M %p')}")
            else:
                hours = int(time_diff // 60)
                minutes = int(time_diff % 60)
                time_text = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
                st.markdown(f"**In {time_text}**: {task['task']} ({task['type']}) - {task['next_time'].strftime('%I:%M %p')}")
    
    with tab3:
        # Show a summary of completed tasks today
        st.subheader("Completed Today")
        
        # Create a dataframe for the completed tasks
        completed_data = []
        for task_name, task_data in st.session_state.tasks.items():
            completed_data.append({
                'Task': task_name,
                'Type': task_data['type'],
                'Completed': task_data['completed_today'],
                'Target': task_data['doses_per_day'],
                'Progress': task_data['completed_today'] / task_data['doses_per_day']
            })
        
        if completed_data:
            df = pd.DataFrame(completed_data)
            
            # Display as a table
            st.dataframe(df[['Task', 'Type', 'Completed', 'Target']], hide_index=True)
            
            # Show progress bars
            for _, row in df.iterrows():
                progress_text = f"{row['Task']}: {int(row['Completed'])}/{int(row['Target'])}"
                st.progress(min(1.0, row['Progress']), text=progress_text)
        else:
            st.info("No tasks have been completed today.")

    # Add a button to reset all "completed today" counters
    if st.button("Reset All Daily Counts"):
        for task_name in st.session_state.tasks:
            st.session_state.tasks[task_name]['completed_today'] = 0
        save_data()
        st.success("All daily counts have been reset!")
        st.rerun()


# Auto refresh section
st.markdown("---")
st.subheader("Notification Settings")
auto_refresh = st.checkbox("Enable auto-refresh to check for due tasks", value=True)
if auto_refresh:
    # Change seconds to minutes and adjust the range and default
    refresh_interval = st.slider("Refresh interval (minutes)", 1, 60, 30) 
    st.info(f"Page will automatically refresh every {refresh_interval} minutes to check for due tasks")
    st.markdown(
        f"""
        <meta http-equiv="refresh" content="{refresh_interval * 60}">
        """,
        unsafe_allow_html=True
    )


# Footer
st.markdown("---")
st.markdown("Made with ❤️ for my sister and her beloved twins!")
