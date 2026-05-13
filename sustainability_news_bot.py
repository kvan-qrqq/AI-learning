import feedparser
import smtplib
import csv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import os
from dateutil import parser as date_parser

# ================= CONFIGURATION =================
# Replace these with your actual details
SMTP_SERVER = "smtp.gmail.com"  # e.g., smtp.gmail.com for Gmail
SMTP_PORT = 587
SENDER_EMAIL = "your_email@gmail.com"
SENDER_PASSWORD = "your_app_password"  # Use an App Password, not your main password

# Default RSS Feeds (used if customer doesn't specify custom links)
DEFAULT_FEEDS = {
    "energy": [
        "https://www.reutersagency.com/feed/?best-topics=energy&post_type=best",
        "https://renewablesnow.com/feed/",
    ],
    "waste": [
        "https://www.wastedive.com/feeds/news/",
        "https://www.recyclingtoday.com/rss.aspx",
    ],
    "wastewater": [
        "https://www.waterworld.com/rss.xml",
        "https://www.wwdmag.com/rss.xml",
    ],
    "chemical": [
        "https://www.chemweek.com/rss",
        "https://www.chemicalwatch.com/feed",
    ],
    "biodiversity": [
        "https://www.sciencedaily.com/rss/environment/biodiversity.xml",
        "https://news.mongabay.com/feed/",
    ],
    "climate": [
        "https://www.climatecentral.org/rss",
        "https://carbonbrief.org/feed/",
    ]
}

CUSTOMER_FILE = "customers.csv"

# ================= FUNCTIONS =================

def load_customers():
    """Loads customer data from the CSV file."""
    customers = []
    if not os.path.exists(CUSTOMER_FILE):
        print(f"Error: {CUSTOMER_FILE} not found.")
        return customers
    
    with open(CUSTOMER_FILE, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            customers.append({
                "name": row['customer_name'],
                "email": row['customer_email'],
                "topics": [t.strip().lower() for t in row['customer_topics'].split(',')],
                "links": [l.strip() for l in row['customer_web_links'].split(',')] if row['customer_web_links'] else []
            })
    return customers

def get_feeds_for_customer(topics, links):
    """Determines which RSS feeds to use based on customer topics and custom links."""
    selected_feeds = {}
    
    # If customer provided custom links, use those directly mapped to their requested topics
    if links:
        # Assign custom links to the first topic requested, or create a generic bucket
        # For simplicity, we map the custom links to the topics they requested.
        # Note: RSS feeds usually cover specific topics. If they provide a link, we assume it's relevant.
        # We will treat custom links as the primary source for the requested topics.
        for topic in topics:
            selected_feeds[topic] = links
    else:
        # Otherwise, use default feeds for the requested topics
        for topic in topics:
            if topic in DEFAULT_FEEDS:
                selected_feeds[topic] = DEFAULT_FEEDS[topic]
            else:
                print(f"Warning: No default feed found for topic '{topic}'.")
                
    return selected_feeds

def fetch_news(feeds_dict, days_back=7):
    """Fetches news items from RSS feeds for specified topics."""
    collected_news = {topic: [] for topic in feeds_dict.keys()}
    cutoff_date = datetime.now() - timedelta(days=days_back)

    print(f"Fetching news since {cutoff_date.date()}...")

    for topic, feed_urls in feeds_dict.items():
        for feed_url in feed_urls:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries:
                    # Parse date safely
                    published = None
                    if hasattr(entry, 'published'):
                        try:
                            published = date_parser.parse(entry.published)
                        except Exception:
                            continue
                    
                    # Filter by date
                    if published and published > cutoff_date:
                        collected_news[topic].append({
                            "title": entry.title,
                            "link": entry.link,
                            "date": published.strftime("%Y-%m-%d"),
                            "summary": entry.get('summary', '')[:150] + "..." # Shorten summary
                        })
            except Exception as e:
                print(f"Error fetching {feed_url}: {e}")
    
    return collected_news

def create_email_body(news_data, customer_name):
    """Generates an HTML email body."""
    html = """
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 800px; margin: 0 auto; padding: 20px; }
            h1 { color: #2c7a4b; border-bottom: 2px solid #2c7a4b; padding-bottom: 10px; }
            h2 { color: #2c7a4b; margin-top: 30px; }
            .news-item { margin-bottom: 15px; background: #f9f9f9; padding: 10px; border-radius: 5px; }
            .news-title { font-weight: bold; font-size: 16px; }
            .news-date { font-size: 12px; color: #666; }
            .news-link { text-decoration: none; color: #2c7a4b; }
            footer { margin-top: 40px; font-size: 12px; color: #888; text-align: center; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Weekly Sustainability Digest</h1>
            <p>Hello {customer},</p>
            <p>Here is your weekly update on sustainability news covering your selected topics.</p>
            <p><em>Report generated on: {date}</em></p>
    """.format(customer=customer_name, date=datetime.now().strftime("%Y-%m-%d"))

    total_articles = 0

    for topic, articles in news_data.items():
        if articles:
            # Capitalize topic for display
            display_topic = topic.capitalize()
            html += f"<h2>{display_topic}</h2>"
            for item in articles[:5]:  # Limit to top 5 per topic to keep email concise
                total_articles += 1
                html += """
                <div class="news-item">
                    <div class="news-title"><a href="{link}" class="news-link">{title}</a></div>
                    <div class="news-date">{date}</div>
                    <div>{summary}</div>
                </div>
                """.format(
                    link=item['link'],
                    title=item['title'],
                    date=item['date'],
                    summary=item['summary']
                )
        else:
            display_topic = topic.capitalize()
            html += f"<h2>{display_topic}</h2><p>No major news found this week.</p>"

    if total_articles == 0:
        html += "<p><strong>Note:</strong> No new articles were found in the selected feeds for this period.</p>"

    html += """
            <footer>
                <p>This is an automated newsletter generated by your Sustainability Bot.</p>
            </footer>
        </div>
    </body>
    </html>
    """
    return html

def send_email(recipient_email, subject, html_content):
    """Sends the email via SMTP."""
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = recipient_email

    part = MIMEText(html_content, 'html')
    msg.attach(part)

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        print(f"Email sent successfully to {recipient_email}!")
    except Exception as e:
        print(f"Failed to send email to {recipient_email}: {e}")

def main():
    # 1. Load Customers
    customers = load_customers()
    if not customers:
        print("No customers found. Exiting.")
        return

    print(f"Processing {len(customers)} customers...")

    for customer in customers:
        print(f"\n--- Processing: {customer['name']} ({customer['email']}) ---")
        
        # 2. Determine Feeds
        feeds_to_use = get_feeds_for_customer(customer['topics'], customer['links'])
        
        if not feeds_to_use:
            print(f"No valid feeds found for {customer['name']}. Skipping.")
            continue

        # 3. Fetch News
        news_data = fetch_news(feeds_to_use, days_back=7)
        
        # 4. Create Content
        subject = f"Weekly Sustainability News: {datetime.now().strftime('%Y-%m-%d')}"
        html_body = create_email_body(news_data, customer['name'])
        
        # 5. Send Email
        # Uncomment the line below to actually send the email
        send_email(customer['email'], subject, html_body)
        
        # For testing without sending, you can uncomment these lines instead:
        # print(f"Preview of Email Subject: {subject}")
        # print(f"Total articles found: {sum(len(v) for v in news_data.values())}")

if __name__ == "__main__":
    main()
