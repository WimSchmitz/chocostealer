# 🎪 Pukkelpop Ticket Monitor
*Originally inspired by [@lvanroye](https://github.com/lvanroye)'s nifty little website polling system!*

A comprehensive ticket monitoring system for Pukkelpop festival that automatically checks for ticket availability and sends email notifications when tickets become available.

## 🚀 Features

- **Real-time Monitoring**: Continuously monitors the official Pukkelpop ticket website
- **Email Notifications**: Automatically sends email alerts when tickets become available
- **Multiple Interfaces**: Choose from Flask web app, Streamlit dashboard, or command-line script
- **Flexible Filtering**: Monitor specific days and camping options
- **Database Storage**: Tracks subscribers and notification history
- **Web Dashboard**: User-friendly interface for managing subscriptions

## 📋 What It Monitors

**Festival Days:**
- Day 1 (Friday)
- Day 2 (Saturday) 
- Day 3 (Sunday)
- Combi (Multi-day passes)

**Camping Options:**
- No Camping
- Camping Chill
- Camping Relax

## 🛠️ Installation

### Prerequisites
- Python 3.12+
- Poetry (for dependency management)
- Gmail account (for email notifications)

### Setup

1. **Clone the repository:**
```bash
git clone https://github.com/WimSchmitz/chocostealer.git
cd chocostealer
```

2. **Install dependencies:**

If you use poetry, you can just execute the following command:

```bash
poetry install
```

Creating your own virtual environment and installing with `pip install -r requirements.txt` is also supported.

3. **Configure environment variables:**
Create a `.env` file in the project root:
```env
EMAIL_USER="your-gmail@gmail.com"
EMAIL_PASSWORD="your-email-password"
SECRET_KEY="your-secret-key-here" # This Secret key is used internally by Flask, to protect user session data.
APP_PASSWORD="your-app" # This is the front end password that users need to enter to open the website
```

> **Note**: Use Gmail App Passwords, not your regular Gmail password. [Learn how to create an App Password](https://support.google.com/accounts/answer/185833).

4. **Activate the virtual environment:**
```bash
poetry shell
```

## 🎯 Usage

### Option 1: Flask Web Application + Background Script (Recommended)

Start the background script to start checking the website:

```bash
python chocostealer/stealer_script.py
```

And then start the web server with subscriber management:

```bash
python chocostealer/stealer_flask.py
```

Then visit:

- **Main Interface**: http://localhost:5000
- **Statistics**: http://localhost:5000/stats

**Features:**

- Subscribe/unsubscribe via web interface
- View subscriber statistics
- Automatic background monitoring
- SQLite database for data persistence

### Option 2: Streamlit Dashboard (Deprecated)

Launch the interactive monitoring dashboard:

```bash
streamlit run chocostealer/stealer_streamlit.py
```

**Features:**
- Real-time ticket availability checker
- Interactive filtering by day and camping
- Visual ticket overview
- No email notifications (view-only)

## 📊 Database Schema

The Flask application uses SQLite with the following tables:

### Subscribers
- `id`: Primary key
- `email`: Subscriber email address
- `day`: Festival day preference
- `camping`: Camping preference
- `created_at`: Subscription timestamp
- `active`: Subscription status

### Notifications
- `id`: Primary key
- `ticket_id`: Unique ticket identifier
- `subscriber_id`: Reference to subscriber
- `sent_at`: Notification timestamp

## 🔧 Configuration

### Email Settings
Configure your Gmail credentials in the `.env` file:
- `EMAIL_USER`: Your Gmail address
- `EMAIL_PASSWORD`: Your Gmail App Password

### Monitoring Intervals
- **Flask App**: Checks every 30 seconds
- **Command Script**: Checks every 5 seconds
- **Streamlit**: Manual refresh (cached for 60 seconds)

### Customization
Edit the following constants in the source files to customize behavior:
- `URL_TEMPLATE`: Pukkelpop ticket URL pattern
- `MAIL_SUBJECT_TEMPLATE`: Email subject format
- `MAIL_BODY_TEMPLATE`: Email body format

## 📁 Project Structure

```
chocostealer/
├── chocostealer/
│   ├── __init__.py
│   ├── stealer_app.py      # Flask web application
│   ├── stealer_streamlit.py # Streamlit dashboard
│   └── stealer_script.py   # Command-line script
├── pyproject.toml          # Poetry dependencies
├── .env                    # Environment variables (create this)
├── .gitignore
└── README.md
```

## 🚨 Important Notes

### Rate Limiting
- The application includes delays between requests to be respectful to the Pukkelpop servers
- Streamlit version caches results for 60 seconds
- Don't modify the delay intervals without good reason

### Email Delivery
- Uses Gmail SMTP with SSL encryption, but supports other email addresses
- Requires Gmail App Passwords (not regular passwords)
- Check spam folder if emails aren't received

### Legal Considerations
- This tool is for personal use only
- Respect the terms of service of the Pukkelpop website
- Don't abuse the monitoring frequency

## 🛡️ Security

- Environment variables are used for sensitive data
- Database and `.env` files are excluded from version control
- Email credentials are never logged or displayed

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is for educational and personal use. Please respect the terms of service of the websites being monitored.

## 👤 Author

**Wim Schmitz** - [wim@schmitz.cc](mailto:wim@schmitz.cc)

## 🙏 Acknowledgments

- Built for Pukkelpop festival ticket monitoring
- Uses BeautifulSoup for web scraping
- Flask and Streamlit for web interfaces
- SQLite for data persistence

---

**Disclaimer**: This tool is not affiliated with Pukkelpop or its official ticketing system. Use responsibly and in accordance with the website's terms of service.
