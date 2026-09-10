# INTELLICONZ Support Hub

INTELLICONZ Support Hub is an internal support ticket management system developed as an internship assessment project.

The system allows employees to create and track support tickets while support staff can assign, resolve, and close tickets.

## Technologies Used

- Python
- Flask
- SQLite
- HTML
- CSS
- JavaScript

## Main Features

### Employee

- Login with an Employee account
- Create support tickets
- View their own tickets
- Search and filter tickets
- View ticket history
- Reopen resolved tickets with a reason
- View dashboard ticket statistics

### Support

- Login with a Support account
- View support tickets
- Search and filter tickets
- Assign tickets
- Resolve tickets with a resolution note
- Close resolved tickets
- View complete ticket history
- View dashboard ticket statistics

## Ticket Workflow

Tickets follow this workflow:

```text
Open → In Progress → Resolved → Closed
```

When a ticket is created, it starts as **Open** and **Unassigned**.

When Support assigns the ticket, it changes to **In Progress**.

Support can resolve an In Progress ticket by providing a resolution note.

An Employee can reopen their resolved ticket if the problem continues. The ticket returns to **Open** and becomes **Unassigned**.

Support can close a resolved ticket.

Closed tickets are read-only.

## Test Accounts

### Employee

```text
Username: employee1
Password: pass123
```

```text
Username: employee2
Password: pass123
```

### Support

```text
Username: support1
Password: pass123
```

```text
Username: support2
Password: pass123
```

## How to Run the Project

### 1. Open the Project

Open the `support-ticket-system` folder in VS Code.

### 2. Install Flask

If Flask is not already installed, run:

```powershell
& "C:\Users\alnaj\AppData\Local\Programs\Python\Python313\python.exe" -m pip install flask
```

### 3. Start the Server

Open the VS Code terminal inside the project folder and run:

```powershell
& "C:\Users\alnaj\AppData\Local\Programs\Python\Python313\python.exe" app.py
```

Keep the VS Code terminal running while using the website.

To stop the server, press:

```text
Ctrl + C
```

## Database

The application uses SQLite for persistent storage.

The database file is:

```text
tickets.db
```

It stores:

- Users
- Tickets
- Ticket history

The information remains stored after the application is restarted.

## API

The project includes the following API endpoints:

```text
GET  /api/tickets
GET  /api/tickets/<ticket_id>
POST /api/tickets
POST /api/tickets/<ticket_id>/assign
POST /api/tickets/<ticket_id>/resolve
POST /api/tickets/<ticket_id>/reopen
POST /api/tickets/<ticket_id>/close
```

The API follows the same authentication, role permissions, and ticket workflow rules as the website.

## Authorization and Validation

The application uses two roles: **Employee** and **Support**.

Employees can create tickets, view their own tickets, and reopen their own resolved tickets.

Support users can view support tickets and assign, resolve, and close tickets according to the ticket's current status.

The application validates required information such as ticket titles and descriptions.

Whitespace-only titles and descriptions are rejected.

Invalid ticket status changes are rejected.

Closed tickets cannot be modified.

## Ticket History

The system automatically records important ticket actions:

- Created
- Assigned
- Resolved
- Reopened
- Closed

History records include the action, user, timestamp, and relevant information such as resolution notes and reopen reasons.

This allows the progress of each ticket to be tracked from creation to completion.

## Challenges and Learning

One of the main challenges was building the ticket workflow while making sure Employees and Support users could only perform actions allowed for their roles.

Another challenge was keeping ticket statuses, assignments, timestamps, resolution notes, reopen reasons, and ticket history consistent.

During this project, I gained experience with:

- Python
- Flask
- SQLite
- SQL
- HTML
- CSS
- JavaScript
- Authentication
- User sessions
- Role-based permissions
- APIs
- Database persistence
- Debugging
- Testing

## Research and Resources

In addition to AI assistance, I researched the technologies and concepts used in this project through official documentation and online development resources.

The following resources relate directly to concepts and code used in this project.

### Flask Routes, Requests, Templates, and Sessions

Flask Quickstart:

https://flask.palletsprojects.com/en/stable/quickstart/

Used to research Flask routes, GET and POST requests, templates, redirects, login sessions, and application structure.

### Flask Application Tutorial

Flask Tutorial:

https://flask.palletsprojects.com/en/stable/tutorial/

Used to research how a Flask web application can be structured, including authentication, databases, templates, and static files.

### Python and SQLite Database Code

Python sqlite3 Documentation:

https://docs.python.org/3/library/sqlite3.html

Used to research SQLite database connections, executing SQL queries, retrieving database rows, and working with SQLite from Python.

### HTML Forms

MDN HTML Forms:

https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Forms

Used to research forms, input fields, buttons, form submission, and validation used in the login and ticket forms.

### CSS Styling

MDN CSS:

https://developer.mozilla.org/en-US/docs/Web/CSS

Used to research CSS styling, layouts, backgrounds, borders, spacing, fonts, and other design features used in the INTELLICONZ interface.

### JavaScript

MDN JavaScript Guide:

https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide

Used to research JavaScript syntax and frontend functionality.

### SQLite and SQL

SQLite SQL Documentation:

https://www.sqlite.org/lang.html

Used to research SQL statements and SQLite database syntax used for storing, searching, filtering, and updating ticket information.

These resources were used to understand the concepts and syntax needed for the project. I also tested and modified the application throughout development to meet the requirements of the INTELLICONZ Support Ticket System.

## AI Use Disclosure

AI tools, including ChatGPT, Claude and Hermes were used as development assistance during this project.

AI assistance was used for:

- Explaining programming concepts
- Helping understand Python, Flask, SQLite, and SQL
- Debugging errors during development
- Reviewing and improving code
- Assisting with HTML and CSS
- Explaining API development and testing
- Assisting with project documentation

AI was not the only resource used during development. I also performed research using official documentation and online development resources to better understand the technologies and concepts used in the project.

Throughout development, I tested the application and reviewed its functionality to understand how the major parts of the system work and to make changes when necessary.

## Developer

Khalid Alnaji

Developed for INTELLICONZ.