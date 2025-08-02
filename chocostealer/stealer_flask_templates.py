
# HTML Templates
INDEX_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Pukkelpop Ticket Monitor</title>

    <!-- SEO Meta Tags -->
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Get instant email notifications when Pukkelpop tickets become available. Monitor Friday, Saturday, Sunday, and Combi passes automatically.">
    <meta name="keywords" content="Pukkelpop, tickets, monitor, notifications, festival, Belgium, music">
    
    <!-- Open Graph / Facebook -->
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://pkpchecker.eu/">
    <meta property="og:title" content="Pukkelpop Ticket Monitor">
    <meta property="og:description" content="Get instant email notifications when Pukkelpop tickets become available for any day or camping option.">
    <meta property="og:image" content="https://pkpchecker.eu/static/pukkelpop-social.png">
    <meta property="og:site_name" content="Pukkelpop Ticket Monitor">
    
    <!-- Twitter -->
    <meta property="twitter:card" content="summary_large_image">
    <meta property="twitter:title" content="Pukkelpop Ticket Monitor">
    <meta property="twitter:description" content="Get instant email notifications when Pukkelpop tickets become available.">
    <meta property="twitter:image" content="https://pkpchecker.eu/static/pukkelpop-social.png">
    
    <link rel="shortcut icon" href="{{ url_for('static', filename='favicon.ico') }}">
    
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        .form-group { margin: 15px 0; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, select { width: 100%; padding: 8px; margin-bottom: 10px; border: 1px solid #ddd; border-radius: 4px; }
        button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #0056b3; }
        .success { color: green; font-weight: bold; }
        .error { color: red; font-weight: bold; }
        .section { margin: 30px 0; padding: 20px; border: 1px solid #eee; border-radius: 8px; }
        h1 { color: #333; text-align: center; }
        h2 { color: #666; border-bottom: 2px solid #eee; padding-bottom: 10px; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f2f2f2; }
        .available { color: #28a745; font-weight: bold; }
        .no-tickets { color: #6c757d; font-style: italic; }
        .ticket-link { color: #007bff; text-decoration: none; }
        .ticket-link:hover { text-decoration: underline; }
        .logout-link { text-align: right; margin-bottom: 20px; }
        .logout-link a { color: #dc3545; text-decoration: none; }
        .logout-link a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="logout-link">
        <a href="/logout">Logout</a>
    </div>
    
    <h1>🎪 Pukkelpop Ticket Monitor</h1>
    
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
                <div class="{{ category }}">{{ message }}</div>
            {% endfor %}
        {% endif %}
    {% endwith %}
    
    <div class="section">
        <h2>Currently Available Tickets</h2>
        {% if current_tickets_overview %}
        <table>
            <thead>
                <tr>
                    <th>Day</th>
                    <th>Camping</th>
                    <th>Available</th>
                    <th>Lowest Price</th>
                    <th>Link</th>
                </tr>
            </thead>
            <tbody>
                {% for day, camping, count, lowest_price, url in current_tickets_overview %}
                <tr>
                    <td>{{ days[day] }}</td>
                    <td>{{ campings[camping] }}</td>
                    <td class="available">{{ count }} tickets</td>
                    <td>{{ lowest_price or 'N/A' }}</td>
                    <td><a href="{{ url }}" target="_blank" class="ticket-link">View Tickets</a></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <p class="no-tickets">No tickets currently available. Subscribe below to get notified when they become available!</p>
        {% endif %}
    </div>
    
    <div class="section">
        <h2>Subscribe for Ticket Alerts</h2>
        <form method="POST" action="/subscribe">
            <div class="form-group">
                <label for="email">Email:</label>
                <input type="email" name="email" required>
            </div>
            
            <div class="form-group">
                <label for="day">Day:</label>
                <select name="day" required>
                    <option value="">Select Day</option>
                    {% for key, value in days.items() %}
                        <option value="{{ key }}">{{ value }}</option>
                    {% endfor %}
                </select>
            </div>
            
            <div class="form-group">
                <label for="camping">Camping:</label>
                <select name="camping" required>
                    <option value="">Select Camping</option>
                    {% for key, value in campings.items() %}
                        <option value="{{ key }}">{{ value }}</option>
                    {% endfor %}
                    <option value="all">All</option>
                </select>
            </div>
            
            <button type="submit">Subscribe</button>
        </form>
    </div>
    
    <div class="section">
        <h2>Unsubscribe</h2>
        <form method="POST" action="/unsubscribe">
            <div class="form-group">
                <label for="email">Email:</label>
                <input type="email" name="email" required>
            </div>
            <button type="submit">Unsubscribe</button>
        </form>
    </div>
    
    <div style="text-align: center; margin-top: 30px;">
        <a href="/stats">View Statistics</a>
    </div>
</body>
</html>
'''

STATS_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Pukkelpop Monitor - Stats</title>
        
    <link rel="shortcut icon" href="{{ url_for('static', filename='favicon.ico') }}">

    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f2f2f2; }
        h1 { color: #333; text-align: center; }
        h2 { color: #666; border-bottom: 2px solid #eee; padding-bottom: 10px; }
        .back-link { text-align: center; margin: 20px 0; }
        .logout-link { text-align: right; margin-bottom: 20px; }
        .logout-link a { color: #dc3545; text-decoration: none; }
        .logout-link a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="logout-link">
        <a href="/logout">Logout</a>
    </div>
    
    <h1>📊 Pukkelpop Monitor Statistics</h1>
    
    <h2>Active Subscribers</h2>
    <table>
        <thead>
            <tr>
                <th>Day</th>
                <th>Subscribers</th>
            </tr>
        </thead>
        <tbody>
            {% for day, count in stats %}
            <tr>
                <td>{{ days[day] }}</td>
                <td>{{ count }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    
    <h2>Recent Notifications</h2>
    <table>
        <thead>
            <tr>
                <th>Ticket ID</th>
                <th>Subscriber ID</th>
                <th>Sent At</th>
            </tr>
        </thead>
        <tbody>
            {% for ticket_id, subscriber_id, sent_at in notifications %}
            <tr>
                <td>{{ ticket_id }}</td>
                <td>{{ subscriber_id }}</td>
                <td>{{ sent_at }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    
    <div class="back-link">
        <a href="/">← Back to Home</a>
    </div>
</body>
</html>
'''

LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Pukkelpop Ticket Monitor</title>

    <!-- SEO Meta Tags -->
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Get instant email notifications when Pukkelpop tickets become available. Monitor Friday, Saturday, Sunday, and Combi passes automatically.">
    <meta name="keywords" content="Pukkelpop, tickets, monitor, notifications, festival, Belgium, music">
    
    <!-- Open Graph / Facebook -->
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://pkpchecker.eu/">
    <meta property="og:title" content="Pukkelpop Ticket Monitor">
    <meta property="og:description" content="Get instant email notifications when Pukkelpop tickets become available for any day or camping option.">
    <meta property="og:image" content="https://pkpchecker.eu/static/pukkelpop-social.png">
    <meta property="og:site_name" content="Pukkelpop Ticket Monitor">
    
    <!-- Twitter -->
    <meta property="twitter:card" content="summary_large_image">
    <meta property="twitter:title" content="Pukkelpop Ticket Monitor">
    <meta property="twitter:description" content="Get instant email notifications when Pukkelpop tickets become available.">
    <meta property="twitter:image" content="https://pkpchecker.eu/static/pukkelpop-social.png">
    
    <link rel="shortcut icon" href="{{ url_for('static', filename='favicon.ico') }}">
    
    <style>
        body { 
            font-family: Arial, sans-serif; 
            max-width: 400px; 
            margin: 100px auto; 
            padding: 20px; 
            background-color: #f8f9fa;
        }
        .login-container { 
            background: white; 
            padding: 40px; 
            border-radius: 8px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 { 
            color: #333; 
            text-align: center; 
            margin-bottom: 30px;
        }
        .form-group { 
            margin: 20px 0; 
        }
        label { 
            display: block; 
            margin-bottom: 5px; 
            font-weight: bold; 
            color: #555;
        }
        input[type="password"] { 
            width: 100%; 
            padding: 12px; 
            border: 1px solid #ddd; 
            border-radius: 4px; 
            font-size: 16px;
            box-sizing: border-box;
        }
        button { 
            width: 100%;
            background: #007bff; 
            color: white; 
            padding: 12px; 
            border: none; 
            border-radius: 4px; 
            cursor: pointer; 
            font-size: 16px;
            margin-top: 10px;
        }
        button:hover { 
            background: #0056b3; 
        }
        .error { 
            color: #dc3545; 
            font-weight: bold; 
            text-align: center;
            margin-bottom: 20px;
        }
        .success { 
            color: #28a745; 
            font-weight: bold; 
            text-align: center;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <h1>🎪 Pukkelpop Monitor</h1>
        <h2 style="text-align: center; color: #666; margin-bottom: 30px;">Please Login</h2>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <form method="POST">
            <div class="form-group">
                <label for="password">Password:</label>
                <input type="password" name="password" required autofocus>
            </div>
            <button type="submit">Login</button>
        </form>
    </div>
</body>
</html>
'''