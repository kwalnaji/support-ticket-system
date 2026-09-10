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


app = Flask(__name__)
app.secret_key = "support-ticket-secret-key"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db_connection():

    connection = sqlite3.connect("tickets.db")

    connection.row_factory = sqlite3.Row

    return connection


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

    connection.execute("""
        INSERT INTO ticket_history
        (
            ticket_id,
            action,
            details,
            actor_id,
            created_at
        )
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (
        ticket_id,
        action,
        details,
        actor_id
    ))


# =========================================================
# CREATE DATABASE
# =========================================================

def create_database():

    connection = get_db_connection()

    # -----------------------------------------------------
    # USERS TABLE
    # -----------------------------------------------------

    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    # -----------------------------------------------------
    # TICKETS TABLE
    # -----------------------------------------------------

    connection.execute("""
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
    """)

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

    # -----------------------------------------------------
    # HISTORY TABLE
    # -----------------------------------------------------

    connection.execute("""
        CREATE TABLE IF NOT EXISTS ticket_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            details TEXT,
            actor_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # -----------------------------------------------------
    # EMPLOYEE TEST ACCOUNTS
    # -----------------------------------------------------

    connection.execute("""
        INSERT OR IGNORE INTO users
        (username, password, role)
        VALUES
        ('employee1', 'pass123', 'Employee')
    """)

    connection.execute("""
        INSERT OR IGNORE INTO users
        (username, password, role)
        VALUES
        ('employee2', 'pass123', 'Employee')
    """)

    # -----------------------------------------------------
    # SUPPORT TEST ACCOUNTS
    # -----------------------------------------------------

    connection.execute("""
        INSERT OR IGNORE INTO users
        (username, password, role)
        VALUES
        ('support1', 'pass123', 'Support')
    """)

    connection.execute("""
        INSERT OR IGNORE INTO users
        (username, password, role)
        VALUES
        ('support2', 'pass123', 'Support')
    """)

    connection.commit()
    connection.close()


# =========================================================
# HOME / DASHBOARD
# =========================================================

@app.route("/")
def home():

    # -----------------------------------------------------
    # USER NOT LOGGED IN
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # EMPLOYEE DASHBOARD
    # -----------------------------------------------------

    if session["role"] == "Employee":

        total_tickets = connection.execute("""
            SELECT COUNT(*) AS count
            FROM tickets
            WHERE creator_id = ?
        """, (
            session["user_id"],
        )).fetchone()["count"]

        open_tickets = connection.execute("""
            SELECT COUNT(*) AS count
            FROM tickets
            WHERE creator_id = ?
            AND status = 'Open'
        """, (
            session["user_id"],
        )).fetchone()["count"]

        closed_tickets = connection.execute("""
            SELECT COUNT(*) AS count
            FROM tickets
            WHERE creator_id = ?
            AND status = 'Closed'
        """, (
            session["user_id"],
        )).fetchone()["count"]

        assigned_tickets = 0

        recent_tickets = connection.execute("""
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
        """, (
            session["user_id"],
        )).fetchall()

    # -----------------------------------------------------
    # SUPPORT DASHBOARD
    # -----------------------------------------------------

    elif session["role"] == "Support":

        total_tickets = connection.execute("""
            SELECT COUNT(*) AS count
            FROM tickets
        """).fetchone()["count"]

        open_tickets = connection.execute("""
            SELECT COUNT(*) AS count
            FROM tickets
            WHERE status = 'Open'
        """).fetchone()["count"]

        assigned_tickets = connection.execute("""
            SELECT COUNT(*) AS count
            FROM tickets
            WHERE assigned_to = ?
            AND status = 'In Progress'
        """, (
            session["user_id"],
        )).fetchone()["count"]

        closed_tickets = connection.execute("""
            SELECT COUNT(*) AS count
            FROM tickets
            WHERE status = 'Closed'
        """).fetchone()["count"]

        recent_tickets = connection.execute("""
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
        """).fetchall()

    # -----------------------------------------------------
    # FALLBACK
    # -----------------------------------------------------

    else:

        total_tickets = 0
        open_tickets = 0
        closed_tickets = 0
        assigned_tickets = 0
        recent_tickets = []

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

        return redirect(
            url_for("login")
        )

    if session["role"] != "Employee":

        return (
            "Access denied. "
            "Only Employees can create tickets."
        )

    if request.method == "POST":

        title = request.form[
            "title"
        ].strip()

        description = request.form[
            "description"
        ].strip()

        category = request.form[
            "category"
        ]

        priority = request.form.get(
            "priority",
            "Medium"
        )

        if not title or not description:

            return (
                "Title and Description "
                "cannot be empty."
            )

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

        cursor = connection.execute("""
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
        """, (
            title,
            description,
            category,
            priority,
            session["user_id"]
        ))

        ticket_id = cursor.lastrowid

        add_history(
            connection,
            ticket_id,
            "Created",
            "Ticket created with status Open.",
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

        return redirect(
            url_for("login")
        )

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

    query += """
        ORDER BY tickets.id DESC
    """

    all_tickets = connection.execute(
        query,
        parameters
    ).fetchall()

    if session["role"] == "Employee":

        summary = connection.execute("""
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
        """, (
            session["user_id"],
        )).fetchone()

    else:

        summary = connection.execute("""
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
        """).fetchone()

    history_rows = connection.execute("""
        SELECT
            ticket_history.*,
            users.username AS actor_username

        FROM ticket_history

        LEFT JOIN users
        ON ticket_history.actor_id = users.id

        ORDER BY
            ticket_history.created_at ASC,
            ticket_history.id ASC
    """).fetchall()

    history_by_ticket = {}

    for history in history_rows:

        ticket_id = history[
            "ticket_id"
        ]

        if ticket_id not in history_by_ticket:

            history_by_ticket[
                ticket_id
            ] = []

        history_by_ticket[
            ticket_id
        ].append(
            history
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
        history_by_ticket=history_by_ticket
    )


# =========================================================
# ASSIGN TICKET
# =========================================================

@app.route(
    "/assign/<int:ticket_id>",
    methods=["POST"]
)
def assign_ticket(ticket_id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    if session["role"] != "Support":

        return (
            "Access denied. "
            "Only Support users can assign tickets."
        )

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

        return (
            "Closed tickets cannot be changed."
        )

    if ticket["assigned_to"] is not None:

        connection.close()

        return (
            "This ticket is already assigned."
        )

    connection.execute("""
        UPDATE tickets
        SET
            assigned_to = ?,
            status = 'In Progress',
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        session["user_id"],
        ticket_id
    ))

    add_history(
        connection,
        ticket_id,
        "Assigned",
        (
            "Ticket assigned to "
            f"{session['username']} "
            "and moved to In Progress."
        ),
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

        return redirect(
            url_for("login")
        )

    if session["role"] != "Support":

        return (
            "Access denied. "
            "Only Support users can resolve tickets."
        )

    resolution_note = request.form[
        "resolution_note"
    ].strip()

    if not resolution_note:

        return (
            "Resolution note is required."
        )

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

        return (
            "Closed tickets cannot be changed."
        )

    if (
        ticket["assigned_to"]
        != session["user_id"]
    ):

        connection.close()

        return (
            "Access denied. "
            "You are not assigned to this ticket."
        )

    if ticket["status"] != "In Progress":

        connection.close()

        return (
            "Only In Progress tickets "
            "can be resolved."
        )

    connection.execute("""
        UPDATE tickets
        SET
            status = 'Resolved',
            resolution_note = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        resolution_note,
        ticket_id
    ))

    add_history(
        connection,
        ticket_id,
        "Resolved",
        (
            "Ticket resolved. "
            "Resolution note: "
            f"{resolution_note}"
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

        return redirect(
            url_for("login")
        )

    if session["role"] != "Employee":

        return (
            "Access denied. "
            "Only Employees can reopen tickets."
        )

    reopen_reason = request.form[
        "reopen_reason"
    ].strip()

    if not reopen_reason:

        return (
            "Reopen reason is required."
        )

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

        return (
            "Closed tickets cannot be changed."
        )

    if (
        ticket["creator_id"]
        != session["user_id"]
    ):

        connection.close()

        return (
            "Access denied. "
            "This is not your ticket."
        )

    if ticket["status"] != "Resolved":

        connection.close()

        return (
            "Only Resolved tickets "
            "can be reopened."
        )

    connection.execute("""
        UPDATE tickets
        SET
            status = 'Open',
            assigned_to = NULL,
            resolution_note = NULL,
            reopen_reason = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        reopen_reason,
        ticket_id
    ))

    add_history(
        connection,
        ticket_id,
        "Reopened",
        (
            "Ticket reopened. "
            "Reason: "
            f"{reopen_reason}"
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

        return redirect(
            url_for("login")
        )

    if session["role"] != "Support":

        return (
            "Access denied. "
            "Only Support users can close tickets."
        )

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

    if (
        ticket["assigned_to"]
        != session["user_id"]
    ):

        connection.close()

        return (
            "Access denied. "
            "You are not assigned to this ticket."
        )

    if ticket["status"] != "Resolved":

        connection.close()

        return (
            "Only Resolved tickets "
            "can be closed."
        )

    connection.execute("""
        UPDATE tickets
        SET
            status = 'Closed',
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        ticket_id,
    ))

    add_history(
        connection,
        ticket_id,
        "Closed",
        "Ticket closed.",
        session["user_id"]
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

        username = request.form[
            "username"
        ].strip()

        password = request.form[
            "password"
        ].strip()

        connection = get_db_connection()

        user = connection.execute("""
            SELECT *
            FROM users
            WHERE username = ?
            AND password = ?
        """, (
            username,
            password
        )).fetchone()

        connection.close()

        if user:

            session["user_id"] = user[
                "id"
            ]

            session["username"] = user[
                "username"
            ]

            session["role"] = user[
                "role"
            ]

            return redirect(
                url_for("home")
            )

        return (
            "Invalid username or password."
        )

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
# API - GET ALL TICKETS
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

    search = request.args.get(
        "search",
        ""
    ).strip()

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

    if search:

        query += """
            AND
            (
                tickets.title LIKE ?
                OR tickets.description LIKE ?
            )
        """

        search_value = (
            f"%{search}%"
        )

        parameters.append(
            search_value
        )

        parameters.append(
            search_value
        )

    query += """
        ORDER BY tickets.id DESC
    """

    rows = connection.execute(
        query,
        parameters
    ).fetchall()

    connection.close()

    tickets_list = []

    for ticket in rows:

        tickets_list.append(
            dict(ticket)
        )

    return jsonify(
        tickets_list
    )


# =========================================================
# API - GET ONE TICKET
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

    ticket = connection.execute("""
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
    """, (
        ticket_id,
    )).fetchone()

    if ticket is None:

        connection.close()

        return jsonify({
            "error": "Ticket not found."
        }), 404

    if (
        session["role"] == "Employee"
        and ticket["creator_id"]
        != session["user_id"]
    ):

        connection.close()

        return jsonify({
            "error": "Access denied."
        }), 403

    history_rows = connection.execute("""
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
    """, (
        ticket_id,
    )).fetchall()

    connection.close()

    ticket_data = dict(ticket)

    ticket_data["history"] = [
        dict(history)
        for history in history_rows
    ]

    return jsonify(
        ticket_data
    )


# =========================================================
# API - CREATE TICKET
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
            "error":
                "Only Employees can create tickets."
        }), 403

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify({
            "error":
                "JSON request body is required."
        }), 400

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
            "error":
                "Title and description are required."
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

    cursor = connection.execute("""
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
    """, (
        title,
        description,
        category,
        priority,
        session["user_id"]
    ))

    ticket_id = cursor.lastrowid

    add_history(
        connection,
        ticket_id,
        "Created",
        "Ticket created with status Open.",
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
        "message":
            "Ticket created successfully.",
        "ticket":
            dict(new_ticket)
    }), 201


# =========================================================
# API - ASSIGN TICKET
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
            "error":
                "Only Support users can assign tickets."
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
            "error":
                "Closed tickets cannot be changed."
        }), 400

    if ticket["assigned_to"] is not None:

        connection.close()

        return jsonify({
            "error":
                "Ticket is already assigned."
        }), 400

    connection.execute("""
        UPDATE tickets
        SET
            assigned_to = ?,
            status = 'In Progress',
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        session["user_id"],
        ticket_id
    ))

    add_history(
        connection,
        ticket_id,
        "Assigned",
        (
            "Ticket assigned to "
            f"{session['username']} "
            "and moved to In Progress."
        ),
        session["user_id"]
    )

    connection.commit()
    connection.close()

    return jsonify({
        "message":
            "Ticket assigned successfully.",
        "ticket_id":
            ticket_id,
        "status":
            "In Progress",
        "assigned_to":
            session["username"]
    })


# =========================================================
# API - RESOLVE TICKET
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
            "error":
                "Only Support users can resolve tickets."
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
            "error":
                "Resolution note is required."
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
            "error":
                "Closed tickets cannot be changed."
        }), 400

    if (
        ticket["assigned_to"]
        != session["user_id"]
    ):

        connection.close()

        return jsonify({
            "error":
                "You are not assigned to this ticket."
        }), 403

    if ticket["status"] != "In Progress":

        connection.close()

        return jsonify({
            "error":
                "Only In Progress tickets "
                "can be resolved."
        }), 400

    connection.execute("""
        UPDATE tickets
        SET
            status = 'Resolved',
            resolution_note = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        resolution_note,
        ticket_id
    ))

    add_history(
        connection,
        ticket_id,
        "Resolved",
        (
            "Ticket resolved. "
            "Resolution note: "
            f"{resolution_note}"
        ),
        session["user_id"]
    )

    connection.commit()
    connection.close()

    return jsonify({
        "message":
            "Ticket resolved successfully.",
        "ticket_id":
            ticket_id,
        "status":
            "Resolved"
    })


# =========================================================
# API - REOPEN TICKET
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
            "error":
                "Only Employees can reopen tickets."
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
            "error":
                "Reopen reason is required."
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
            "error":
                "Closed tickets cannot be changed."
        }), 400

    if (
        ticket["creator_id"]
        != session["user_id"]
    ):

        connection.close()

        return jsonify({
            "error":
                "You can only reopen your own tickets."
        }), 403

    if ticket["status"] != "Resolved":

        connection.close()

        return jsonify({
            "error":
                "Only Resolved tickets can be reopened."
        }), 400

    connection.execute("""
        UPDATE tickets
        SET
            status = 'Open',
            assigned_to = NULL,
            resolution_note = NULL,
            reopen_reason = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        reopen_reason,
        ticket_id
    ))

    add_history(
        connection,
        ticket_id,
        "Reopened",
        (
            "Ticket reopened. "
            "Reason: "
            f"{reopen_reason}"
        ),
        session["user_id"]
    )

    connection.commit()
    connection.close()

    return jsonify({
        "message":
            "Ticket reopened successfully.",
        "ticket_id":
            ticket_id,
        "status":
            "Open"
    })


# =========================================================
# API - CLOSE TICKET
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

    if session["role"] != "Support":

        return jsonify({
            "error":
                "Only Support users can close tickets."
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

    if (
        ticket["assigned_to"]
        != session["user_id"]
    ):

        connection.close()

        return jsonify({
            "error":
                "You are not assigned to this ticket."
        }), 403

    if ticket["status"] != "Resolved":

        connection.close()

        return jsonify({
            "error":
                "Only Resolved tickets can be closed."
        }), 400

    connection.execute("""
        UPDATE tickets
        SET
            status = 'Closed',
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        ticket_id,
    ))

    add_history(
        connection,
        ticket_id,
        "Closed",
        "Ticket closed.",
        session["user_id"]
    )

    connection.commit()
    connection.close()

    return jsonify({
        "message":
            "Ticket closed successfully.",
        "ticket_id":
            ticket_id,
        "status":
            "Closed"
    })


# =========================================================
# START APPLICATION
# =========================================================

if __name__ == "__main__":

    create_database()

    app.run(debug=True)