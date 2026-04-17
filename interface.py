import PySimpleGUI as sg
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import json
from collections import OrderedDict
import random
import os

def load_users():
    try:
        with open('users.json', 'r') as f:
            return json.load(f)
    except:
        return {"users": []}

def save_users(users):
    with open('users.json', 'w') as f:
        json.dump(users, f, indent=4)

def load_insights():
    try:
        with open('sleep_insights.json', 'r') as f:
            return json.load(f)
    except:
        return {"insights": ["No insights available."]}

def save_active_user(username):
    with open("active_user.json", "w") as f:
        json.dump({"user": username}, f)

def login_window():
    users = load_users()

    layout = [
        [sg.Text("Username"), sg.Input(key='-USER-')],
        [sg.Text("Password"), sg.Input(password_char='*', key='-PASS-')],
        [sg.Button('Login'), sg.Button('Create Account')]
    ]

    window = sg.Window("Login", layout)

    while True:
        event, values = window.read()

        if event == sg.WINDOW_CLOSED:
            break

        elif event == 'Login':
            username = values['-USER-']
            password = values['-PASS-']

            for user in users['users']:
                if user['username'] == username and user['password'] == password:
                    save_active_user(username)
                    window.close()
                    return username

            sg.popup("Invalid username or password")

        elif event == 'Create Account':
            window.close()
            return create_account_window()

    window.close()

def create_account_window():
    users = load_users()

    layout = [
        [sg.Text("New Username"), sg.Input(key='-USER-')],
        [sg.Text("New Password"), sg.Input(password_char='*', key='-PASS-')],
        [sg.Button('Create'), sg.Button('Back')]
    ]

    window = sg.Window("Create Account", layout)

    while True:
        event, values = window.read()

        if event in (sg.WINDOW_CLOSED, 'Back'):
            break

        elif event == 'Create':
            username = values['-USER-']
            password = values['-PASS-']

            if not username or not password:
                sg.popup("Please enter both fields")
                continue

            for user in users['users']:
                if user['username'] == username:
                    sg.popup("User already exists")
                    continue

            users['users'].append({
                "username": username,
                "password": password
            })

            save_users(users)
            sg.popup("Account created successfully!")
            window.close()
            return username

    window.close()


def draw_figure(canvas, figure):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(fill='both', expand=1)
    return figure_canvas_agg

def create_pie_chart(sleep, awake):
    fig, ax = plt.subplots()
    ax.pie([sleep, awake],
           labels=["Sleep", "Awake"],
           colors=["gold", "red"],
           autopct='%1.1f%%')
    return fig

def create_histogram(data, dates, user):
    fig, ax = plt.subplots()
    ax.bar(data.index, data.values)
    ax.set_title(f"Sleep Record of {user}")
    return fig

def sleep_record_screen(user_data, unique_dates, user):
    insights = load_insights()
    daily_sleep = user_data.groupby(user_data['date'].dt.date)['sleep'].sum()

    fig = create_histogram(daily_sleep, unique_dates, user)

    layout = [
        [sg.Canvas(key='-CANVAS-')],
        [sg.Text('', key='-INSIGHT-')],
        [sg.Button('Insight'), sg.Button('Back')]
    ]

    window = sg.Window("Sleep Record", layout, finalize=True)
    draw_figure(window['-CANVAS-'].TKCanvas, fig)

    while True:
        event, _ = window.read()

        if event in (sg.WINDOW_CLOSED, 'Back'):
            break

        elif event == 'Insight':
            window['-INSIGHT-'].update(random.choice(insights['insights']))

    window.close()

def data_screen(user):
    if not os.path.exists('sleep_dataset.csv'):
        sg.popup("No data file found!")
        return

    data = pd.read_csv('sleep_dataset.csv', parse_dates=['timestamp', 'date'])
    user_data = data[data['user_id'] == user]

    if user_data.empty:
        sg.popup("No data available")
        return

    user_data['sleep'] = user_data['sleep_state']
    daily_sleep = user_data.groupby(user_data['date'].dt.date)['sleep'].sum()

    layout = [
        [sg.Text(f"Welcome {user}")],
        [sg.Button('View Charts'), sg.Button('Exit')]
    ]

    window = sg.Window("Dashboard", layout)

    while True:
        event, _ = window.read()

        if event in (sg.WINDOW_CLOSED, 'Exit'):
            break

        elif event == 'View Charts':
            window.close()
            sleep_record_screen(user_data, list(daily_sleep.index), user)
            return

    window.close()

if __name__ == "__main__":
    user = login_window()
    if user:
        data_screen(user)