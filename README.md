# INTELLICONZ Support Hub

INTELLICONZ Support Hub is an internal support ticket management system developed as an internship assessment project.

The system allows employees to create and track support tickets while support staff can assign, manage, comment on, and resolve tickets.

## Technologies Used

- Python
- Flask
- SQLite
- SQL
- HTML
- CSS
- JavaScript
- Git
- GitHub

## Main Features

### Employee

- Login with an Employee account
- Create support tickets
- View only their own tickets
- Search and filter tickets
- View ticket comments
- Add comments to their own non-Closed tickets
- View ticket history
- Reopen their own Resolved tickets with a required reason
- Close their own Resolved tickets
- View dashboard ticket statistics

### Support

- Login with a Support account
- View all support tickets
- Search and filter tickets
- Assign tickets to any Support user
- Reassign non-Closed tickets to another Support user
- Start work on assigned Open tickets
- Resolve In Progress tickets with a required resolution note
- Add comments to any non-Closed ticket
- View complete ticket history
- View dashboard ticket statistics
- Perform allowed Support actions even if another Support user is assigned to the ticket

## Ticket Workflow

Tickets follow this workflow:

```text
Open → In Progress → Resolved → Closed
                         ↓
                    Reopen
                         ↓
                    In Progress
```

When a ticket is created, it starts as **Open** and **Unassigned**.

Support can assign the ticket to any Support user. Assigning the ticket does **not** automatically change its status.

After the ticket has been assigned, Support can use **Start Work** to change the ticket from **Open** to **In Progress**.

Support can reassign any non-Closed ticket to another Support user.

Any Support user can perform allowed Support actions. The action is not restricted only to the currently assigned Support user.

Support can resolve an **In Progress** ticket by providing a required resolution note.

An Employee can reopen their own **Resolved** ticket if the problem continues. A reopen reason is required.

When reopened, the ticket returns to **In Progress** and keeps its assigned Support user.

The previous resolution information remains available in the ticket history.

Only the Employee who created the ticket can close their own **Resolved** ticket.

Closed tickets are read-only and cannot receive new comments or workflow changes.

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

### 2. Install Dependencies

The project includes a `requirements.txt` file.

Run:

```powershell
& "C:\Users\alnaj\AppData\Local\Programs\Python\Python313\python.exe" -m pip install -r requirements.txt
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
- Ticket assignments
- Comments
- Resolution notes
- Reopen reasons
- Ticket history

The information remains stored after the application is restarted.

The application creates the required database tables and test accounts when needed.

## Search and Filters

Tickets can be searched and filtered using:

- Search
- Status
- Category
- Priority
- Assigned Support
- Unassigned

Search and multiple filters can be used together.

The ticket page also displays summary counts for:

- Total
- Open
- In Progress
- Resolved
- Closed

## Comments

Employees can add comments to their own non-Closed tickets.

Support users can add comments to any non-Closed ticket.

Comments are displayed from oldest to newest.

Closed tickets cannot receive new comments.

## API

The project includes the following API endpoints:

```text
POST /api/login

GET  /api/tickets
POST /api/tickets
GET  /api/tickets/<ticket_id>

POST /api/tickets/<ticket_id>/assign
POST /api/tickets/<ticket_id>/start
POST /api/tickets/<ticket_id>/resolve
POST /api/tickets/<ticket_id>/reopen
POST /api/tickets/<ticket_id>/close

GET  /api/tickets/<ticket_id>/comments
POST /api/tickets/<ticket_id>/comments

GET  /api/tickets/<ticket_id>/history
GET  /api/summary
```

The API follows the same authentication, role permissions, visibility rules, validation, and ticket workflow rules as the website.

## Authorization and Validation

The application uses two roles: **Employee** and **Support**.

Employees can create tickets and view only their own tickets.

An Employee cannot access another Employee's ticket through the website or API.

Employees cannot perform Support-only actions such as assigning or starting tickets.

Support users can view all tickets.

Only Support users can be selected as ticket assignees.

Employees cannot be assigned as Support users.

An Open ticket must have an assigned Support user before it can move to **In Progress**.

A resolution note is required before an In Progress ticket can become **Resolved**.

Only the Employee who created a Resolved ticket can reopen or close it.

A reopen reason is required.

Closed tickets cannot be modified or receive new comments.

The application also validates required information such as ticket titles and descriptions.

Whitespace-only titles and descriptions are rejected.

Invalid ticket status changes are rejected by the backend.

## Ticket History

The system automatically records important ticket actions:

- Created
- Assigned
- Reassigned
- Started
- Resolved
- Reopened
- Closed

History records include the action, user, timestamp, and relevant information such as assignment changes, status changes, resolution notes, and reopen reasons.

Ticket history is displayed from oldest to newest.

Resolution information remains in the history even if the ticket is later reopened and resolved again.

This allows the progress of each ticket to be tracked from creation to completion.

## Testing

The system was manually tested throughout development.

Tests included:

- Employee login
- Support login
- Ticket creation
- New tickets starting as Open and Unassigned
- Assigning a ticket to a Support user
- Assignment without automatically changing the ticket status
- Reassigning a ticket
- Starting work on an assigned ticket
- Open to In Progress workflow
- Resolving a ticket
- Resolution notes
- Support actions when another Support user is assigned
- Employee reopening a Resolved ticket
- Reopen reasons
- Retaining the assigned Support user after reopening
- Retaining previous resolution information
- Resolving a reopened ticket again
- Employee closing their Resolved ticket
- Employee comments
- Support comments
- Comments displayed in chronological order
- Closed ticket read-only behavior
- Employee ticket visibility
- Cross-Employee API access denial
- Unauthorized Employee state changes through the API
- Combined search and filters
- Assignee filtering
- Summary counts
- API login
- API summary results

## Challenges and Learning

One of the main challenges was building the ticket workflow while making sure Employees and Support users could only perform actions allowed for their roles.

Another challenge was keeping ticket statuses, assignments, timestamps, resolution notes, reopen reasons, comments, and ticket history consistent.

I also worked on enforcing permissions in the backend so that hiding a button in the frontend is not the only protection.

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
- REST APIs
- Database persistence
- Debugging
- Testing
- Git
- GitHub

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
- Reviewing ticket workflow requirements
- Testing API permissions and validation

AI was not the only resource used during development. I also performed research using official documentation and online development resources to better understand the technologies and concepts used in the project.

Throughout development, I tested the application and reviewed its functionality to understand how the major parts of the system work and to make changes when necessary.

## Developer

Khalid Alnaji

Developed for INTELLICONZ.