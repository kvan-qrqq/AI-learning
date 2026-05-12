# Weekly Sustainability News Automation

This guide explains how to set up the `sustainability_news_bot.py` script to run automatically every week.

## Prerequisites

1.  **Python Installed**: Ensure Python 3.6+ is installed.
2.  **Dependencies**: Install the required libraries:
    ```bash
    pip install feedparser python-dateutil
    ```
3.  **Email Configuration**:
    *   Open `sustainability_news_bot.py`.
    *   Update the `SENDER_EMAIL`, `SENDER_PASSWORD`, and `RECIPIENT_EMAIL` variables at the top of the file.
    *   **Note for Gmail users**: You must generate an [App Password](https://support.google.com/accounts/answer/185833) to use with this script; your regular login password will not work if 2FA is enabled.
    *   Uncomment the `send_email(subject, html_body)` line in the `main()` function when you are ready to send real emails.

---

## Option 1: Automate on Linux/macOS (Using Cron)

Cron is a time-based job scheduler found on most Unix-like operating systems.

1.  **Make the script executable** (optional but recommended):
    ```bash
    chmod +x /workspace/sustainability_news_bot.py
    ```
    *(Ensure the first line of your python script is `#!/usr/bin/env python3`)*

2.  **Open your Crontab editor**:
    ```bash
    crontab -e
    ```

3.  **Add a new job**:
    Add the following line to the bottom of the file to run the script every **Monday at 9:00 AM**:

    ```cron
    0 9 * * 1 cd /workspace && /usr/bin/python3 sustainability_news_bot.py >> /workspace/news_bot.log 2>&1
    ```

    *   `0 9 * * 1`: Runs at 09:00 on every Monday.
    *   `cd /workspace`: Ensures the script runs from the correct directory.
    *   `>> ...log`: Saves the output/errors to a log file for debugging.

4.  **Save and exit**. The cron job is now active.

---

## Option 2: Automate on Windows (Using Task Scheduler)

1.  **Create a Batch File**:
    Create a new file named `run_news_bot.bat` in `/workspace` with the following content:
    ```batch
    @echo off
    cd /d C:\path\to\workspace
    python sustainability_news_bot.py
    ```
    *(Replace `C:\path\to\workspace` with your actual folder path).*

2.  **Open Task Scheduler**:
    *   Press `Win + R`, type `taskschd.msc`, and hit Enter.

3.  **Create a Basic Task**:
    *   Click **Create Basic Task...** in the right panel.
    *   **Name**: "Weekly Sustainability News".
    *   **Trigger**: Select **Weekly**.
    *   **Schedule**: Choose **Monday** (or your preferred day) and set the time (e.g., 9:00 AM).
    *   **Action**: Select **Start a program**.
    *   **Program/script**: Browse and select the `run_news_bot.bat` file you created.
    *   **Finish**: Complete the wizard.

---

## Option 3: Cloud Automation (GitHub Actions) - *Recommended for Reliability*

If you don't want to rely on your local computer being turned on, you can host this on GitHub.

1.  **Push this code to a GitHub repository**.
2.  **Create a Workflow File**:
    Create a file at `.github/workflows/weekly_news.yml` in your repository:

    ```yaml
    name: Weekly Sustainability News

    on:
      schedule:
        # Runs every Monday at 09:00 UTC
        - cron: '0 9 * * 1'
      workflow_dispatch: # Allows manual triggering for testing

    jobs:
      send-news:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v3
          
          - name: Set up Python
            uses: actions/setup-python@v4
            with:
              python-version: '3.9'
              
          - name: Install dependencies
            run: |
              pip install feedparser python-dateutil
              
          - name: Run News Bot
            env:
              SENDER_EMAIL: ${{ secrets.SENDER_EMAIL }}
              SENDER_PASSWORD: ${{ secrets.SENDER_PASSWORD }}
              RECIPIENT_EMAIL: ${{ secrets.RECIPIENT_EMAIL }}
            run: python sustainability_news_bot.py
    ```

3.  **Set Secrets**:
    *   Go to your GitHub Repository -> **Settings** -> **Secrets and variables** -> **Actions**.
    *   Add `SENDER_EMAIL`, `SENDER_PASSWORD`, and `RECIPIENT_EMAIL` as New Repository Secrets.
    *   *Update your python script to read these from `os.environ` instead of hardcoding them.*
