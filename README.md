# Project 10 – Sales CRM System

A functional Customer Relationship Management application developed using Python, Flask and SQLite.

## 1. Project Overview

The Sales CRM System is a business application designed to manage customer records, monitor sales opportunities, track deal progression and analyse sales performance through a centralised dashboard.

## 2. Core Features

### Customer Management
- Create customer records.
- View and search customers.
- Edit customer information.
- Delete customer records where no associated deals exist.
- Store contact details, industry information and notes.

### Sales Pipeline
Track opportunities through six stages:
- Lead
- Qualified
- Proposal
- Negotiation
- Won
- Lost

### Deal Tracking
- Create and edit deals.
- Associate deals with customers.
- Record deal values.
- Set expected closing dates.
- Track successful and unsuccessful deals.

### Performance Dashboard
- Total customers.
- Total deals.
- Open pipeline value.
- Won revenue.
- Sales win rate.
- Recent deal activity.

### Performance Reporting
- Deal volumes by sales stage.
- Total deal value by stage.
- Customer performance.
- Won revenue by customer.

## 3. Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.13 | Application development |
| Flask 3.1.3 | Web framework |
| SQLite | Database management |
| SQL | Database queries |
| HTML | Interface structure |
| CSS | Interface styling |

All software and dependencies used are free.

## 4. Database Design

The application uses two relational database tables.

**Customers**
- Customer ID
- Company name
- Contact name
- Email
- Telephone number
- Industry
- Notes

**Deals**
- Deal ID
- Customer ID
- Deal name
- Deal value
- Sales stage
- Expected closing date
- Creation and update timestamps

A foreign key connects deals to their associated customer records.

## 5. Security Features

- Parameterised SQL queries.
- CSRF token generation and validation.
- Random application secret generation.
- HTTP-only session cookies.
- SameSite cookie configuration.
- Input validation.
- Database foreign-key constraints.
- Restrictions on negative deal values.
- Restrictions on invalid sales stages.
- Application request-size limit.

Customer deletion is restricted when associated deals exist.

The prototype does not currently include user authentication or role-based access control. Additional controls would be required before production deployment.

## 6. Functional Testing

| Test | Result |
|---|---|
| Dashboard loading | Passed |
| Customer creation | Passed |
| Customer search | Passed |
| Customer editing | Passed |
| Customer deletion protection | Passed |
| Deal creation | Passed |
| Deal editing | Passed |
| Sales pipeline progression | Passed |
| Dashboard calculations | Passed |
| Performance reporting | Passed |
| CSRF rejection | Passed |
| Negative deal value rejection | Passed |
| Invalid sales stage rejection | Passed |
| Invalid customer reference rejection | Passed |
| Main application routes | Passed |
| Customer and deal edit routes | Passed |

## 7. Demonstration Results

Test customer: Northstar Technologies Ltd.

Two sales opportunities were created.

| Deal | Value | Final Stage |
|---|---:|---|
| Enterprise CRM Transformation | £1,000,000 | Won |
| CRM Implementation Package | £4,500 | Proposal |

Verified dashboard results:

- Total customers: 1
- Total deals: 2
- Open pipeline value: £4,500
- Won revenue: £1,000,000
- Win rate: 100%

## 8. Project Structure

```text
Sales CRM System/
├── app.py
├── database.py
├── requirements.txt
├── README.md
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── customers.html
│   ├── customer_form.html
│   ├── deals.html
│   ├── deal_form.html
│   └── reports.html
├── static/
│   └── style.css
└── evidence/
## 9. Installation

1. Clone the repository.
2. Create a virtual environment:

   `python -m venv venv`

3. Activate the environment on Windows:

   `.\venv\Scripts\Activate.ps1`

4. Install dependencies:

   `pip install -r requirements.txt`

5. Start the application:

   `python app.py`

6. Open `http://127.0.0.1:5000`.

## 10. Evidence

The evidence folder contains screenshots captured during development and functional testing. These demonstrate customer management, sales pipeline progression, dashboard calculations, performance reporting and application functionality.

## 11. Future Improvements

- User authentication and role-based access.
- Advanced sales analytics.
- Visual sales pipeline charts.
- Customer activity history.
- CSV report exports.
- Suitable free hosting.

## 12. Final Project Outcome

The Sales CRM System demonstrates practical development of a functional business application using Python, Flask, HTML, CSS and SQLite.

The completed prototype supports customer management, sales pipeline tracking, deal management and performance reporting.

It also demonstrates relational database design, input validation, CSRF protection, database constraints and functional testing.

**Project Status: Functional prototype completed.**