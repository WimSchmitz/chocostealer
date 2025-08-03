"""
Pukkelpop Ticket Monitor with Flask Web Interface
Run with: python stealer_app.py
"""

import sqlite3
from datetime import datetime, timezone
from flask import (
    Flask,
    render_template_string,
    request,
    redirect,
    send_from_directory,
    url_for,
    flash,
    session,
)
import logging
from . import config
from . import stealer_flask_templates as templates

# Logger setup
logger = logging.getLogger("chocostealer")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

app = Flask(__name__)
app.secret_key = config.APP_SECRET_KEY


def get_subscribers(day=None, camping=None):
    conn = sqlite3.connect(config.DATABASE_NAME)
    cursor = conn.cursor()

    if day and camping:
        cursor.execute(
            """
            SELECT email FROM subscribers 
            WHERE day = ? AND camping = ? AND active = 1
        """,
            (day, camping),
        )
    else:
        cursor.execute("SELECT * FROM subscribers WHERE active = 1")

    results = cursor.fetchall()
    conn.close()
    return results


def add_subscriber(email, day, camping):
    conn = sqlite3.connect(config.DATABASE_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO subscribers (email, day, camping) 
            VALUES (?, ?, ?)
        """,
            (email, day, camping),
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False  # Email already exists


def remove_subscriber(email):
    conn = sqlite3.connect(config.DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE subscribers SET active = 0 WHERE email = ?", (email,))
    conn.commit()
    conn.close()


def get_notified_tickets():
    conn = sqlite3.connect(config.DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT ticket_id FROM notifications")
    results = {row[0] for row in cursor.fetchall()}
    conn.close()
    return results


def get_current_tickets_overview():
    """Get a list of currently available tickets, grouped by day and camping, showing count and lowest price."""
    conn = sqlite3.connect(config.DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT 
            day,
            camping,
            COUNT(*) as ticket_count,
            MIN(price) as lowest_price,
            (SELECT url 
            FROM tickets t2 
            WHERE t2.day = t1.day 
            AND t2.camping = t1.camping 
            AND t2.price = (SELECT MIN(price) 
                            FROM tickets t3 
                            WHERE t3.day = t1.day 
                                AND t3.camping = t1.camping)
            LIMIT 1) as url
        FROM tickets t1
        GROUP BY day, camping
        ORDER BY day, camping
    """
    )
    results = cursor.fetchall()
    conn.close()
    return results

def get_last_refreshed():
    """Get the last time tickets were refreshed."""
    conn = sqlite3.connect(config.DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(created_at) FROM tickets")
    result = cursor.fetchone()[0]
    conn.close()

    if result:
        last_utc = datetime.fromisoformat(result).replace(tzinfo=timezone.utc)
        now_utc = datetime.now(timezone.utc)
        delta = now_utc - last_utc

        seconds = int(delta.total_seconds())
        if seconds < 60:
            return f"{seconds} seconds ago"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            hours = seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
    else:
        return None

# Password protection decorator
def require_password(f):
    def decorated_function(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    decorated_function.__name__ = f.__name__
    return decorated_function


# Flask routes
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password")
        if password == config.APP_PASSWORD:
            session["authenticated"] = True
            return redirect(url_for("index"))
        else:
            flash("Incorrect password", "error")

    return render_template_string(templates.LOGIN_TEMPLATE)


@app.route("/logout")
def logout():
    session.pop("authenticated", None)
    flash("You have been logged out", "success")
    return redirect(url_for("login"))

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route("/")
@require_password
def index():
    current_tickets_overview = get_current_tickets_overview()
    last_refreshed = get_last_refreshed()
    return render_template_string(
        templates.INDEX_TEMPLATE,
        days=config.DAYS,
        campings=config.CAMPINGS,
        current_tickets_overview=current_tickets_overview,
        last_refreshed=last_refreshed
    )


@app.route("/subscribe", methods=["POST"])
@require_password
def subscribe():
    email = request.form.get("email")
    day = request.form.get("day")
    camping = request.form.get("camping")

    if not email or not day or not camping:
        flash("Please fill in all fields", "error")
        return redirect(url_for("index"))

    if camping == "all":
        if all(add_subscriber(email, day, c) for c in config.CAMPINGS.keys()):
            flash(
                f"Successfully subscribed {email} for {config.DAYS[day]} with all campings!",
                "success",
            )
    else:
        if add_subscriber(email, day, camping):
            flash(
                f"Successfully subscribed {email} for {config.DAYS[day]} with {config.CAMPINGS[camping]}!",
                "success",
            )

    return redirect(url_for("index"))


@app.route("/unsubscribe", methods=["POST"])
@require_password
def unsubscribe():
    email = request.form.get("email")

    if not email:
        flash("Please enter your email", "error")
        return redirect(url_for("index"))

    remove_subscriber(email)
    flash(f"Successfully unsubscribed {email}", "success")
    return redirect(url_for("index"))


@app.route("/stats")
@require_password
def stats():
    conn = sqlite3.connect(config.DATABASE_NAME)
    cursor = conn.cursor()

    # Get subscriber stats
    cursor.execute(
        """
        SELECT day, COUNT(DISTINCT email) as count
        FROM subscribers 
        WHERE active = 1 
        GROUP BY day
    """
    )
    subscriber_stats = cursor.fetchall()

    # Get recent notifications
    cursor.execute(
        """
        SELECT ticket_id, subscriber_id, sent_at 
        FROM notifications 
        ORDER BY sent_at DESC 
        LIMIT 10
    """
    )
    recent_notifications = cursor.fetchall()

    conn.close()

    return render_template_string(
        templates.STATS_TEMPLATE,
        stats=subscriber_stats,
        notifications=recent_notifications,
        days=config.DAYS,
        campings=config.CAMPINGS,
    )


if __name__ == "__main__":
    # Start Flask app
    print("Starting Pukkelpop Ticket Monitor...")
    print("Web interface: http://localhost:5000")
    print("Statistics: http://localhost:5000/stats")

    app.run(host="0.0.0.0", port=5000, debug=False)
