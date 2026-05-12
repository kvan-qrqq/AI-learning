import feedparser
import smtplib
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
RECIPIENT_EMAIL = "customer_email@example.com"

# Topics and corresponding RSS Feeds 
# Note: In a production environment, you might use a News API (like NewsAPI.org or Bing News Search)
# Here we use public RSS feeds as a free alternative.
TOPICS = {
    "Energy": [
        "https://www.reutersagency.com/feed/?best-topics=energy&post_type=best",
        "https://renewablesnow.com/feed/",
    ],
    "Waste & Circular Economy": [
        "https://www.wastedive.com/feeds/news/",
        "https://www.recyclingtoday.com/rss.aspx",
    ],
    "Water & Wastewater": [
        "https://www.waterworld.com/rss.xml",
        "https://www.wwdmag.com/rss.xml",
    ],
    "Chemicals": [
        "https://www.chemweek.com/rss",
        "https://www.chemicalwatch.com/feed",
    ],
    "Biodiversity": [
        "https://www.sciencedaily.com/rss/environment/biodiversity.xml",
        "https://news.mongabay.com/feed/",
    ],
    "Climate Change": [
        "https://www.climatecentral.org/rss",
        "https://carbonbrief.org/feed/",
    ]
}

# ================= FUNCTIONS =================

def fetch_news(topics, days_back=7):
    """Fetches news items from RSS feeds for specified topics."""
    collected_news = {topic: [] for topic in topics.keys()}
    cutoff_date = datetime.now() - timedelta(days=days_back)

    print(f"Fetching news since {cutoff_date.date()}...")

    for topic, feeds in topics.items():
        for feed_url in feeds:
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

def create_email_body(news_data):
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
            <p>Hello,</p>
            <p>Here is your weekly update on sustainability news covering Energy, Waste, Water, Chemicals, Biodiversity, and Climate.</p>
            <p><em>Report generated on: {date}</em></p>
    """.format(date=datetime.now().strftime("%Y-%m-%d"))

    total_articles = 0

    for topic, articles in news_data.items():
        if articles:
            html += f"<h2>{topic}</h2>"
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
            html += f"<h2>{topic}</h2><p>No major news found this week.</p>"

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

def send_email(subject, html_content):
    """Sends the email via SMTP."""
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECIPIENT_EMAIL

    part = MIMEText(html_content, 'html')
    msg.attach(part)

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

def main():
    # 1. Fetch News
    news_data = fetch_news(TOPICS, days_back=7)
    
    # 2. Create Content
    subject = f"Weekly Sustainability News: {datetime.now().strftime('%Y-%m-%d')}"
    html_body = create_email_body(news_data)
    
    # 3. Send Email
    # Uncomment the line below to actually send the email
    # send_email(subject, html_body)
    
    # For testing, we just print to console first
    print(f"\n--- Preview of Email Subject: {subject} ---")
    print(f"Total articles found: {sum(len(v) for v in news_data.values())}")
    for topic, items in news_data.items():
        print(f"- {topic}: {len(items)} items")

if __name__ == "__main__":
    main()
