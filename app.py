import os
import secrets
import sqlite3
import math
from datetime import date
from decimal import Decimal, InvalidOperation

from flask import (
    Flask, render_template, request,
    redirect, url_for, flash, session, abort
)

from database import get_db_connection, initialize_database


app = Flask(__name__)

app.config["SECRET_KEY"] = (
    os.environ.get("SECRET_KEY") or secrets.token_hex(32)
)
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

STAGES = (
    "Lead",
    "Qualified",
    "Proposal",
    "Negotiation",
    "Won",
    "Lost"
)


# -----------------------------
# Security and validation
# -----------------------------

@app.context_processor
def inject_security_token():
    session.setdefault("csrf_token", secrets.token_urlsafe(32))
    return {"csrf_token": session["csrf_token"]}


@app.before_request
def protect_post_requests():
    if request.method == "POST":
        submitted = request.form.get("csrf_token", "")
        expected = session.get("csrf_token", "")

        if not expected or not secrets.compare_digest(
            submitted, expected
        ):
            abort(400)


def clean_text(value, max_length=255):
    value = (value or "").strip()

    if len(value) > max_length:
        raise ValueError(
            f"Text must not exceed {max_length} characters."
        )

    return value


def validate_money(value):
    try:
        amount = Decimal((value or "").strip())
    except (InvalidOperation, ValueError):
        raise ValueError("Enter a valid deal value.")

    if not amount.is_finite() or amount < 0:
        raise ValueError("Deal value must be a valid non-negative amount.")

    if amount > Decimal("999999999"):
        raise ValueError("Deal value is too large.")

    return float(amount)


def validate_date(value):
    value = (value or "").strip()

    if not value:
        return None

    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        raise ValueError("Enter a valid closing date.")


# -----------------------------
# Dashboard
# -----------------------------

@app.route("/")
def dashboard():
    connection = get_db_connection()

    try:
        customers = connection.execute(
            "SELECT COUNT(*) FROM customers"
        ).fetchone()[0]

        deals = connection.execute(
            "SELECT COUNT(*) FROM deals"
        ).fetchone()[0]

        pipeline = connection.execute("""
            SELECT COALESCE(SUM(deal_value), 0)
            FROM deals
            WHERE stage NOT IN ('Won', 'Lost')
        """).fetchone()[0]

        revenue = connection.execute("""
            SELECT COALESCE(SUM(deal_value), 0)
            FROM deals
            WHERE stage = 'Won'
        """).fetchone()[0]

        closed = connection.execute("""
            SELECT
                SUM(CASE WHEN stage = 'Won' THEN 1 ELSE 0 END),
                SUM(CASE WHEN stage IN ('Won', 'Lost') THEN 1 ELSE 0 END)
            FROM deals
        """).fetchone()

        won = closed[0] or 0
        closed_total = closed[1] or 0

        win_rate = (
            (won / closed_total) * 100
            if closed_total else 0
        )

        recent_deals = connection.execute("""
            SELECT
                deals.*,
                customers.company_name
            FROM deals
            JOIN customers
                ON deals.customer_id = customers.id
            ORDER BY deals.created_at DESC
            LIMIT 5
        """).fetchall()

        return render_template(
            "dashboard.html",
            customers=customers,
            deals=deals,
            pipeline=pipeline,
            revenue=revenue,
            win_rate=round(win_rate, 1),
            recent_deals=recent_deals
        )

    finally:
        connection.close()


# -----------------------------
# Customer management
# -----------------------------

@app.route("/customers")
def customers():
    search = request.args.get("search", "").strip()

    connection = get_db_connection()

    try:
        records = connection.execute("""
            SELECT
                customers.*,
                COUNT(deals.id) AS deal_count
            FROM customers
            LEFT JOIN deals
                ON customers.id = deals.customer_id
            WHERE
                customers.company_name LIKE ?
                OR customers.contact_name LIKE ?
                OR customers.email LIKE ?
            GROUP BY customers.id
            ORDER BY customers.created_at DESC
        """, (
            f"%{search}%",
            f"%{search}%",
            f"%{search}%"
        )).fetchall()

        return render_template(
            "customers.html",
            customers=records,
            search=search
        )

    finally:
        connection.close()


@app.route("/customers/new", methods=["GET", "POST"])
def add_customer():
    if request.method == "POST":
        try:
            company = clean_text(
                request.form.get("company_name"), 150
            )
            contact = clean_text(
                request.form.get("contact_name"), 150
            )
            email = clean_text(
                request.form.get("email"), 254
            )
            phone = clean_text(
                request.form.get("phone"), 40
            )
            industry = clean_text(
                request.form.get("industry"), 100
            )
            notes = clean_text(
                request.form.get("notes"), 2000
            )

            if not company or not contact:
                raise ValueError(
                    "Company name and contact name are required."
                )

            if email and ("@" not in email or " " in email):
                raise ValueError("Enter a valid email address.")

            connection = get_db_connection()

            try:
                connection.execute("""
                    INSERT INTO customers
                    (company_name, contact_name, email, phone, industry, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    company, contact, email,
                    phone, industry, notes
                ))

                connection.commit()

            finally:
                connection.close()

            flash("Customer added successfully.", "success")
            return redirect(url_for("customers"))

        except ValueError as error:
            flash(str(error), "error")

    return render_template("customer_form.html", customer=None)


@app.route("/customers/<int:customer_id>/edit", methods=["GET", "POST"])
def edit_customer(customer_id):
    connection = get_db_connection()

    try:
        customer = connection.execute(
            "SELECT * FROM customers WHERE id = ?",
            (customer_id,)
        ).fetchone()

        if customer is None:
            abort(404)

        if request.method == "POST":
            try:
                company = clean_text(
                    request.form.get("company_name"), 150
                )
                contact = clean_text(
                    request.form.get("contact_name"), 150
                )
                email = clean_text(
                    request.form.get("email"), 254
                )
                phone = clean_text(
                    request.form.get("phone"), 40
                )
                industry = clean_text(
                    request.form.get("industry"), 100
                )
                notes = clean_text(
                    request.form.get("notes"), 2000
                )

                if not company or not contact:
                    raise ValueError(
                        "Company name and contact name are required."
                    )

                if email and ("@" not in email or " " in email):
                    raise ValueError("Enter a valid email address.")

                connection.execute("""
                    UPDATE customers
                    SET company_name = ?,
                        contact_name = ?,
                        email = ?,
                        phone = ?,
                        industry = ?,
                        notes = ?
                    WHERE id = ?
                """, (
                    company, contact, email,
                    phone, industry, notes, customer_id
                ))

                connection.commit()

                flash("Customer updated successfully.", "success")
                return redirect(url_for("customers"))

            except ValueError as error:
                flash(str(error), "error")

        return render_template(
            "customer_form.html",
            customer=customer
        )

    finally:
        connection.close()


@app.route("/customers/<int:customer_id>/delete", methods=["POST"])
def delete_customer(customer_id):
    connection = get_db_connection()

    try:
        connection.execute(
            "DELETE FROM customers WHERE id = ?",
            (customer_id,)
        )
        connection.commit()

        flash("Customer deleted successfully.", "success")

    except sqlite3.IntegrityError:
        connection.rollback()
        flash(
            "This customer has deals linked to their record. "
            "Remove or reassign those deals before deleting the customer.",
            "error"
        )

    finally:
        connection.close()

    return redirect(url_for("customers"))


# -----------------------------
# Deal management
# -----------------------------

@app.route("/deals")
def deals():
    connection = get_db_connection()

    try:
        records = connection.execute("""
            SELECT
                deals.*,
                customers.company_name
            FROM deals
            JOIN customers
                ON deals.customer_id = customers.id
            ORDER BY deals.created_at DESC
        """).fetchall()

        return render_template(
            "deals.html",
            deals=records
        )

    finally:
        connection.close()


@app.route("/deals/new", methods=["GET", "POST"])
def add_deal():
    connection = get_db_connection()

    try:
        customer_list = connection.execute("""
            SELECT id, company_name
            FROM customers
            ORDER BY company_name
        """).fetchall()

        if request.method == "POST":
            try:
                customer_id = int(
                    request.form.get("customer_id", "")
                )

                customer = connection.execute(
                    "SELECT id FROM customers WHERE id = ?",
                    (customer_id,)
                ).fetchone()

                if customer is None:
                    raise ValueError("Select a valid customer.")

                name = clean_text(
                    request.form.get("deal_name"), 150
                )

                if not name:
                    raise ValueError("Deal name is required.")

                value = validate_money(
                    request.form.get("deal_value")
                )

                stage = request.form.get("stage", "")

                if stage not in STAGES:
                    raise ValueError("Select a valid sales stage.")

                closing_date = validate_date(
                    request.form.get("expected_close_date")
                )

                connection.execute("""
                    INSERT INTO deals (
                        customer_id,
                        deal_name,
                        deal_value,
                        stage,
                        expected_close_date
                    )
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    customer_id,
                    name,
                    value,
                    stage,
                    closing_date
                ))

                connection.commit()

                flash("Deal created successfully.", "success")
                return redirect(url_for("deals"))

            except (ValueError, TypeError):
                connection.rollback()
                flash("Check the deal details and try again.", "error")

        return render_template(
            "deal_form.html",
            deal=None,
            customers=customer_list,
            stages=STAGES
        )

    finally:
        connection.close()


@app.route("/deals/<int:deal_id>/edit", methods=["GET", "POST"])
def edit_deal(deal_id):
    connection = get_db_connection()

    try:
        deal = connection.execute(
            "SELECT * FROM deals WHERE id = ?",
            (deal_id,)
        ).fetchone()

        if deal is None:
            abort(404)

        customer_list = connection.execute("""
            SELECT id, company_name
            FROM customers
            ORDER BY company_name
        """).fetchall()

        if request.method == "POST":
            try:
                customer_id = int(
                    request.form.get("customer_id", "")
                )

                customer = connection.execute(
                    "SELECT id FROM customers WHERE id = ?",
                    (customer_id,)
                ).fetchone()

                if customer is None:
                    raise ValueError("Select a valid customer.")

                name = clean_text(
                    request.form.get("deal_name"), 150
                )

                if not name:
                    raise ValueError("Deal name is required.")

                value = validate_money(
                    request.form.get("deal_value")
                )

                stage = request.form.get("stage", "")

                if stage not in STAGES:
                    raise ValueError("Select a valid sales stage.")

                closing_date = validate_date(
                    request.form.get("expected_close_date")
                )

                connection.execute("""
                    UPDATE deals
                    SET customer_id = ?,
                        deal_name = ?,
                        deal_value = ?,
                        stage = ?,
                        expected_close_date = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    customer_id,
                    name,
                    value,
                    stage,
                    closing_date,
                    deal_id
                ))

                connection.commit()

                flash("Deal updated successfully.", "success")
                return redirect(url_for("deals"))

            except (ValueError, TypeError) as error:
                connection.rollback()
                flash(str(error) or "Check the deal details.", "error")

        return render_template(
            "deal_form.html",
            deal=deal,
            customers=customer_list,
            stages=STAGES
        )

    finally:
        connection.close()


@app.route("/deals/<int:deal_id>/delete", methods=["POST"])
def delete_deal(deal_id):
    connection = get_db_connection()

    try:
        connection.execute(
            "DELETE FROM deals WHERE id = ?",
            (deal_id,)
        )
        connection.commit()

        flash("Deal deleted successfully.", "success")

    finally:
        connection.close()

    return redirect(url_for("deals"))


# -----------------------------
# Performance reporting
# -----------------------------

@app.route("/reports")
def reports():
    connection = get_db_connection()

    try:
        performance = connection.execute("""
            SELECT
                stage,
                COUNT(*) AS deal_count,
                COALESCE(SUM(deal_value), 0) AS total_value
            FROM deals
            GROUP BY stage
            ORDER BY CASE stage
                WHEN 'Lead' THEN 1
                WHEN 'Qualified' THEN 2
                WHEN 'Proposal' THEN 3
                WHEN 'Negotiation' THEN 4
                WHEN 'Won' THEN 5
                WHEN 'Lost' THEN 6
            END
        """).fetchall()

        top_customers = connection.execute("""
            SELECT
                customers.company_name,
                COUNT(deals.id) AS deal_count,
                COALESCE(SUM(
                    CASE WHEN deals.stage = 'Won'
                    THEN deals.deal_value ELSE 0 END
                ), 0) AS won_value
            FROM customers
            LEFT JOIN deals
                ON customers.id = deals.customer_id
            GROUP BY customers.id
            ORDER BY won_value DESC
            LIMIT 10
        """).fetchall()

        return render_template(
            "reports.html",
            performance=performance,
            top_customers=top_customers
        )

    finally:
        connection.close()


# -----------------------------
# Application startup
# -----------------------------

@app.errorhandler(400)
def bad_request(error):
    return "Bad request. Please refresh the page and try again.", 400


@app.errorhandler(404)
def not_found(error):
    return "The requested record or page was not found.", 404


if __name__ == "__main__":
    initialize_database()
    app.run(host="127.0.0.1", port=5000, debug=False)
