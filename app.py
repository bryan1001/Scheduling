import streamlit as st
from streamlit_calendar import calendar
from datetime import datetime, timedelta, date
import schedule
import time

st.set_page_config(layout="wide")
# #     range(0, 5): 0,  # Bry: 11/17 to 11/22
#     range(5, 7): 1,  # Mel: 11/22 to 11/24
#     range(10, 15): 0,  # Bry: 11/27 to 12/1
#     range(35, 42): 1,  # Mel: 12/22 to 12/29


st.title("Shared Custody Schedule Optimizer")

# Date range selector for overall schedule
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Schedule Start Date", date(2024, 11, 17))
with col2:
    num_days = st.number_input("Number of Days", min_value=14, value=50)

end_date = start_date + timedelta(days=num_days)
if "events" not in st.session_state:
    st.session_state["events"] = []


# st.write(st.session_state.events)


# Calendar events for fixed assignments


st.session_state["last_update_time"] = 0
st.session_state["start_date"] = start_date
st.session_state["num_days"] = num_days


@st.fragment(run_every=1)
def single_cal(month):
    events = st.session_state["events"][:]
    events_by_date = {event["start"]: event for event in events}

    if "events_new" in st.session_state:
        for event in st.session_state["events_new"]:
            if event["start"] not in events_by_date:
                events.append(event)
                events_by_date[event["start"]] = event

    calendar_options = {
        "headerToolbar": {
            "left": "",
            "center": "title",
            "right": "",
        },
        "contentHeight": 450,
        "initialView": "dayGridMonth",
        "initialDate": month.strftime("%Y-%m-%d"),
        "showNonCurrentDates": False,
        "validRange": {
            "start": start_date.strftime("%Y-%m-%d"),
            "end": (start_date + timedelta(days=num_days)).strftime("%Y-%m-%d"),
        },
    }

    calendar_options = calendar_options.copy()
    calendar_options["events"] = events[:]
    # calendar_options["start"] = month.strftime("%Y-%m-%d")
    res = calendar(
        events=events,
        options=calendar_options,
        custom_css="--fc-bg-event-opacity: 1;",
        key=f"calendar{str(month)}",
    )

    # Handle calendar interactions
    if res.get("dateClick"):

        if time.time() - st.session_state["last_update_time"] < 0.1:
            return
        st.session_state["last_update_time"] = time.time()
        clicked_event = res.get("dateClick")
        # Handle event clicks to cycle through states
        clicked_date = clicked_event.get("date")
        clicked_date = clicked_date[:10]

        existing_events = [
            e for e in st.session_state["events"] if e["start"] == clicked_date
        ]
        st.session_state["events_new"] = []

        if not existing_events:
            # Add new event for Bry
            new_event = {
                "title": "Bry",
                "start": clicked_date,
                "end": clicked_date,
                "color": "#1976d2",
                "allDay": True,
                "display": "background",
            }
            st.session_state.events.append(new_event)
        elif existing_events[0]["title"] == "Bry":
            # Change to Mel
            existing_events[0]["title"] = "Mel"
            existing_events[0]["color"] = "#2e7d32"
        else:
            # Remove event
            st.session_state["events"].remove(existing_events[0])
        st.session_state["events"] = st.session_state["events"][:]

        st.rerun(scope="fragment")


from dateutil.relativedelta import relativedelta


def cal():
    # Initialize calendar

    # calculate number of months

    num_months = (
        (end_date.year - start_date.year) * 12 + end_date.month - start_date.month
    ) + 1

    for i in range(0, num_months, 3):
        cols = st.columns(
            3,
        )
        for j in range(i, min(i + 3, num_months)):
            with cols[j % 3]:
                single_cal(start_date + relativedelta(months=j))


cal()

if st.button("Clear"):
    st.session_state["events_new"] = []
if st.button("Generate"):
    pre_assigned = {}
    for event in st.session_state["events"]:
        start = datetime.strptime(
            event["start"][: (4 + 1 + 2 + 1 + 2)], "%Y-%m-%d"
        ).date()
        end = datetime.strptime(event["end"][: (4 + 1 + 2 + 1 + 2)], "%Y-%m-%d").date()
        parent = 0 if event["title"] == "Bry" else 1
        days = (end - start).days
        start_offset = (start - start_date).days
        pre_assigned[range(start_offset, start_offset + days + 1)] = parent

    solution, full_week_count = schedule.solve_shared_custody_exhaustive(
        start_date, num_days, pre_assigned
    )
    st.session_state["events_new"] = [
        {
            "title": solution[i],
            "start": (start_date + timedelta(days=i)).strftime("%Y-%m-%d"),
            "end": (start_date + timedelta(days=i)).strftime("%Y-%m-%d"),
            "color": "#003161" if solution[i] == "Bry" else "#005404",
            "allDay": True,
            "display": "background",
        }
        for i in range(num_days)
    ]


# st.write(f"Full Weeks: {full_week_count}")
