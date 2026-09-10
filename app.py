from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify
)

import sqlite3
import os


app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "development-secret-key"
)


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db_connection():

    connection = sqlite3.connect("tickets.db")

    connection.row_factory = sqlite3.Row

    return connection


# =========================================================
# ADD COLUMN IF MISSING
# =========================================================

def add_column_if_missing(
    connection,
    table_name,
    column_name,
    column_definition
):

    columns = connection.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()

    column_names = [
        column["name"]
        for column in columns
    ]

    if column_name not in column_names:

        connection.execute(
            f"""
            ALTER TABLE {table_name}
            ADD COLUMN {column_name} {column_definition}
            """
        )


# =========================================================
# TICKET HISTORY HELPER
# =========================================================

def add_history(
    connection,
    ticket_id,
    action,
    details,
    actor_id
):

    connection.execute(
        """
        INSERT INTO ticket_history
        (
            ticket_id,
            action,
            details,
            actor_id,
            created_at
        )
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (
            ticket_id,
            action,
            details,
            actor_id
        )
    )


# =========================================================
# CHECK TICKET VISIBILITY
# =========================================================

def user_can_view_ticket(ticket):

    if session.get("role") == "Support":
        return True

    if (
        session.get("role") == "Employee"
        and ticket["creator_id"] == session.get("user_id")
    ):
        return True

    return False


# =========================================================
# CREATE DATABASE
# =========================================================

def create_database():

    connection = get_db_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            priority TEXT NOT NULL DEFAULT 'Medium',
            status TEXT NOT NULL DEFAULT 'Open',
            creator_id INTEGER,
            assigned_to INTEGER,
            resolution_note TEXT,
            reopen_reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    add_column_if_missing(
        connection,
        "tickets",
        "creator_id",
        "INTEGER"
    )

    add_column_if_missing(
        connection,
        "tickets",
        "assigned_to",
        "INTEGER"
    )

    add_column_if_missing(
        connection,
        "tickets",
        "resolution_note",
        "TEXT"
    )

    add_column_if_missing(
        connection,
        "tickets",
        "reopen_reason",
        "TEXT"
    )

    add_column_if_missing(
        connection,
        "tickets",
        "updated_at",
        "TIMESTAMP"
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS ticket_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            details TEXT,
            actor_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            comment TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    connection.execute(
        """
        INSERT OR IGNORE INTO users
        (username, password, role)
        VALUES
        ('employee1', 'pass123', 'Employee')
        """
    )

    connection.execute(
        """
        INSERT OR IGNORE INTO users
        (username, password, role)
        VALUES
        ('employee2', 'pass123', 'Employee')
        """
    )

    connection.execute(
        """
        INSERT OR IGNORE INTO users
        (username, password, role)
        VALUES
        ('support1', 'pass123', 'Support')
        """
    )

    connection.execute(
        """
        INSERT OR IGNORE INTO users
        (username, password, role)
        VALUES
        ('support2', 'pass123', 'Support')
        """
    )

    connection.commit()
    connection.close()


# =========================================================
# HOME / DASHBOARD
# =========================================================

@app.route("/")
def home():

    if "user_id" not in session:

        return render_template(
            "index.html",
            total_tickets=0,
            open_tickets=0,
            closed_tickets=0,
            assigned_tickets=0,
            recent_tickets=[]
        )

    connection = get_db_connection()

    if session["role"] == "Employee":

        total_tickets = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM tickets
            WHERE creator_id = ?
            """,
            (session["user_id"],)
        ).fetchone()["count"]

        open_tickets = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM tickets
            WHERE creator_id = ?
            AND status = 'Open'
            """,
            (session["user_id"],)
        ).fetchone()["count"]

        closed_tickets = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM tickets
            WHERE creator_id = ?
            AND status = 'Closed'
            """,
            (session["user_id"],)
        ).fetchone()["count"]

        assigned_tickets = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM tickets
            WHERE creator_id = ?
            AND assigned_to IS NOT NULL
            AND status = 'In Progress'
            """,
            (session["user_id"],)
        ).fetchone()["count"]

        recent_tickets = connection.execute(
            """
            SELECT
                id,
                title,
                category,
                priority,
                status,
                created_at,
                updated_at
            FROM tickets
            WHERE creator_id = ?
            ORDER BY id DESC
            LIMIT 5
            """,
            (session["user_id"],)
        ).fetchall()

    else:

        total_tickets = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM tickets
            """
        ).fetchone()["count"]

        open_tickets = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM tickets
            WHERE status = 'Open'
            """
        ).fetchone()["count"]

        assigned_tickets = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM tickets
            WHERE assigned_to = ?
            AND status = 'In Progress'
            """,
            (session["user_id"],)
        ).fetchone()["count"]

        closed_tickets = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM tickets
            WHERE status = 'Closed'
            """
        ).fetchone()["count"]

        recent_tickets = connection.execute(
            """
            SELECT
                id,
                title,
                category,
                priority,
                status,
                created_at,
                updated_at
            FROM tickets
            ORDER BY id DESC
            LIMIT 5
            """
        ).fetchall()

    connection.close()

    return render_template(
        "index.html",
        total_tickets=total_tickets,
        open_tickets=open_tickets,
        closed_tickets=closed_tickets,
        assigned_tickets=assigned_tickets,
        recent_tickets=recent_tickets
    )


# =========================================================
# CREATE TICKET
# =========================================================

@app.route(
    "/create-ticket",
    methods=["GET", "POST"]
)
def create_ticket():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "Employee":
        return "Access denied. Only Employees can create tickets."

    if request.method == "POST":

        title = request.form.get(
            "title",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        category = request.form.get(
            "category",
            ""
        )

        priority = request.form.get(
            "priority",
            "Medium"
        )

        if not title or not description:
            return "Title and Description cannot be empty."

        valid_categories = [
            "Technical Issue",
            "Access Request",
            "Other"
        ]

        valid_priorities = [
            "Low",
            "Medium",
            "High"
        ]

        if category not in valid_categories:
            return "Invalid category."

        if priority not in valid_priorities:
            return "Invalid priority."

        connection = get_db_connection()

        cursor = connection.execute(
            """
            INSERT INTO tickets
            (
                title,
                description,
                category,
                priority,
                creator_id,
                assigned_to,
                status,
                created_at,
                updated_at
            )
            VALUES
            (
                ?, ?, ?, ?, ?,
                NULL,
                'Open',
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            """,
            (
                title,
                description,
                category,
                priority,
                session["user_id"]
            )
        )

        ticket_id = cursor.lastrowid

        add_history(
            connection,
            ticket_id,
            "Created",
            "Status changed from None to Open. Assigned Support: Unassigned.",
            session["user_id"]
        )

        connection.commit()
        connection.close()

        return redirect(
            url_for("tickets")
        )

    return render_template(
        "create_ticket.html"
    )


# =========================================================
# VIEW / SEARCH / FILTER TICKETS
# =========================================================

@app.route("/tickets")
def tickets():

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()

    search = request.args.get(
        "search",
        ""
    ).strip()

    status_filter = request.args.get(
        "status",
        ""
    ).strip()

    category_filter = request.args.get(
        "category",
        ""
    ).strip()

    priority_filter = request.args.get(
        "priority",
        ""
    ).strip()

    assignee_filter = request.args.get(
        "assignee",
        ""
    ).strip()

    query = """
        SELECT
            tickets.*,
            creator.username AS creator_username,
            support.username AS assigned_username

        FROM tickets

        LEFT JOIN users AS creator
        ON tickets.creator_id = creator.id

        LEFT JOIN users AS support
        ON tickets.assigned_to = support.id

        WHERE 1 = 1
    """

    parameters = []

    if session["role"] == "Employee":

        query += """
            AND tickets.creator_id = ?
        """

        parameters.append(
            session["user_id"]
        )

    if search:

        query += """
            AND
            (
                tickets.title LIKE ?
                OR tickets.description LIKE ?
            )
        """

        search_value = f"%{search}%"

        parameters.append(search_value)
        parameters.append(search_value)

    if status_filter:

        query += """
            AND tickets.status = ?
        """

        parameters.append(
            status_filter
        )

    if category_filter:

        query += """
            AND tickets.category = ?
        """

        parameters.append(
            category_filter
        )

    if priority_filter:

        query += """
            AND tickets.priority = ?
        """

        parameters.append(
            priority_filter
        )

    if assignee_filter:

        if assignee_filter == "Unassigned":

            query += """
                AND tickets.assigned_to IS NULL
            """

        else:

            query += """
                AND support.username = ?
            """

            parameters.append(
                assignee_filter
            )

    query += """
        ORDER BY tickets.id DESC
    """

    all_tickets = connection.execute(
        query,
        parameters
    ).fetchall()

    if session["role"] == "Employee":

        summary = connection.execute(
            """
            SELECT
                COUNT(*) AS total,

                SUM(
                    CASE
                        WHEN status = 'Open'
                        THEN 1
                        ELSE 0
                    END
                ) AS open_count,

                SUM(
                    CASE
                        WHEN status = 'In Progress'
                        THEN 1
                        ELSE 0
                    END
                ) AS progress_count,

                SUM(
                    CASE
                        WHEN status = 'Resolved'
                        THEN 1
                        ELSE 0
                    END
                ) AS resolved_count,

                SUM(
                    CASE
                        WHEN status = 'Closed'
                        THEN 1
                        ELSE 0
                    END
                ) AS closed_count

            FROM tickets

            WHERE creator_id = ?
            """,
            (
                session["user_id"],
            )
        ).fetchone()

    else:

        summary = connection.execute(
            """
            SELECT
                COUNT(*) AS total,

                SUM(
                    CASE
                        WHEN status = 'Open'
                        THEN 1
                        ELSE 0
                    END
                ) AS open_count,

                SUM(
                    CASE
                        WHEN status = 'In Progress'
                        THEN 1
                        ELSE 0
                    END
                ) AS progress_count,

                SUM(
                    CASE
                        WHEN status = 'Resolved'
                        THEN 1
                        ELSE 0
                    END
                ) AS resolved_count,

                SUM(
                    CASE
                        WHEN status = 'Closed'
                        THEN 1
                        ELSE 0
                    END
                ) AS closed_count

            FROM tickets
            """
        ).fetchone()

    support_users = connection.execute(
        """
        SELECT id, username
        FROM users
        WHERE role = 'Support'
        ORDER BY username ASC
        """
    ).fetchall()

    history_rows = connection.execute(
        """
        SELECT
            ticket_history.*,
            users.username AS actor_username

        FROM ticket_history

        LEFT JOIN users
        ON ticket_history.actor_id = users.id

        ORDER BY
            ticket_history.created_at ASC,
            ticket_history.id ASC
        """
    ).fetchall()

    history_by_ticket = {}

    for history in history_rows:

        ticket_id = history["ticket_id"]

        if ticket_id not in history_by_ticket:
            history_by_ticket[ticket_id] = []

        history_by_ticket[ticket_id].append(
            history
        )

    comment_rows = connection.execute(
        """
        SELECT
            comments.*,
            users.username AS username,
            users.role AS role

        FROM comments

        LEFT JOIN users
        ON comments.user_id = users.id

        ORDER BY
            comments.created_at ASC,
            comments.id ASC
        """
    ).fetchall()

    comments_by_ticket = {}

    for comment in comment_rows:

        ticket_id = comment["ticket_id"]

        if ticket_id not in comments_by_ticket:
            comments_by_ticket[ticket_id] = []

        comments_by_ticket[ticket_id].append(
            comment
        )

    connection.close()

    return render_template(
        "tickets.html",
        tickets=all_tickets,
        summary=summary,
        search=search,
        status_filter=status_filter,
        category_filter=category_filter,
        priority_filter=priority_filter,
        assignee_filter=assignee_filter,
        support_users=support_users,
        history_by_ticket=history_by_ticket,
        comments_by_ticket=comments_by_ticket
    )


# =========================================================
# ASSIGN OR REASSIGN TICKET
# =========================================================

@app.route(
    "/assign/<int:ticket_id>",
    methods=["POST"]
)
def assign_ticket(ticket_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "Support":
        return "Access denied. Only Support users can assign tickets."

    support_user_id = request.form.get(
        "support_user_id",
        ""
    ).strip()

    if not support_user_id:
        return "Please select a Support user."

    connection = get_db_connection()

    ticket = connection.execute(
        """
        SELECT *
        FROM tickets
        WHERE id = ?
        """,
        (ticket_id,)
    ).fetchone()

    if ticket is None:

        connection.close()

        return "Ticket not found."

    if ticket["status"] == "Closed":

        connection.close()

        return "Closed tickets cannot be changed."

    support_user = connection.execute(
        """
        SELECT *
        FROM users
        WHERE id = ?
        AND role = 'Support'
        """,
        (support_user_id,)
    ).fetchone()

    if support_user is None:

        connection.close()

        return "Invalid Support user."

    old_assigned_to = ticket["assigned_to"]

    old_support_username = "Unassigned"

    if old_assigned_to is not None:

        old_support = connection.execute(
            """
            SELECT username
            FROM users
            WHERE id = ?
            """,
            (old_assigned_to,)
        ).fetchone()

        if old_support:
            old_support_username = old_support["username"]

    if old_assigned_to == support_user["id"]:

        connection.close()

        return "This ticket is already assigned to that Support user."

    connection.execute(
        """
        UPDATE tickets
        SET
            assigned_to = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            support_user["id"],
            ticket_id
        )
    )

    add_history(
        connection,
        ticket_id,
        "Assigned",
        (
            f"Assigned Support changed from "
            f"{old_support_username} to "
            f"{support_user['username']}."
        ),
        session["user_id"]
    )

    connection.commit()
    connection.close()

    return redirect(
        url_for("tickets")
    )


# =========================================================
# START WORK
# =========================================================

@app.route(
    "/start/<int:ticket_id>",
    methods=["POST"]
)
def start_ticket(ticket_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "Support":
        return "Access denied. Only Support users can start tickets."

    connection = get_db_connection()

    ticket = connection.execute(
        """
        SELECT *
        FROM tickets
        WHERE id = ?
        """,
        (ticket_id,)
    ).fetchone()

    if ticket is None:

        connection.close()

        return "Ticket not found."

    if ticket["status"] == "Closed":

        connection.close()

        return "Closed tickets cannot be changed."

    if ticket["status"] != "Open":

        connection.close()

        return "Only Open tickets can be moved to In Progress."

    if ticket["assigned_to"] is None:

        connection.close()

        return "An unassigned ticket cannot be started."

    connection.execute(
        """
        UPDATE tickets
        SET
            status = 'In Progress',
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (ticket_id,)
    )

    add_history(
        connection,
        ticket_id,
        "Status Changed",
        "Status changed from Open to In Progress.",
        session["user_id"]
    )

    connection.commit()
    connection.close()

    return redirect(
        url_for("tickets")
    )


# =========================================================
# RESOLVE TICKET
# =========================================================

@app.route(
    "/resolve/<int:ticket_id>",
    methods=["POST"]
)
def resolve_ticket(ticket_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "Support":
        return "Access denied. Only Support users can resolve tickets."

    resolution_note = request.form.get(
        "resolution_note",
        ""
    ).strip()

    if not resolution_note:
        return "Resolution note is required."

    connection = get_db_connection()

    ticket = connection.execute(
        """
        SELECT *
        FROM tickets
        WHERE id = ?
        """,
        (ticket_id,)
    ).fetchone()

    if ticket is None:

        connection.close()

        return "Ticket not found."

    if ticket["status"] == "Closed":

        connection.close()

        return "Closed tickets cannot be changed."

    if ticket["assigned_to"] is None:

        connection.close()

        return "Ticket must have an assigned Support user."

    if ticket["status"] != "In Progress":

        connection.close()

        return "Only In Progress tickets can be resolved."

    connection.execute(
        """
        UPDATE tickets
        SET
            status = 'Resolved',
            resolution_note = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            resolution_note,
            ticket_id
        )
    )

    add_history(
        connection,
        ticket_id,
        "Resolved",
        (
            "Status changed from In Progress to Resolved. "
            f"Resolution note: {resolution_note}"
        ),
        session["user_id"]
    )

    connection.commit()
    connection.close()

    return redirect(
        url_for("tickets")
    )


# =========================================================
# REOPEN TICKET
# =========================================================

@app.route(
    "/reopen/<int:ticket_id>",
    methods=["POST"]
)
def reopen_ticket(ticket_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "Employee":
        return "Access denied. Only Employees can reopen tickets."

    reopen_reason = request.form.get(
        "reopen_reason",
        ""
    ).strip()

    if not reopen_reason:
        return "Reopen reason is required."

    connection = get_db_connection()

    ticket = connection.execute(
        """
        SELECT *
        FROM tickets
        WHERE id = ?
        """,
        (ticket_id,)
    ).fetchone()

    if ticket is None:

        connection.close()

        return "Ticket not found."

    if ticket["creator_id"] != session["user_id"]:

        connection.close()

        return "Access denied. This is not your ticket."

    if ticket["status"] == "Closed":

        connection.close()

        return "Closed tickets cannot be changed."

    if ticket["status"] != "Resolved":

        connection.close()

        return "Only Resolved tickets can be reopened."

    if ticket["assigned_to"] is None:

        connection.close()

        return "Resolved ticket does not have an assigned Support user."

    connection.execute(
        """
        UPDATE tickets
        SET
            status = 'In Progress',
            reopen_reason = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            reopen_reason,
            ticket_id
        )
    )

    add_history(
        connection,
        ticket_id,
        "Reopened",
        (
            "Status changed from Resolved to In Progress. "
            f"Reason: {reopen_reason}. "
            "Assigned Support user retained."
        ),
        session["user_id"]
    )

    connection.commit()
    connection.close()

    return redirect(
        url_for("tickets")
    )


# =========================================================
# CLOSE TICKET
# =========================================================

@app.route(
    "/close/<int:ticket_id>",
    methods=["POST"]
)
def close_ticket(ticket_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "Employee":
        return "Access denied. Only Employees can close tickets."

    connection = get_db_connection()

    ticket = connection.execute(
        """
        SELECT *
        FROM tickets
        WHERE id = ?
        """,
        (ticket_id,)
    ).fetchone()

    if ticket is None:

        connection.close()

        return "Ticket not found."

    if ticket["creator_id"] != session["user_id"]:

        connection.close()

        return "Access denied. This is not your ticket."

    if ticket["status"] != "Resolved":

        connection.close()

        return "Only Resolved tickets can be closed."

    connection.execute(
        """
        UPDATE tickets
        SET
            status = 'Closed',
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (ticket_id,)
    )

    add_history(
        connection,
        ticket_id,
        "Closed",
        "Status changed from Resolved to Closed.",
        session["user_id"]
    )

    connection.commit()
    connection.close()

    return redirect(
        url_for("tickets")
    )


# =========================================================
# ADD COMMENT
# =========================================================

@app.route(
    "/comment/<int:ticket_id>",
    methods=["POST"]
)
def add_comment(ticket_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    comment_text = request.form.get(
        "comment",
        ""
    ).strip()

    if not comment_text:
        return "Comment cannot be empty."

    connection = get_db_connection()

    ticket = connection.execute(
        """
        SELECT *
        FROM tickets
        WHERE id = ?
        """,
        (ticket_id,)
    ).fetchone()

    if ticket is None:

        connection.close()

        return "Ticket not found."

    if not user_can_view_ticket(ticket):

        connection.close()

        return "Access denied."

    if ticket["status"] == "Closed":

        connection.close()

        return "Comments cannot be added to Closed tickets."

    connection.execute(
        """
        INSERT INTO comments
        (
            ticket_id,
            user_id,
            comment,
            created_at
        )
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (
            ticket_id,
            session["user_id"],
            comment_text
        )
    )

    connection.commit()
    connection.close()

    return redirect(
        url_for("tickets")
    )


# =========================================================
# LOGIN
# =========================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        ).strip()

        connection = get_db_connection()

        user = connection.execute(
            """
            SELECT *
            FROM users
            WHERE username = ?
            AND password = ?
            """,
            (
                username,
                password
            )
        ).fetchone()

        connection.close()

        if user:

            session["user_id"] = user["id"]

            session["username"] = user["username"]

            session["role"] = user["role"]

            return redirect(
                url_for("home")
            )

        return "Invalid username or password."

    return render_template(
        "login.html"
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# =========================================================
# API LOGIN
# =========================================================

@app.route(
    "/api/login",
    methods=["POST"]
)
def api_login():

    data = request.get_json(
        silent=True
    ) or {}

    username = str(
        data.get(
            "username",
            ""
        )
    ).strip()

    password = str(
        data.get(
            "password",
            ""
        )
    ).strip()

    if not username or not password:

        return jsonify({
            "error": "Username and password are required."
        }), 400

    connection = get_db_connection()

    user = connection.execute(
        """
        SELECT *
        FROM users
        WHERE username = ?
        AND password = ?
        """,
        (
            username,
            password
        )
    ).fetchone()

    connection.close()

    if user is None:

        return jsonify({
            "error": "Invalid username or password."
        }), 401

    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["role"] = user["role"]

    return jsonify({
        "message": "Login successful.",
        "username": user["username"],
        "role": user["role"]
    })


# =========================================================
# API GET ALL TICKETS
# =========================================================

@app.route(
    "/api/tickets",
    methods=["GET"]
)
def api_get_tickets():

    if "user_id" not in session:

        return jsonify({
            "error": "Authentication required."
        }), 401

    connection = get_db_connection()

    query = """
        SELECT
            tickets.*,
            creator.username AS creator_username,
            support.username AS assigned_username

        FROM tickets

        LEFT JOIN users AS creator
        ON tickets.creator_id = creator.id

        LEFT JOIN users AS support
        ON tickets.assigned_to = support.id

        WHERE 1 = 1
    """

    parameters = []

    if session["role"] == "Employee":

        query += """
            AND tickets.creator_id = ?
        """

        parameters.append(
            session["user_id"]
        )

    search = request.args.get(
        "search",
        ""
    ).strip()

    status_filter = request.args.get(
        "status",
        ""
    ).strip()

    category_filter = request.args.get(
        "category",
        ""
    ).strip()

    priority_filter = request.args.get(
        "priority",
        ""
    ).strip()

    assignee_filter = request.args.get(
        "assignee",
        ""
    ).strip()

    if search:

        query += """
            AND
            (
                tickets.title LIKE ?
                OR tickets.description LIKE ?
            )
        """

        search_value = f"%{search}%"

        parameters.extend(
            [
                search_value,
                search_value
            ]
        )

    if status_filter:

        query += """
            AND tickets.status = ?
        """

        parameters.append(
            status_filter
        )

    if category_filter:

        query += """
            AND tickets.category = ?
        """

        parameters.append(
            category_filter
        )

    if priority_filter:

        query += """
            AND tickets.priority = ?
        """

        parameters.append(
            priority_filter
        )

    if assignee_filter:

        if assignee_filter == "Unassigned":

            query += """
                AND tickets.assigned_to IS NULL
            """

        else:

            query += """
                AND support.username = ?
            """

            parameters.append(
                assignee_filter
            )

    query += """
        ORDER BY tickets.id DESC
    """

    rows = connection.execute(
        query,
        parameters
    ).fetchall()

    connection.close()

    return jsonify(
        [
            dict(ticket)
            for ticket in rows
        ]
    )


# =========================================================
# API GET ONE TICKET
# =========================================================

@app.route(
    "/api/tickets/<int:ticket_id>",
    methods=["GET"]
)
def api_get_ticket(ticket_id):

    if "user_id" not in session:

        return jsonify({
            "error": "Authentication required."
        }), 401

    connection = get_db_connection()

    ticket = connection.execute(
        """
        SELECT
            tickets.*,
            creator.username AS creator_username,
            support.username AS assigned_username

        FROM tickets

        LEFT JOIN users AS creator
        ON tickets.creator_id = creator.id

        LEFT JOIN users AS support
        ON tickets.assigned_to = support.id

        WHERE tickets.id = ?
        """,
        (ticket_id,)
    ).fetchone()

    if ticket is None:

        connection.close()

        return jsonify({
            "error": "Ticket not found."
        }), 404

    if not user_can_view_ticket(ticket):

        connection.close()

        return jsonify({
            "error": "Access denied."
        }), 403

    history_rows = connection.execute(
        """
        SELECT
            ticket_history.id,
            ticket_history.action,
            ticket_history.details,
            ticket_history.created_at,
            users.username AS actor_username

        FROM ticket_history

        LEFT JOIN users
        ON ticket_history.actor_id = users.id

        WHERE ticket_history.ticket_id = ?

        ORDER BY
            ticket_history.created_at ASC,
            ticket_history.id ASC
        """,
        (ticket_id,)
    ).fetchall()

    comment_rows = connection.execute(
        """
        SELECT
            comments.id,
            comments.comment,
            comments.created_at,
            users.username,
            users.role

        FROM comments

        LEFT JOIN users
        ON comments.user_id = users.id

        WHERE comments.ticket_id = ?

        ORDER BY
            comments.created_at ASC,
            comments.id ASC
        """,
        (ticket_id,)
    ).fetchall()

    connection.close()

    ticket_data = dict(ticket)

    ticket_data["history"] = [
        dict(history)
        for history in history_rows
    ]

    ticket_data["comments"] = [
        dict(comment)
        for comment in comment_rows
    ]

    return jsonify(
        ticket_data
    )


# =========================================================
# API CREATE TICKET
# =========================================================

@app.route(
    "/api/tickets",
    methods=["POST"]
)
def api_create_ticket():

    if "user_id" not in session:

        return jsonify({
            "error": "Authentication required."
        }), 401

    if session["role"] != "Employee":

        return jsonify({
            "error": "Only Employees can create tickets."
        }), 403

    data = request.get_json(
        silent=True
    ) or {}

    title = str(
        data.get(
            "title",
            ""
        )
    ).strip()

    description = str(
        data.get(
            "description",
            ""
        )
    ).strip()

    category = data.get(
        "category",
        ""
    )

    priority = data.get(
        "priority",
        "Medium"
    )

    if not title or not description:

        return jsonify({
            "error": "Title and description are required."
        }), 400

    valid_categories = [
        "Technical Issue",
        "Access Request",
        "Other"
    ]

    valid_priorities = [
        "Low",
        "Medium",
        "High"
    ]

    if category not in valid_categories:

        return jsonify({
            "error": "Invalid category."
        }), 400

    if priority not in valid_priorities:

        return jsonify({
            "error": "Invalid priority."
        }), 400

    connection = get_db_connection()

    cursor = connection.execute(
        """
        INSERT INTO tickets
        (
            title,
            description,
            category,
            priority,
            status,
            creator_id,
            assigned_to,
            created_at,
            updated_at
        )

        VALUES
        (
            ?, ?, ?, ?,
            'Open',
            ?,
            NULL,
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        )
        """,
        (
            title,
            description,
            category,
            priority,
            session["user_id"]
        )
    )

    ticket_id = cursor.lastrowid

    add_history(
        connection,
        ticket_id,
        "Created",
        "Status changed from None to Open. Assigned Support: Unassigned.",
        session["user_id"]
    )

    connection.commit()

    new_ticket = connection.execute(
        """
        SELECT *
        FROM tickets
        WHERE id = ?
        """,
        (ticket_id,)
    ).fetchone()

    connection.close()

    return jsonify({
        "message": "Ticket created successfully.",
        "ticket": dict(new_ticket)
    }), 201


# =========================================================
# API ASSIGN / REASSIGN
# =========================================================

@app.route(
    "/api/tickets/<int:ticket_id>/assign",
    methods=["POST"]
)
def api_assign_ticket(ticket_id):

    if "user_id" not in session:

        return jsonify({
            "error": "Authentication required."
        }), 401

    if session["role"] != "Support":

        return jsonify({
            "error": "Only Support users can assign tickets."
        }), 403

    data = request.get_json(
        silent=True
    ) or {}

    support_user_id = data.get(
        "support_user_id"
    )

    if support_user_id is None:

        return jsonify({
            "error": "support_user_id is required."
        }), 400

    connection = get_db_connection()

    ticket = connection.execute(
        """
        SELECT *
        FROM tickets
        WHERE id = ?
        """,
        (ticket_id,)
    ).fetchone()

    if ticket is None:

        connection.close()

        return jsonify({
            "error": "Ticket not found."
        }), 404

    if ticket["status"] == "Closed":

        connection.close()

        return jsonify({
            "error": "Closed tickets cannot be changed."
        }), 400

    support_user = connection.execute(
        """
        SELECT *
        FROM users
        WHERE id = ?
        AND role = 'Support'
        """,
        (support_user_id,)
    ).fetchone()

    if support_user is None:

        connection.close()

        return jsonify({
            "error": "Invalid Support user."
        }), 400

    old_support_username = "Unassigned"

    if ticket["assigned_to"] is not None:

        old_support = connection.execute(
            """
            SELECT username
            FROM users
            WHERE id = ?
            """,
            (ticket["assigned_to"],)
        ).fetchone()

        if old_support:

            old_support_username = old_support["username"]

    if ticket["assigned_to"] == support_user["id"]:

        connection.close()

        return jsonify({
            "error": "Ticket is already assigned to that Support user."
        }), 400

    connection.execute(
        """
        UPDATE tickets
        SET
            assigned_to = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            support_user["id"],
            ticket_id
        )
    )

    add_history(
        connection,
        ticket_id,
        "Assigned",
        (
            f"Assigned Support changed from "
            f"{old_support_username} to "
            f"{support_user['username']}."
        ),
        session["user_id"]
    )

    connection.commit()
    connection.close()

    return jsonify({
        "message": "Ticket assignment updated successfully.",
        "ticket_id": ticket_id,
        "assigned_to": support_user["username"]
    })


# =========================================================
# API START WORK
# =========================================================

@app.route(
    "/api/tickets/<int:ticket_id>/start",
    methods=["POST"]
)
def api_start_ticket(ticket_id):

    if "user_id" not in session:

        return jsonify({
            "error": "Authentication required."
        }), 401

    if session["role"] != "Support":

        return jsonify({
            "error": "Only Support users can start tickets."
        }), 403

    connection = get_db_connection()

    ticket = connection.execute(
        """
        SELECT *
        FROM tickets
        WHERE id = ?
        """,
        (ticket_id,)
    ).fetchone()

    if ticket is None:

        connection.close()

        return jsonify({
            "error": "Ticket not found."
        }), 404

    if ticket["status"] == "Closed":

        connection.close()

        return jsonify({
            "error": "Closed tickets cannot be changed."
        }), 400

    if ticket["status"] != "Open":

        connection.close()

        return jsonify({
            "error": "Only Open tickets can be started."
        }), 400

    if ticket["assigned_to"] is None:

        connection.close()

        return jsonify({
            "error": "An unassigned ticket cannot be started."
        }), 400

    connection.execute(
        """
        UPDATE tickets
        SET
            status = 'In Progress',
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (ticket_id,)
    )

    add_history(
        connection,
        ticket_id,
        "Status Changed",
        "Status changed from Open to In Progress.",
        session["user_id"]
    )

    connection.commit()
    connection.close()

    return jsonify({
        "message": "Ticket moved to In Progress.",
        "ticket_id": ticket_id,
        "status": "In Progress"
    })


# =========================================================
# API RESOLVE
# =========================================================

@app.route(
    "/api/tickets/<int:ticket_id>/resolve",
    methods=["POST"]
)
def api_resolve_ticket(ticket_id):

    if "user_id" not in session:

        return jsonify({
            "error": "Authentication required."
        }), 401

    if session["role"] != "Support":

        return jsonify({
            "error": "Only Support users can resolve tickets."
        }), 403

    data = request.get_json(
        silent=True
    ) or {}

    resolution_note = str(
        data.get(
            "resolution_note",
            ""
        )
    ).strip()

    if not resolution_note:

        return jsonify({
            "error": "Resolution note is required."
        }), 400

    connection = get_db_connection()

    ticket = connection.execute(
        """
        SELECT *
        FROM tickets
        WHERE id = ?
        """,
        (ticket_id,)
    ).fetchone()

    if ticket is None:

        connection.close()

        return jsonify({
            "error": "Ticket not found."
        }), 404

    if ticket["status"] == "Closed":

        connection.close()

        return jsonify({
            "error": "Closed tickets cannot be changed."
        }), 400

    if ticket["assigned_to"] is None:

        connection.close()

        return jsonify({
            "error": "Ticket must have an assigned Support user."
        }), 400

    if ticket["status"] != "In Progress":

        connection.close()

        return jsonify({
            "error": "Only In Progress tickets can be resolved."
        }), 400

    connection.execute(
        """
        UPDATE tickets
        SET
            status = 'Resolved',
            resolution_note = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            resolution_note,
            ticket_id
        )
    )

    add_history(
        connection,
        ticket_id,
        "Resolved",
        (
            "Status changed from In Progress to Resolved. "
            f"Resolution note: {resolution_note}"
        ),
        session["user_id"]
    )

    connection.commit()
    connection.close()

    return jsonify({
        "message": "Ticket resolved successfully.",
        "ticket_id": ticket_id,
        "status": "Resolved"
    })


# =========================================================
# API REOPEN
# =========================================================

@app.route(
    "/api/tickets/<int:ticket_id>/reopen",
    methods=["POST"]
)
def api_reopen_ticket(ticket_id):

    if "user_id" not in session:

        return jsonify({
            "error": "Authentication required."
        }), 401

    if session["role"] != "Employee":

        return jsonify({
            "error": "Only Employees can reopen tickets."
        }), 403

    data = request.get_json(
        silent=True
    ) or {}

    reopen_reason = str(
        data.get(
            "reopen_reason",
            ""
        )
    ).strip()

    if not reopen_reason:

        return jsonify({
            "error": "Reopen reason is required."
        }), 400

    connection = get_db_connection()

    ticket = connection.execute(
        """
        SELECT *
        FROM tickets
        WHERE id = ?
        """,
        (ticket_id,)
    ).fetchone()

    if ticket is None:

        connection.close()

        return jsonify({
            "error": "Ticket not found."
        }), 404

    if ticket["creator_id"] != session["user_id"]:

        connection.close()

        return jsonify({
            "error": "You can only reopen your own tickets."
        }), 403

    if ticket["status"] == "Closed":

        connection.close()

        return jsonify({
            "error": "Closed tickets cannot be changed."
        }), 400

    if ticket["status"] != "Resolved":

        connection.close()

        return jsonify({
            "error": "Only Resolved tickets can be reopened."
        }), 400

    if ticket["assigned_to"] is None:

        connection.close()

        return jsonify({
            "error": "Ticket does not have an assigned Support user."
        }), 400

    connection.execute(
        """
        UPDATE tickets
        SET
            status = 'In Progress',
            reopen_reason = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            reopen_reason,
            ticket_id
        )
    )

    add_history(
        connection,
        ticket_id,
        "Reopened",
        (
            "Status changed from Resolved to In Progress. "
            f"Reason: {reopen_reason}. "
            "Assigned Support user retained."
        ),
        session["user_id"]
    )

    connection.commit()
    connection.close()

    return jsonify({
        "message": "Ticket reopened successfully.",
        "ticket_id": ticket_id,
        "status": "In Progress"
    })


# =========================================================
# API CLOSE
# =========================================================

@app.route(
    "/api/tickets/<int:ticket_id>/close",
    methods=["POST"]
)
def api_close_ticket(ticket_id):

    if "user_id" not in session:

        return jsonify({
            "error": "Authentication required."
        }), 401

    if session["role"] != "Employee":

        return jsonify({
            "error": "Only Employees can close tickets."
        }), 403

    connection = get_db_connection()

    ticket = connection.execute(
        """
        SELECT *
        FROM tickets
        WHERE id = ?
        """,
        (ticket_id,)
    ).fetchone()

    if ticket is None:

        connection.close()

        return jsonify({
            "error": "Ticket not found."
        }), 404

    if ticket["creator_id"] != session["user_id"]:

        connection.close()

        return jsonify({
            "error": "You can only close your own tickets."
        }), 403

    if ticket["status"] != "Resolved":

        connection.close()

        return jsonify({
            "error": "Only Resolved tickets can be closed."
        }), 400

    connection.execute(
        """
        UPDATE tickets
        SET
            status = 'Closed',
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (ticket_id,)
    )

    add_history(
        connection,
        ticket_id,
        "Closed",
        "Status changed from Resolved to Closed.",
        session["user_id"]
    )

    connection.commit()
    connection.close()

    return jsonify({
        "message": "Ticket closed successfully.",
        "ticket_id": ticket_id,
        "status": "Closed"
    })


# =========================================================
# API COMMENTS
# =========================================================

@app.route(
    "/api/tickets/<int:ticket_id>/comments",
    methods=["GET", "POST"]
)
def api_ticket_comments(ticket_id):

    if "user_id" not in session:

        return jsonify({
            "error": "Authentication required."
        }), 401

    connection = get_db_connection()

    ticket = connection.execute(
        """
        SELECT *
        FROM tickets
        WHERE id = ?
        """,
        (ticket_id,)
    ).fetchone()

    if ticket is None:

        connection.close()

        return jsonify({
            "error": "Ticket not found."
        }), 404

    if not user_can_view_ticket(ticket):

        connection.close()

        return jsonify({
            "error": "Access denied."
        }), 403

    if request.method == "POST":

        if ticket["status"] == "Closed":

            connection.close()

            return jsonify({
                "error": "Comments cannot be added to Closed tickets."
            }), 400

        data = request.get_json(
            silent=True
        ) or {}

        comment_text = str(
            data.get(
                "comment",
                ""
            )
        ).strip()

        if not comment_text:

            connection.close()

            return jsonify({
                "error": "Comment cannot be empty."
            }), 400

        connection.execute(
            """
            INSERT INTO comments
            (
                ticket_id,
                user_id,
                comment,
                created_at
            )
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                ticket_id,
                session["user_id"],
                comment_text
            )
        )

        connection.commit()

    rows = connection.execute(
        """
        SELECT
            comments.id,
            comments.comment,
            comments.created_at,
            users.username,
            users.role

        FROM comments

        LEFT JOIN users
        ON comments.user_id = users.id

        WHERE comments.ticket_id = ?

        ORDER BY
            comments.created_at ASC,
            comments.id ASC
        """,
        (ticket_id,)
    ).fetchall()

    connection.close()

    return jsonify(
        [
            dict(comment)
            for comment in rows
        ]
    )


# =========================================================
# API HISTORY
# =========================================================

@app.route(
    "/api/tickets/<int:ticket_id>/history",
    methods=["GET"]
)
def api_ticket_history(ticket_id):

    if "user_id" not in session:

        return jsonify({
            "error": "Authentication required."
        }), 401

    connection = get_db_connection()

    ticket = connection.execute(
        """
        SELECT *
        FROM tickets
        WHERE id = ?
        """,
        (ticket_id,)
    ).fetchone()

    if ticket is None:

        connection.close()

        return jsonify({
            "error": "Ticket not found."
        }), 404

    if not user_can_view_ticket(ticket):

        connection.close()

        return jsonify({
            "error": "Access denied."
        }), 403

    rows = connection.execute(
        """
        SELECT
            ticket_history.id,
            ticket_history.action,
            ticket_history.details,
            ticket_history.created_at,
            users.username AS actor_username

        FROM ticket_history

        LEFT JOIN users
        ON ticket_history.actor_id = users.id

        WHERE ticket_history.ticket_id = ?

        ORDER BY
            ticket_history.created_at ASC,
            ticket_history.id ASC
        """,
        (ticket_id,)
    ).fetchall()

    connection.close()

    return jsonify(
        [
            dict(history)
            for history in rows
        ]
    )


# =========================================================
# API SUMMARY
# =========================================================

@app.route(
    "/api/summary",
    methods=["GET"]
)
def api_summary():

    if "user_id" not in session:

        return jsonify({
            "error": "Authentication required."
        }), 401

    connection = get_db_connection()

    if session["role"] == "Employee":

        summary = connection.execute(
            """
            SELECT
                COUNT(*) AS total,

                COALESCE(SUM(
                    CASE
                        WHEN status = 'Open'
                        THEN 1
                        ELSE 0
                    END
                ), 0) AS open,

                COALESCE(SUM(
                    CASE
                        WHEN status = 'In Progress'
                        THEN 1
                        ELSE 0
                    END
                ), 0) AS in_progress,

                COALESCE(SUM(
                    CASE
                        WHEN status = 'Resolved'
                        THEN 1
                        ELSE 0
                    END
                ), 0) AS resolved,

                COALESCE(SUM(
                    CASE
                        WHEN status = 'Closed'
                        THEN 1
                        ELSE 0
                    END
                ), 0) AS closed

            FROM tickets
            WHERE creator_id = ?
            """,
            (session["user_id"],)
        ).fetchone()

    else:

        summary = connection.execute(
            """
            SELECT
                COUNT(*) AS total,

                COALESCE(SUM(
                    CASE
                        WHEN status = 'Open'
                        THEN 1
                        ELSE 0
                    END
                ), 0) AS open,

                COALESCE(SUM(
                    CASE
                        WHEN status = 'In Progress'
                        THEN 1
                        ELSE 0
                    END
                ), 0) AS in_progress,

                COALESCE(SUM(
                    CASE
                        WHEN status = 'Resolved'
                        THEN 1
                        ELSE 0
                    END
                ), 0) AS resolved,

                COALESCE(SUM(
                    CASE
                        WHEN status = 'Closed'
                        THEN 1
                        ELSE 0
                    END
                ), 0) AS closed

            FROM tickets
            """
        ).fetchone()

    connection.close()

    return jsonify(
        dict(summary)
    )


# =========================================================
# START APPLICATION
# =========================================================

if __name__ == "__main__":

    create_database()

    app.run(debug=True)