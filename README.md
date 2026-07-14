# Spendsight

**Spending analyzer for Chase, Discover, and TD Bank transactions with Google Sheets sync.**

Spendsight helps you understand where your money goes by importing bank CSV exports, categorizing transactions with customizable rules, and visualizing your spending patterns.

## Demo

[Watch the demo video](https://youtu.be/rww2Yisol34)

---

## Features

### Interactive Dashboard

- **Clickable pie chart** and **line chart** with category breakdowns
- Filter by category, necessity, frequency, or any combination
- Sort transactions by amount or date
- **Movable timeframe view** - switch between days, weeks, months, or years



### Smart Auto-Tagging

- Create keyword-based rules to automatically tag transactions
- **Three tag dimensions**: Category, Necessity (Needs/Wants/Savings), Frequency (One-time/Recurring/Subscription)
- **Sweep rules** to auto-remove unwanted transactions (transfers, duplicates, etc.)



### Budget Mode

- Set weekly or monthly spending budgets
- Add personal analysis notes for each time period
- Track spending against your goals



### Google Sheets Sync

- All transactions backed up to your Google Sheet
- Built-in setup wizard with step-by-step guide
- Sync button in navigation for manual updates



### Desktop App

- Runs in system tray (Windows)
- Single executable - no installation needed
- Auto-opens browser on launch

---



## Supported Banks


| Bank     | Format                      |
| -------- | --------------------------- |
| Chase    | Credit Card, Checking/Debit |
| Discover | Credit Card                 |
| TD Bank  | Checking, Credit Card       |


---



## Quick Start



### Option 1: Run from Source

```bash
py -3.11 -m pip install -r requirements.txt
py -3.11 run.py
```



### Option 2: Download Executable

Download `Spendsight.exe` from [Releases](../../releases) and run it.

---



## Setup Guide

1. **Run Spendsight** - the setup wizard opens automatically
2. **Create a Google Sheet** and copy the Sheet ID from the URL
3. **Create a Service Account** in Google Cloud Console
4. **Download credentials.json** and upload it in the wizard
5. **Share your Sheet** with the service account email
6. **Done!** Upload your first CSV

---



## Getting Bank Transactions



### Chase

1. Log into chase.com
2. Go to your account → Activity
3. Click "Download" → Select date range → Download CSV



### Discover

1. Log into discover.com
2. Go to Statements & Activity
3. Click "Export" → Select date range → Download CSV



### TD Bank

1. Log into TD Bank online banking
2. Open your checking or credit card account
3. Go to Account Activity / transaction history
4. Choose your date range → Download CSV
5. Tip: include "checking" or "credit" in the filename so account type is detected correctly

---



## Build from Source

```bash
pyinstaller run.spec
```

The executable will be in the `dist/` folder.

---



## License

MIT