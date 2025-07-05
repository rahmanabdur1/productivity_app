import dash
from dash import html, dcc, Input, Output, State, callback_context
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import requests # This is now crucial for backend communication
import json # For handling JSON data

# --- Configuration for Backend API ---
# IMPORTANT: Ensure this matches your Django backend's URL
API_BASE_URL = "http://127.0.0.1:8000/api/"

# --- Dash App Initialization ---
app = dash.Dash(__name__)

# --- Helper Function for API Calls ---
def fetch_data_from_backend(endpoint, auth_token=None, params=None, method='GET', data=None):
    """
    Helper function to make authenticated API calls to the Django backend.
    """
    headers = {}
    if auth_token:
        headers["Authorization"] = f"Token {auth_token}"
    
    # For POST/PUT/PATCH, ensure content-type is application/json
    if method in ['POST', 'PUT', 'PATCH']:
        headers["Content-Type"] = "application/json"
        if data:
            data = json.dumps(data) # Convert dict to JSON string

    try:
        if method == 'GET':
            response = requests.get(f"{API_BASE_URL}{endpoint}", headers=headers, params=params)
        elif method == 'POST':
            response = requests.post(f"{API_BASE_URL}{endpoint}", headers=headers, data=data)
        elif method == 'PUT':
            response = requests.put(f"{API_BASE_URL}{endpoint}", headers=headers, data=data)
        elif method == 'PATCH':
            response = requests.patch(f"{API_BASE_URL}{endpoint}", headers=headers, data=data)
        elif method == 'DELETE':
            response = requests.delete(f"{API_BASE_URL}{endpoint}", headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        
        # Check if response has content before trying to parse JSON
        if response.content:
            return response.json()
        return {} # Return empty dict for no-content responses (e.g., DELETE)

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err} - {response.status_code} - {response.text}")
        return {"error": f"HTTP Error: {response.status_code} - {response.text}"}
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Connection error occurred: {conn_err}. Is backend running at {API_BASE_URL}?")
        return {"error": "Connection Error: Could not connect to backend."}
    except requests.exceptions.Timeout as timeout_err:
        print(f"Timeout error occurred: {timeout_err}")
        return {"error": "Timeout Error: Request to backend timed out."}
    except requests.exceptions.RequestException as req_err:
        print(f"An unexpected request error occurred: {req_err}")
        return {"error": f"Request Error: {req_err}"}
    except json.JSONDecodeError as json_err:
        print(f"JSON decode error: {json_err} - Response content: {response.text}")
        return {"error": "Invalid JSON response from backend."}


# --- Reusable Components ---
def create_card(title, content):
    return html.Div(
        className="bg-white p-6 rounded-xl shadow-lg border border-gray-200",
        children=[
            html.H3(title, className="text-xl font-semibold text-gray-800 mb-4"),
            content
        ]
    )

def create_filter_bar():
    return html.Div(
        className="bg-gray-100 p-4 rounded-lg shadow-sm flex flex-wrap gap-4 items-center mb-6",
        children=[
            html.Div(className="flex items-center space-x-2", children=[
                html.I(className="lucide lucide-filter w-5 h-5 text-gray-600"),
                html.Span("Filter By:", className="text-gray-700 font-medium")
            ]),
            dcc.Dropdown(
                id='filter-date-range',
                options=[
                    {'label': 'Daily', 'value': 'daily'},
                    {'label': 'Weekly', 'value': 'weekly'},
                    {'label': 'Monthly', 'value': 'monthly'}
                ],
                value='weekly',
                clearable=False,
                className="dash-dropdown", # Apply custom class
                style={'width': '150px'}
            ),
            dcc.Dropdown(
                id='filter-team',
                options=[
                    {'label': 'All Teams', 'value': 'All'},
                    {'label': 'Team Alpha', 'value': 'Team Alpha'},
                    {'label': 'Team Beta', 'value': 'Team Beta'},
                    {'label': 'Team Gamma', 'value': 'Team Gamma'}
                ],
                value='All',
                clearable=False,
                className="dash-dropdown",
                style={'width': '150px'}
            ),
            dcc.Dropdown(
                id='filter-project',
                options=[
                    {'label': 'All Projects', 'value': 'All'},
                    {'label': 'Project X', 'value': 'Project X'},
                    {'label': 'Project Y', 'value': 'Project Y'},
                    {'label': 'Project Z', 'value': 'Project Z'}
                ],
                value='All',
                clearable=False,
                className="dash-dropdown",
                style={'width': '150px'}
            ),
            html.Button(
                [
                    html.I(className="lucide lucide-download w-5 h-5 mr-2"),
                    html.Span("Export Report")
                ],
                id='export-report-button',
                className="ml-auto bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md shadow-md flex items-center space-x-2 transition duration-300"
            )
        ]
    )

# --- Dashboard Layouts (Now fetch data from backend) ---

def employee_dashboard_layout(auth_token):
    # Fetch data from backend
    daily_hours_data = fetch_data_from_backend('timelogs/daily_summary/', auth_token)
    app_usage_data = fetch_data_from_backend('appusages/summary/', auth_token)

    if "error" in daily_hours_data or "error" in app_usage_data:
        return html.Div(f"Error loading employee dashboard data: {daily_hours_data.get('error') or app_usage_data.get('error')}", className="text-red-500 p-4")

    daily_hours_df = pd.DataFrame(daily_hours_data)
    app_usage_df = pd.DataFrame(app_usage_data)

    fig_daily_hours = px.line(daily_hours_df, x='date', y=['working_hours', 'app_usage_hours'],
                              title='Daily & Weekly Working Hours & App Usage')
    fig_daily_hours.update_layout(hovermode="x unified")

    fig_productivity_score = px.line(daily_hours_df, x='date', y='productivity_score',
                                       title='Productivity Score Trend',
                                       range_y=[0, 100])
    fig_productivity_score.update_layout(hovermode="x unified")

    fig_app_usage = px.pie(app_usage_df, values='total_usage_hours', names='app_name',
                           title='Application Usage Breakdown')

    return html.Div(
        className="p-6 space-y-8",
        children=[
            html.H2("Employee Dashboard", className="text-4xl font-extrabold text-gray-900 mb-8 font-inter"),
            create_filter_bar(),
            html.Div(className="grid grid-cols-1 lg:grid-cols-2 gap-8", children=[
                create_card("Daily & Weekly Working Hours", dcc.Graph(figure=fig_daily_hours)),
                create_card("Productivity Score Trend", dcc.Graph(figure=fig_productivity_score))
            ]),
            html.Div(className="grid grid-cols-1 lg:grid-cols-2 gap-8", children=[
                create_card("Application Usage Breakdown", dcc.Graph(figure=fig_app_usage)),
                create_card(
                    "Productivity Suggestions",
                    html.Ul(className="list-disc list-inside text-gray-700 space-y-2", children=[
                        html.Li("Take short breaks every 90 minutes to recharge."),
                        html.Li("Minimize distractions by turning off unnecessary notifications."),
                        html.Li("Prioritize tasks to focus on high-impact activities."),
                        html.Li("Review your most productive hours and schedule demanding tasks accordingly."),
                        html.Li("Ensure a comfortable and ergonomic workspace.")
                    ])
                )
            ])
        ]
    )

def team_head_dashboard_layout(auth_token):
    # For team head, you'd fetch team-specific data
    # Example: team_productivity_data = fetch_data_from_backend('teams/productivity_summary/', auth_token, params={'team_id': '...' })
    team_productivity_df = pd.DataFrame([
        {'Team': 'Team Alpha', 'Productivity Score': 85},
        {'Team': 'Team Beta', 'Productivity Score': 78},
        {'Team': 'Team Gamma', 'Productivity Score': 92},
    ]) # Mock data for now, replace with API call

    team_activity_df = pd.DataFrame([
        {'Date': '2025-07-01', 'Team Alpha Activity': 60, 'Team Beta Activity': 55},
        {'Date': '2025-07-02', 'Team Alpha Activity': 65, 'Team Beta Activity': 60},
        {'Date': '2025-07-03', 'Team Alpha Activity': 70, 'Team Beta Activity': 62},
        {'Date': '2025-07-04', 'Team Alpha Activity': 68, 'Team Beta Activity': 58},
    ]) # Mock data for now, replace with API call

    fig_team_productivity = px.bar(team_productivity_df, x='Team', y='Productivity Score',
                                   title='Team Productivity Comparison',
                                   range_y=[0, 100])
    fig_team_productivity.update_traces(marker_color='#8884d8')

    fig_team_activity = px.line(team_activity_df, x='Date', y=team_activity_df.columns[1:],
                                title='Team Activity Trends')
    fig_team_activity.update_layout(hovermode="x unified")

    return html.Div(
        className="p-6 space-y-8",
        children=[
            html.H2("Team Head Dashboard", className="text-4xl font-extrabold text-gray-900 mb-8 font-inter"),
            create_filter_bar(),
            html.Div(className="grid grid-cols-1 lg:grid-cols-2 gap-8", children=[
                create_card("Team Productivity Comparison", dcc.Graph(figure=fig_team_productivity)),
                create_card("Team Activity Trends", dcc.Graph(figure=fig_team_activity))
            ]),
            create_card(
                "Alerts for Unusual Behavior",
                html.Ul(className="list-disc list-inside text-gray-700 space-y-2", children=[
                    html.Li(html.Span("John Doe: Significant drop in activity for the last 2 days.", className="text-red-600 font-semibold")),
                    html.Li("Jane Smith: Consistently low productivity score this week."),
                    html.Li("Team Gamma: 15% decrease in average working hours compared to last month.")
                ])
            )
        ]
    )

def project_manager_dashboard_layout(auth_token):
    # For project manager, you'd fetch project-specific data
    # Example: project_allocation_data = fetch_data_from_backend('projects/allocation_summary/', auth_token)
    project_allocation_df = pd.DataFrame([
        {'Project': 'Project X', 'Time Spent (Hours)': 80},
        {'Project': 'Project Y', 'Time Spent (Hours)': 45},
        {'Project': 'Project Z', 'Time Spent (Hours)': 60},
    ]) # Mock data for now, replace with API call

    resource_usage_df = pd.DataFrame([
        {'Date': '2025-07-01', 'Developer Hours': 120, 'Designer Hours': 40},
        {'Date': '2025-07-02', 'Developer Hours': 110, 'Designer Hours': 45},
        {'Date': '2025-07-03', 'Developer Hours': 130, 'Designer Hours': 35},
    ]) # Mock data for now, replace with API call

    fig_project_allocation = px.bar(project_allocation_df, x='Project', y='Time Spent (Hours)',
                                    title='Time Allocation Per Project')
    fig_project_allocation.update_traces(marker_color='#8884d8')

    fig_resource_usage = px.line(resource_usage_df, x='Date', y=resource_usage_df.columns[1:],
                                 title='Resource Usage Across Teams')
    fig_resource_usage.update_layout(hovermode="x unified")

    project_progress_table = html.Table(
        className="min-w-full bg-white rounded-lg shadow-md",
        children=[
            html.Thead(className="bg-gray-200", children=[
                html.Tr(children=[
                    html.Th("Project", className="py-3 px-4 text-left text-sm font-semibold text-gray-700"),
                    html.Th("Status", className="py-3 px-4 text-left text-sm font-semibold text-gray-700"),
                    html.Th("Time Est.", className="py-3 px-4 text-left text-sm font-semibold text-gray-700"),
                    html.Th("Time Spent", className="py-3 px-4 text-left text-sm font-semibold text-gray-700"),
                    html.Th("Progress", className="py-3 px-4 text-left text-sm font-semibold text-gray-700")
                ])
            ]),
            html.Tbody(children=[
                html.Tr(className="border-b border-gray-200 hover:bg-gray-50", children=[
                    html.Td("Project Alpha", className="py-3 px-4"),
                    html.Td("On Track", className="py-3 px-4 text-green-600 font-medium"),
                    html.Td("200 hrs", className="py-3 px-4"),
                    html.Td("150 hrs", className="py-3 px-4"),
                    html.Td("75%", className="py-3 px-4")
                ]),
                html.Tr(className="border-b border-gray-200 hover:bg-gray-50", children=[
                    html.Td("Project Beta", className="py-3 px-4"),
                    html.Td("Delayed", className="py-3 px-4 text-orange-600 font-medium"),
                    html.Td("150 hrs", className="py-3 px-4"),
                    html.Td("160 hrs", className="py-3 px-4"),
                    html.Td("80%", className="py-3 px-4")
                ]),
                html.Tr(className="hover:bg-gray-50", children=[
                    html.Td("Project Gamma", className="py-3 px-4"),
                    html.Td("Planning", className="py-3 px-4 text-blue-600 font-medium"),
                    html.Td("300 hrs", className="py-3 px-4"),
                    html.Td("20 hrs", className="py-3 px-4"),
                    html.Td("5%", className="py-3 px-4")
                ])
            ])
        ]
    )

    return html.Div(
        className="p-6 space-y-8",
        children=[
            html.H2("Project Manager Dashboard", className="text-4xl font-extrabold text-gray-900 mb-8 font-inter"),
            create_filter_bar(),
            html.Div(className="grid grid-cols-1 lg:grid-cols-2 gap-8", children=[
                create_card("Time Allocation Per Project", dcc.Graph(figure=fig_project_allocation)),
                create_card("Resource Usage Across Teams", dcc.Graph(figure=fig_resource_usage))
            ]),
            create_card("Project Progress Reports", html.Div(className="overflow-x-auto", children=[project_progress_table]))
        ]
    )

def notifications_panel_layout(auth_token):
    # In a real app, notifications would be fetched from backend
    # notifications_data = fetch_data_from_backend('notifications/', auth_token)
    # if "error" in notifications_data:
    #     return html.Div(f"Error loading notifications: {notifications_data['error']}", className="text-red-500 p-4")
    
    # Mock data for now
    notifications = [
        {'id': 1, 'type': 'alert', 'message': 'Your daily app usage is 20% lower than average.', 'date': '2025-07-04'},
        {'id': 2, 'type': 'info', 'message': 'Team Alpha productivity increased by 10% this week!', 'date': '2025-07-03'},
        {'id': 3, 'type': 'warning', 'message': 'Project X is exceeding its estimated time by 10 hours.', 'date': '2025-07-02'},
        {'id': 4, 'type': 'alert', 'message': 'Sudden drop in focus time detected yesterday.', 'date': '2025-07-01'},
    ]

    def get_notification_color(ntype):
        if ntype == 'alert': return 'bg-red-100 border-red-400 text-red-700'
        if ntype == 'warning': return 'bg-yellow-100 border-yellow-400 text-yellow-700'
        if ntype == 'info': return 'bg-blue-100 border-blue-400 text-blue-700'
        return 'bg-gray-100 border-gray-400 text-gray-700'

    notifications_list = [
        html.Div(
            key=notification['id'],
            className=f"p-4 rounded-lg border-l-4 {get_notification_color(notification['type'])} shadow-sm flex items-center justify-between",
            children=[
                html.P(notification['message'], className="font-medium"),
                html.Span(notification['date'], className="text-sm text-gray-600")
            ]
        ) for notification in notifications
    ]

    return html.Div(
        className="p-6 space-y-6",
        children=[
            html.H2("Notifications", className="text-4xl font-extrabold text-gray-900 mb-8 font-inter"),
            html.Div(className="space-y-4", children=notifications_list)
        ]
    )

def admin_panel_layout(auth_token):
    # Fetch users and logs from backend
    users_data = fetch_data_from_backend('users/', auth_token)
    logs_data = fetch_data_from_backend('timelogs/', auth_token) # Admin can see all timelogs

    if "error" in users_data or "error" in logs_data:
        return html.Div(f"Error loading admin panel data: {users_data.get('error') or logs_data.get('error')}", className="text-red-500 p-4")

    users_table_rows = []
    for user in users_data['results']: # Assuming paginated results, access 'results' key
        users_table_rows.append(
            html.Tr(className="border-b border-gray-200 hover:bg-gray-50", children=[
                html.Td(user['username'], className="py-3 px-4"),
                html.Td(user['email'], className="py-3 px-4"),
                html.Td(
                    dcc.Dropdown(
                        id={'type': 'user-role-dropdown', 'index': user['id']},
                        options=[
                            {'label': 'Employee', 'value': 'employee'},
                            {'label': 'Team Head', 'value': 'team_head'},
                            {'label': 'Project Manager', 'value': 'project_manager'},
                            {'label': 'Admin', 'value': 'admin'}
                        ],
                        value=user['role'], # Use the 'role' field from the backend
                        clearable=False,
                        className="dash-dropdown",
                        style={'width': '150px'}
                    ),
                    className="py-3 px-4"
                ),
                html.Td(
                    html.Button(
                        "Delete",
                        id={'type': 'delete-user-button', 'index': user['id']},
                        n_clicks=0,
                        className="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded-md text-sm shadow-sm transition duration-300"
                    ),
                    className="py-3 px-4"
                )
            ])
        )

    logs_table_rows = []
    for log in logs_data['results']: # Assuming paginated results
        logs_table_rows.append(
            html.Tr(className="border-b border-gray-200 hover:bg-gray-50", children=[
                html.Td(log['id'], className="py-3 px-4"),
                html.Td(log['user_username'], className="py-3 px-4"),
                html.Td(log['start_time'].split('T')[0], className="py-3 px-4"), # Just date part
                html.Td(log['activity_description'], className="py-3 px-4"),
                html.Td(f"{round((datetime.fromisoformat(log['end_time'].replace('Z', '+00:00')) - datetime.fromisoformat(log['start_time'].replace('Z', '+00:00'))).total_seconds() / 3600, 2) if log['end_time'] else 'N/A'} hrs", className="py-3 px-4"),
                html.Td(log.get('app_name', 'N/A'), className="py-3 px-4"), # App name not directly in TimeLog
                html.Td(
                    html.Button(
                        "Edit",
                        id={'type': 'edit-log-button', 'index': log['id']},
                        n_clicks=0,
                        className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded-md text-sm shadow-sm transition duration-300"
                    ),
                    className="py-3 px-4"
                )
            ])
        )

    return html.Div(
        className="p-6 space-y-8",
        children=[
            html.H2("Admin Panel", className="text-4xl font-extrabold text-gray-900 mb-8 font-inter"),

            create_card(
                "Manage Users and Roles",
                html.Div(className="overflow-x-auto", children=[
                    html.Table(
                        className="min-w-full bg-white rounded-lg shadow-md",
                        children=[
                            html.Thead(className="bg-gray-200", children=[
                                html.Tr(children=[
                                    html.Th("Username", className="py-3 px-4 text-left text-sm font-semibold text-gray-700"),
                                    html.Th("Email", className="py-3 px-4 text-left text-sm font-semibold text-gray-700"),
                                    html.Th("Role", className="py-3 px-4 text-left text-sm font-semibold text-gray-700"),
                                    html.Th("Actions", className="py-3 px-4 text-left text-sm font-semibold text-gray-700")
                                ])
                            ]),
                            html.Tbody(id='admin-users-table-body', children=users_table_rows)
                        ]
                    )
                ])
            ),

            create_card(
                "View and Edit Collected Logs",
                html.Div(className="overflow-x-auto", children=[
                    html.Table(
                        className="min-w-full bg-white rounded-lg shadow-md",
                        children=[
                            html.Thead(className="bg-gray-200", children=[
                                html.Tr(children=[
                                    html.Th("Log ID", className="py-3 px-4 text-left text-sm font-semibold text-gray-700"),
                                    html.Th("User", className="py-3 px-4 text-left text-sm font-semibold text-gray-700"),
                                    html.Th("Date", className="py-3 px-4 text-left text-sm font-semibold text-gray-700"),
                                    html.Th("Activity", className="py-3 px-4 text-left text-sm font-semibold text-gray-700"),
                                    html.Th("Duration", className="py-3 px-4 text-left text-sm font-semibold text-gray-700"),
                                    html.Th("App Usage", className="py-3 px-4 text-left text-sm font-semibold text-gray-700"),
                                    html.Th("Actions", className="py-3 px-4 text-left text-sm font-semibold text-gray-700")
                                ])
                            ]),
                            html.Tbody(children=logs_table_rows)
                        ]
                    )
                ])
            ),

            create_card(
                "Update Configurations / Thresholds",
                html.Div(className="space-y-4", children=[
                    html.Div(children=[
                        html.Label("Low Activity Threshold (hours/day):", htmlFor="lowActivityThreshold", className="block text-gray-700 font-medium mb-1"),
                        dcc.Input(
                            type="number",
                            id="lowActivityThreshold",
                            value=4,
                            className="w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                        )
                    ]),
                    html.Div(children=[
                        html.Label("Productivity Drop Alert (%):", htmlFor="productivityDropPercentage", className="block text-gray-700 font-medium mb-1"),
                        dcc.Input(
                            type="number",
                            id="productivityDropPercentage",
                            value=15,
                            className="w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                        )
                    ]),
                    html.Button(
                        "Save Configurations",
                        id="save-configs-button",
                        n_clicks=0,
                        className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-md shadow-md transition duration-300"
                    )
                ])
            )
        ]
    )

# --- Login Layout ---
login_layout = html.Div(
    className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8 font-inter",
    children=[
        html.Div(
            className="max-w-md w-full space-y-8 p-10 bg-white rounded-xl shadow-lg z-10",
            children=[
                html.Div(children=[
                    html.H2("Sign in to your account", className="mt-6 text-center text-3xl font-extrabold text-gray-900"),
                ]),
                html.Div(className="mt-8 space-y-6", children=[
                    html.Div(className="rounded-md shadow-sm -space-y-px", children=[
                        html.Div(children=[
                            html.Label("Username", htmlFor="username", className="sr-only"),
                            dcc.Input(
                                type="text",
                                id="login-username",
                                name="username",
                                required=True,
                                placeholder="Username",
                                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                            )
                        ]),
                        html.Div(children=[
                            html.Label("Password", htmlFor="password", className="sr-only"),
                            dcc.Input(
                                type="password",
                                id="login-password",
                                name="password",
                                required=True,
                                placeholder="Password",
                                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                            )
                        ])
                    ]),
                    html.Div(children=[
                        html.Button(
                            "Sign in",
                            id="login-button",
                            n_clicks=0,
                            className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                        )
                    ]),
                    html.Div(id='login-status-message', className="text-center text-red-500 text-sm")
                ])
            ]
        )
    ]
)


# --- App Layout ---
app.layout = html.Div(
    className="min-h-screen bg-gray-50 font-inter",
    children=[
        # Inline CSS for Tailwind-like styling and font import
        html.Style('''
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
            body { font-family: 'Inter', sans-serif; margin: 0; }
            .font-inter { font-family: 'Inter', sans-serif; }
            /* Basic Tailwind-like classes for Dash components */
            .bg-gradient-to-r { background-image: linear-gradient(to right, var(--tw-gradient-stops)); }
            .from-blue-600 { --tw-gradient-from: #2563eb; --tw-gradient-stops: var(--tw-gradient-from), var(--tw-gradient-to, rgba(37, 99, 235, 0)); }
            .to-indigo-700 { --tw-gradient-to: #4338ca; }
            .text-white { color: #fff; }
            .p-4 { padding: 1rem; }
            .shadow-lg { box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05); }
            .rounded-b-lg { border-bottom-left-radius: 0.5rem; border-bottom-right-radius: 0.5rem; }
            .flex { display: flex; }
            .justify-between { justify-content: space-between; }
            .items-center { align-items: center; }
            .text-3xl { font-size: 1.875rem; line-height: 2.25rem; }
            .font-bold { font-weight: 700; }
            .relative { position: relative; }
            .space-x-2 > *:not([hidden]) ~ *:not([hidden]) { margin-left: 0.5rem; }
            .bg-blue-700 { background-color: #1d4ed8; }
            .hover\\:bg-blue-800:hover { background-color: #1e40af; }
            .px-4 { padding-left: 1rem; padding-right: 1rem; }
            .py-2 { padding-top: 0.5rem; padding-bottom: 0.5rem; }
            .rounded-full { border-radius: 9999px; }
            .transition { transition-property: all; transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1); transition-duration: 150ms; }
            .duration-300 { transition-duration: 300ms; }
            .ease-in-out { transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1); }
            .shadow-md { box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); }
            .w-5 { width: 1.25rem; }
            .h-5 { height: 1.25rem; }
            .font-semibold { font-weight: 600; }
            .capitalize { text-transform: capitalize; }
            .w-4 { width: 1rem; }
            .h-4 { height: 1rem; }
            .rotate-180 { transform: rotate(180deg); }
            .mt-2 { margin-top: 0.5rem; }
            .w-48 { width: 12rem; }
            .bg-white { background-color: #fff; }
            .rounded-lg { border-radius: 0.5rem; }
            .shadow-xl { box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04); }
            .py-1 { padding-top: 0.25rem; padding-bottom: 0.25rem; }
            .z-10 { z-index: 10; }
            .block { display: block; }
            .w-full { width: 100%; }
            .text-left { text-align: left; }
            .text-gray-800 { color: #1f2937; }
            .hover\\:bg-gray-100:hover { background-color: #f3f4f6; }
            .my-1 { margin-top: 0.25rem; margin-bottom: 0.25rem; }
            .text-red-600 { color: #dc2626; }
            .hover\\:bg-red-50:hover { background-color: #fef2f2; }
            .mr-2 { margin-right: 0.5rem; }
            .min-h-screen { min-height: 100vh; }
            .bg-gray-50 { background-color: #f9fafb; }
            .w-64 { width: 16rem; }
            .bg-gray-800 { background-color: #1f2937; }
            .text-white { color: #fff; }
            .p-4 { padding: 1rem; }
            .rounded-r-lg { border-top-right-radius: 0.5rem; border-bottom-right-radius: 0.5rem; }
            .mt-8 { margin-top: 2rem; }
            .mb-2 { margin-bottom: 0.5rem; }
            .bg-blue-600 { background-color: #2563eb; }
            .hover\\:bg-gray-700:hover { background-color: #374151; }
            .ml-3 { margin-left: 0.75rem; }
            .text-lg { font-size: 1.125rem; line-height: 1.75rem; }
            .font-medium { font-weight: 500; }
            .flex-col { flex-direction: column; }
            .lg\\:flex-row { /* Responsive for large screens */ }
            .flex-1 { flex: 1 1 0%; }
            .p-6 { padding: 1.5rem; }
            .lg\\:p-8 { /* Responsive for large screens */ }
            .overflow-y-auto { overflow-y: auto; }
            .max-h-\\[calc\\(100vh-80px\\)\\] { max-height: calc(100vh - 80px); } /* Adjust based on header height */
            .space-y-8 > *:not([hidden]) ~ *:not([hidden]) { margin-top: 2rem; }
            .text-4xl { font-size: 2.25rem; line-height: 2.5rem; }
            .font-extrabold { font-weight: 800; }
            .text-gray-900 { color: #111827; }
            .mb-8 { margin-bottom: 2rem; }
            .grid { display: grid; }
            .grid-cols-1 { grid-template-columns: repeat(1, minmax(0, 1fr)); }
            .lg\\:grid-cols-2 { /* Responsive for large screens */ }
            .gap-8 { gap: 2rem; }
            .border { border-width: 1px; }
            .border-gray-200 { border-color: #e5e7eb; }
            .text-gray-800 { color: #1f2937; }
            .mb-4 { margin-bottom: 1rem; }
            .bg-gray-100 { background-color: #f3f4f6; }
            .gap-4 { gap: 1rem; }
            .text-gray-600 { color: #4b5563; }
            .p-2 { padding: 0.5rem; }
            .border-gray-300 { border-color: #d1d5db; }
            .shadow-sm { box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05); }
            .focus\\:ring-blue-500:focus { --tw-ring-color: #3b82f6; }
            .focus\\:border-blue-500:focus { border-color: #3b82f6; }
            .ml-auto { margin-left: auto; }
            .bg-blue-500 { background-color: #3b82f6; }
            .hover\\:bg-blue-600:hover { background-color: #2563eb; }
            .space-x-2 > *:not([hidden]) ~ *:not([hidden]) { margin-left: 0.5rem; }
            .list-disc { list-style-type: disc; }
            .list-inside { list-style-position: inside; }
            .text-gray-700 { color: #374151; }
            .text-red-600 { color: #dc2626; }
            .text-orange-600 { color: #ea580c; }
            .text-green-600 { color: #16a34a; }
            .text-blue-600 { color: #2563eb; }
            .overflow-x-auto { overflow-x: auto; }
            .min-w-full { min-width: 100%; }
            .bg-gray-200 { background-color: #e5e7eb; }
            .py-3 { padding-top: 0.75rem; padding-bottom: 0.75rem; }
            .text-sm { font-size: 0.875rem; line-height: 1.25rem; }
            .border-b { border-bottom-width: 1px; }
            .hover\\:bg-gray-50:hover { background-color: #f9fafb; }
            .px-3 { padding-left: 0.75rem; padding-right: 0.75rem; }
            .py-1 { padding-top: 0.25rem; padding-bottom: 0.25rem; }
            .text-xs { font-size: 0.75rem; line-height: 1rem; }
            .bg-green-500 { background-color: #22c55e; }
            .hover\\:bg-green-600:hover { background-color: #16a34a; }
            .lucide { display: inline-block; vertical-align: middle; } /* Basic style for lucide icons */

            /* Specific styles for dropdowns to override Dash defaults */
            .dash-dropdown .Select-control {
                border-radius: 0.375rem; /* rounded-md */
                border: 1px solid #d1d5db; /* border-gray-300 */
                box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05); /* shadow-sm */
                border: none !important; /* Override default Dash border */
                box-shadow: none !important; /* Override default Dash shadow */
            }
            .dash-dropdown .Select-value-label {
                color: #1f2937 !important; /* text-gray-800 */
            }
            .dash-dropdown .Select-menu-outer {
                border-radius: 0.375rem; /* rounded-md */
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); /* shadow-md */
            }
            .dash-dropdown .Select-option.is-focused {
                background-color: #e0e7ff !important; /* light blue for focus */
            }
            .dash-dropdown .Select-option.is-selected {
                background-color: #bfdbfe !important; /* blue-200 for selected */
                color: #1f2937 !important;
            }
        '''),
        # Hidden div to store authentication token and user role
        dcc.Store(id='auth-token-store', data=None), # Stores the authentication token
        dcc.Store(id='user-role-store', data='employee'), # Stores the current user's role
        dcc.Store(id='current-view-store', data='dashboard'), # Stores the current dashboard view

        # Main content container, conditionally rendered
        html.Div(id='app-container', children=login_layout) # Initially show login layout
    ]
)

# --- Callbacks ---

# Callback for Login
@app.callback(
    Output('auth-token-store', 'data'),
    Output('user-role-store', 'data'),
    Output('login-status-message', 'children'),
    Input('login-button', 'n_clicks'),
    State('login-username', 'value'),
    State('login-password', 'value')
)
def authenticate_user(n_clicks, username, password):
    if n_clicks > 0:
        if not username or not password:
            return dash.no_update, dash.no_update, "Please enter both username and password."

        try:
            # Make a POST request to your Django login endpoint
            response = requests.post(f"{API_BASE_URL}token/", json={"username": username, "password": password})
            response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
            
            token_data = response.json()
            access_token = token_data.get("token")
            user_role = token_data.get("role", "employee") # Default to employee if role not provided

            if access_token:
                return access_token, user_role, "" # Return token, role, and clear status message
            else:
                return None, "employee", "Login failed: No token received."

        except requests.exceptions.HTTPError as http_err:
            error_message = f"Login failed: {http_err.response.status_code}"
            try:
                error_details = http_err.response.json()
                if error_details:
                    error_message += f" - {error_details.get('detail') or error_details}"
            except json.JSONDecodeError:
                error_message += f" - {http_err.response.text}"
            print(f"Login HTTP error: {error_message}")
            return None, "employee", error_message
        except requests.exceptions.RequestException as req_err:
            print(f"Login connection error: {req_err}")
            return None, "employee", "Login failed: Could not connect to the server."
    return dash.no_update, dash.no_update, ""

# Callback to render main app or login based on auth token
@app.callback(
    Output('app-container', 'children'),
    Output('current-role-display', 'children'), # Update current role display in header
    Output('nav-dashboard', 'className'),
    Output('nav-notifications', 'className'),
    Output('nav-admin-panel', 'className'),
    Output('nav-admin-li', 'className'),
    Input('auth-token-store', 'data'),
    Input('user-role-store', 'data'), # Listen to user role changes
    Input('current-view-store', 'data'),
    Input({'type': 'role-select-button', 'role': dash.ALL}, 'n_clicks'), # For role switching
    Input('logout-button', 'n_clicks'),
    Input('nav-dashboard', 'n_clicks'),
    Input('nav-notifications', 'n_clicks'),
    Input('nav-admin-panel', 'n_clicks'),
    State('current-role-display', 'children'), # Current display name
    State('current-role-store', 'data'), # Current stored role
    prevent_initial_call=False # Allow initial load to show login
)
def render_app_or_login_and_update_nav(auth_token, user_role_from_store, current_view_from_store,
                                       role_button_clicks, logout_clicks, dashboard_clicks,
                                       notifications_clicks, admin_panel_clicks,
                                       current_role_display_name, current_role_stored):
    ctx = callback_context

    # Determine the effective role and view
    effective_role = user_role_from_store
    effective_view = current_view_from_store

    if ctx.triggered:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if 'role-select-button' in button_id:
            effective_role = eval(button_id)['role']
            # When role changes, default view to dashboard or admin_panel for admin
            effective_view = 'admin_panel' if effective_role == 'admin' else 'dashboard'
        elif button_id == 'logout-button':
            effective_role = 'employee' # Reset role on logout
            effective_view = 'dashboard'
            # auth_token will be set to None by the logout callback
        elif button_id == 'nav-dashboard':
            effective_view = 'dashboard'
        elif button_id == 'nav-notifications':
            effective_view = 'notifications'
        elif button_id == 'nav-admin-panel':
            effective_view = 'admin_panel'

    # Update sidebar button active states
    dashboard_class = "flex items-center w-full px-4 py-2 rounded-md transition duration-200 ease-in-out hover:bg-gray-700"
    notifications_class = "flex items-center w-full px-4 py-2 rounded-md transition duration-200 ease-in-out hover:bg-gray-700"
    admin_panel_class = "flex items-center w-full px-4 py-2 rounded-md transition duration-200 ease-in-out hover:bg-gray-700"
    admin_li_class = "mb-2 hidden" # Hidden by default

    if effective_view == 'dashboard':
        dashboard_class += " bg-blue-600 shadow-md"
    elif effective_view == 'notifications':
        notifications_class += " bg-blue-600 shadow-md"
    elif effective_view == 'admin_panel':
        admin_panel_class += " bg-blue-600 shadow-md"

    if effective_role == 'admin':
        admin_li_class = "mb-2" # Show admin panel nav item

    # Determine the display name for the header
    display_name_map = {
        'employee': 'Employee',
        'team_head': 'Team Head',
        'project_manager': 'Project Manager',
        'admin': 'Admin'
    }
    display_role_name = display_name_map.get(effective_role, 'Employee')


    if auth_token: # If authenticated, show main app layout
        app_layout_content = html.Div(
            className="min-h-screen bg-gray-50 font-inter",
            children=[
                html.Header(
                    className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white p-4 shadow-lg flex justify-between items-center rounded-b-lg",
                    children=[
                        html.H1("Productivity Tracker", className="text-3xl font-bold font-inter"),
                        html.Div(
                            className="relative",
                            children=[
                                html.Button(
                                    id='role-dropdown-button',
                                    n_clicks=0,
                                    className="flex items-center space-x-2 bg-blue-700 hover:bg-blue-800 px-4 py-2 rounded-full transition duration-300 ease-in-out shadow-md",
                                    children=[
                                        html.I(className="lucide lucide-user w-5 h-5"),
                                        html.Span(id='current-role-display', children=display_role_name, className="font-semibold capitalize"),
                                        html.I(id='role-dropdown-icon', className="lucide lucide-chevron-down w-4 h-4 transition-transform")
                                    ]
                                ),
                                html.Div(
                                    id='role-dropdown-content',
                                    className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-xl py-1 z-10 hidden",
                                    children=[
                                        html.Button("Employee", id={'type': 'role-select-button', 'role': 'employee'}, n_clicks=0, className="block w-full text-left px-4 py-2 text-gray-800 hover:bg-gray-100"),
                                        html.Button("Team Head", id={'type': 'role-select-button', 'role': 'team_head'}, n_clicks=0, className="block w-full text-left px-4 py-2 text-gray-800 hover:bg-gray-100"),
                                        html.Button("Project Manager", id={'type': 'role-select-button', 'role': 'project_manager'}, n_clicks=0, className="block w-full text-left px-4 py-2 text-gray-800 hover:bg-gray-100"),
                                        html.Hr(className="my-1"),
                                        html.Button("Admin", id={'type': 'role-select-button', 'role': 'admin'}, n_clicks=0, className="block w-full text-left px-4 py-2 text-gray-800 hover:bg-gray-100"),
                                        html.Hr(className="my-1"),
                                        html.Button(
                                            [
                                                html.I(className="lucide lucide-log-out inline-block w-4 h-4 mr-2"),
                                                "Logout"
                                            ],
                                            id='logout-button', n_clicks=0, className="block w-full text-left px-4 py-2 text-red-600 hover:bg-red-50"
                                        )
                                    ]
                                )
                            ]
                        )
                    ]
                ),
                html.Div(
                    className="flex flex-col lg:flex-row",
                    children=[
                        html.Aside(
                            className="w-64 bg-gray-800 text-white p-4 rounded-r-lg shadow-lg",
                            children=[
                                html.Nav(
                                    className="mt-8",
                                    children=[
                                        html.Ul(
                                            children=[
                                                html.Li(className="mb-2", children=html.Button(
                                                    [html.I(className="lucide lucide-calendar-days w-5 h-5"), html.Span("Dashboard", className="ml-3 text-lg font-medium")],
                                                    id='nav-dashboard', n_clicks=0,
                                                    className=dashboard_class
                                                )),
                                                html.Li(className="mb-2", children=html.Button(
                                                    [html.I(className="lucide lucide-bell w-5 h-5"), html.Span("Notifications", className="ml-3 text-lg font-medium")],
                                                    id='nav-notifications', n_clicks=0,
                                                    className=notifications_class
                                                )),
                                                html.Li(id='nav-admin-li', className=admin_li_class, children=html.Button(
                                                    [html.I(className="lucide lucide-settings w-5 h-5"), html.Span("Admin Panel", className="ml-3 text-lg font-medium")],
                                                    id='nav-admin-panel', n_clicks=0,
                                                    className=admin_panel_class
                                                ))
                                            ]
                                        )
                                    ]
                                )
                            ]
                        ),
                        html.Main(
                            id='page-content',
                            className="flex-1 p-4 lg:p-8 overflow-y-auto max-h-[calc(100vh-80px)]"
                        )
                    ]
                ),
            ]
        )
        return app_layout_content, display_role_name, dashboard_class, notifications_class, admin_panel_class, admin_li_class, effective_role
    else: # If not authenticated, show login screen
        return login_layout, "Guest", dashboard_class, notifications_class, admin_panel_class, admin_li_class, "employee" # Reset role to default on logout


# Callback to toggle role dropdown
@app.callback(
    Output('role-dropdown-content', 'className', allow_duplicate=True),
    Output('role-dropdown-icon', 'className', allow_duplicate=True),
    Input('role-dropdown-button', 'n_clicks'),
    State('role-dropdown-content', 'className'),
    prevent_initial_call=True
)
def toggle_role_dropdown(n_clicks, current_class):
    if n_clicks:
        if 'hidden' in current_class:
            return current_class.replace(' hidden', ''), 'lucide lucide-chevron-down w-4 h-4 transition-transform rotate-180'
        else:
            return current_class + ' hidden', 'lucide lucide-chevron-down w-4 h-4 transition-transform'
    return current_class, 'lucide lucide-chevron-down w-4 h-4 transition-transform'

# Callback for Logout
@app.callback(
    Output('auth-token-store', 'data', allow_duplicate=True),
    Output('user-role-store', 'data', allow_duplicate=True),
    Output('login-status-message', 'children', allow_duplicate=True),
    Input('logout-button', 'n_clicks'),
    prevent_initial_call=True
)
def logout_user(n_clicks):
    if n_clicks > 0:
        # In a real app, you might also hit a logout endpoint on Django
        return None, 'employee', "You have been logged out."
    return dash.no_update, dash.no_update, dash.no_update

# Callback to render page content based on role and view
@app.callback(
    Output('page-content', 'children'),
    Input('user-role-store', 'data'),
    Input('current-view-store', 'data'),
    State('auth-token-store', 'data') # Pass auth token to layout functions
)
def render_page_content(role, view, auth_token):
    if not auth_token: # If not logged in, return empty content (handled by app-container callback)
        return html.Div("Please log in to view content.")

    if view == 'notifications':
        return notifications_panel_layout(auth_token)
    elif view == 'admin_panel' and role == 'admin':
        return admin_panel_layout(auth_token)
    elif role == 'employee':
        return employee_dashboard_layout(auth_token)
    elif role == 'team_head':
        return team_head_dashboard_layout(auth_token)
    elif role == 'project_manager':
        return project_manager_dashboard_layout(auth_token)
    else:
        # Fallback for unknown roles or if admin is not viewing admin panel explicitly
        return employee_dashboard_layout(auth_token)

# Callback for admin panel user management
@app.callback(
    Output('admin-users-table-body', 'children'),
    Input({'type': 'user-role-dropdown', 'index': dash.ALL}, 'value'),
    Input({'type': 'delete-user-button', 'index': dash.ALL}, 'n_clicks'),
    State('auth-token-store', 'data'), # Pass token for conceptual API call
    prevent_initial_call=True
)
def update_admin_users_table(role_values, delete_clicks, auth_token):
    if not auth_token:
        return html.Tr(html.Td("Please log in as an administrator.", colSpan=4))

    ctx = callback_context

    if not ctx.triggered:
        # Initial load or no relevant trigger, fetch and render
        users_data = fetch_data_from_backend('users/', auth_token)
        if "error" in users_data:
            return html.Tr(html.Td(f"Error loading users: {users_data['error']}", colSpan=4, className="text-red-500"))
        users = users_data.get('results', [])
        
        # Re-render the table with fetched data
        new_users_table_rows = []
        for user in users:
            new_users_table_rows.append(
                html.Tr(className="border-b border-gray-200 hover:bg-gray-50", children=[
                    html.Td(user['username'], className="py-3 px-4"),
                    html.Td(user['email'], className="py-3 px-4"),
                    html.Td(
                        dcc.Dropdown(
                            id={'type': 'user-role-dropdown', 'index': user['id']},
                            options=[
                                {'label': 'Employee', 'value': 'employee'},
                                {'label': 'Team Head', 'value': 'team_head'},
                                {'label': 'Project Manager', 'value': 'project_manager'},
                                {'label': 'Admin', 'value': 'admin'}
                            ],
                            value=user['role'],
                            clearable=False,
                            className="dash-dropdown",
                            style={'width': '150px'}
                        ),
                        className="py-3 px-4"
                    ),
                    html.Td(
                        html.Button(
                            "Delete",
                            id={'type': 'delete-user-button', 'index': user['id']},
                            n_clicks=0,
                            className="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded-md text-sm shadow-sm transition duration-300"
                        ),
                        className="py-3 px-4"
                    )
                ])
            )
        return new_users_table_rows

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if 'delete-user-button' in triggered_id:
        deleted_user_id = eval(triggered_id)['index']
        response = fetch_data_from_backend(f'users/{deleted_user_id}/', auth_token, method='DELETE')
        if "error" in response:
            print(f"Failed to delete user {deleted_user_id}: {response['error']}")
            # Re-fetch data to reflect actual state if deletion failed
        else:
            print(f"User {deleted_user_id} deleted successfully.")
        
        # After action, re-fetch the updated list of users
        users_data = fetch_data_from_backend('users/', auth_token)
        if "error" in users_data:
            return html.Tr(html.Td(f"Error re-loading users after delete: {users_data['error']}", colSpan=4, className="text-red-500"))
        users = users_data.get('results', [])

    elif 'user-role-dropdown' in triggered_id:
        dropdown_id = eval(triggered_id)['index']
        new_role = ctx.triggered[0]['value']
        
        # Call the custom set_role action on the backend
        response = fetch_data_from_backend(f'users/{dropdown_id}/set_role/', auth_token, method='POST', data={'role': new_role})
        if "error" in response:
            print(f"Failed to update role for user {dropdown_id}: {response['error']}")
            # Re-fetch data to reflect actual state if update failed
        else:
            print(f"User {dropdown_id} role updated to {new_role}.")
        
        # After action, re-fetch the updated list of users
        users_data = fetch_data_from_backend('users/', auth_token)
        if "error" in users_data:
            return html.Tr(html.Td(f"Error re-loading users after role update: {users_data['error']}", colSpan=4, className="text-red-500"))
        users = users_data.get('results', [])
    else:
        users_data = fetch_data_from_backend('users/', auth_token)
        if "error" in users_data:
            return html.Tr(html.Td(f"Error re-loading users: {users_data['error']}", colSpan=4, className="text-red-500"))
        users = users_data.get('results', [])

    # Re-render the table with updated data
    new_users_table_rows = []
    for user in users:
        new_users_table_rows.append(
            html.Tr(className="border-b border-gray-200 hover:bg-gray-50", children=[
                html.Td(user['username'], className="py-3 px-4"),
                html.Td(user['email'], className="py-3 px-4"),
                html.Td(
                    dcc.Dropdown(
                        id={'type': 'user-role-dropdown', 'index': user['id']},
                        options=[
                            {'label': 'Employee', 'value': 'employee'},
                            {'label': 'Team Head', 'value': 'team_head'},
                            {'label': 'Project Manager', 'value': 'project_manager'},
                            {'label': 'Admin', 'value': 'admin'}
                        ],
                        value=user['role'],
                        clearable=False,
                        className="dash-dropdown",
                        style={'width': '150px'}
                    ),
                    className="py-3 px-4"
                ),
                html.Td(
                    html.Button(
                        "Delete",
                        id={'type': 'delete-user-button', 'index': user['id']},
                        n_clicks=0,
                        className="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded-md text-sm shadow-sm transition duration-300"
                    ),
                    className="py-3 px-4"
                )
            ])
        )
    return new_users_table_rows


@app.callback(
    Output('dummy-output-log-edit', 'children'), # A dummy output to trigger the callback
    Input({'type': 'edit-log-button', 'index': dash.ALL}, 'n_clicks'),
    State('auth-token-store', 'data'), # Pass token for conceptual API call
    prevent_initial_call=True
)
def simulate_edit_log(n_clicks, auth_token):
    if not auth_token:
        return html.Div("Not authenticated.", style={'display': 'none'})

    ctx = callback_context
    if not ctx.triggered:
        return dash.no_update
    
    button_id = eval(ctx.triggered[0]['prop_id'].split('.')[0])
    log_id = button_id['index']
    
    # --- Simulate API Call to Django Backend for Log Edit ---
    # In a real scenario, you'd likely open a modal to get new data for the log
    # For this example, we'll just simulate a PATCH with dummy data
    dummy_update_data = {"activity_description": f"Updated activity for log {log_id}"}
    response = fetch_data_from_backend(f'timelogs/{log_id}/', auth_token, method='PATCH', data=dummy_update_data)
    
    if "error" in response:
        print(f"Failed to update log {log_id}: {response['error']}")
        return html.Div(f"Failed to update log {log_id}: {response['error']}", style={'display': 'none'})
    else:
        print(f"Log {log_id} updated successfully via API.")
        return html.Div(f"Log ID: {log_id} updated.", style={'display': 'none'})


@app.callback(
    Output('dummy-output-save-configs', 'children'), # A dummy output
    Input('save-configs-button', 'n_clicks'),
    State('lowActivityThreshold', 'value'),
    State('productivityDropPercentage', 'value'),
    State('auth-token-store', 'data'), # Pass token for conceptual API call
    prevent_initial_call=True
)
def save_configurations(n_clicks, low_activity, productivity_drop, auth_token):
    if not auth_token:
        return html.Div("Not authenticated.", style={'display': 'none'})

    if n_clicks > 0:
        # --- Simulate API Call to Django Backend for Config Update ---
        # You would need a Django model/view for configurations
        config_data = {"low_activity_threshold": low_activity, "productivity_drop_percentage": productivity_drop}
        # Example endpoint: 'configs/update/' or 'settings/1/' (if single config object)
        # response = fetch_data_from_backend('configs/', auth_token, method='POST', data=config_data)
        
        # For now, just print and simulate success
        print(f"Simulating saving configurations with token: {auth_token}")
        print(f"Low Activity Threshold: {low_activity} hours/day")
        print(f"Productivity Drop Alert: {productivity_drop}%")
        # if "error" in response:
        #     print(f"Error saving configurations: {response['error']}")
        #     return html.Div(f"Failed to save configurations: {response['error']}", style={'display': 'none'})
        # else:
        #     print("Configurations saved successfully via API.")
        return html.Div("Configurations saved!", style={'display': 'none'})
    return dash.no_update


@app.callback(
    Output('dummy-output-export', 'children'), # A dummy output
    Input('export-report-button', 'n_clicks'),
    State('filter-date-range', 'value'),
    State('filter-team', 'value'),
    State('filter-project', 'value'),
    State('user-role-store', 'data'), # Use user-role-store for role
    State('auth-token-store', 'data'), # Pass token for conceptual API call
    prevent_initial_call=True
)
def export_report(n_clicks, date_range, team, project, role, auth_token):
    if not auth_token:
        return html.Div("Not authenticated.", style={'display': 'none'})

    if n_clicks > 0:
        # --- Simulate API Call to Django Backend for Report Export ---
        # This would typically trigger a file download from the backend
        params = {"date_range": date_range, "team": team, "project": project, "role": role}
        # response = fetch_data_from_backend('reports/export/', auth_token, params=params, method='GET')
        
        # For now, just print and simulate success
        print(f"Simulating report export for role: {role} with token: {auth_token}")
        print(f"Filters: Date Range={date_range}, Team={team}, Project={project}")
        # if "error" in response:
        #     print(f"Error exporting report: {response['error']}")
        #     return html.Div(f"Failed to export report: {response['error']}", style={'display': 'none'})
        # else:
        #     print("Report export initiated via API.")
        return html.Div("Report export initiated!", style={'display': 'none'})
    return dash.no_update

# Add dummy divs for the callbacks that don't directly update the UI
app.layout.children[-1].children.append(html.Div(id='dummy-output-log-edit', style={'display': 'none'}))
app.layout.children[-1].children.append(html.Div(id='dummy-output-save-configs', style={'display': 'none'}))
app.layout.children[-1].children.append(html.Div(id='dummy-output-export', style={'display': 'none'}))


if __name__ == '__main__':
    app.run_server(debug=True)