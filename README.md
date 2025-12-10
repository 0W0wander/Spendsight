# Spendsight

A personal budget tracking service that provides insights and analytics on your spending.

## Overview

Spendsight helps you track and analyze your spending by:
- Processing CSV exports from Chase and Discover bank accounts
- Syncing transaction data to Google Sheets
- Providing intelligent insights and analytics on your spending patterns

## Features

- **CSV Import**: Upload transaction CSVs from Chase and Discover
- **Google Sheets Integration**: Automatic sync to Google Sheets for backup and manual review
- **Spending Insights**: AI-powered categorization and trend analysis
- 📉 **Analytics Dashboard**: Visual charts and spending breakdowns
- **Budget Alerts**: Track spending against categories

## Project Structure

```
Spendsight/
├── backend/
│   ├── app.py                 # Main Flask application
│   ├── config.py              # Configuration management
│   ├── parsers/               # CSV parsers for different banks
│   │   ├── chase_parser.py
│   │   └── discover_parser.py
│   ├── sheets/                # Google Sheets integration
│   │   └── sheets_client.py
│   ├── analytics/             # Analytics and insights engine
│   │   ├── categorizer.py
│   │   └── insights.py
│   └── models/                # Data models
│       └── transaction.py
├── frontend/
│   ├── static/                # CSS, JS, images
│   └── templates/             # HTML templates
├── data/                      # Local data storage
│   └── uploads/               # Uploaded CSV files
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Setup Instructions

### Prerequisites

- Python 3.8+
- Google Cloud account (for Sheets API)
- Bank account CSVs from Chase and/or Discover

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Google Sheets API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the Google Sheets API
4. Create credentials (Service Account) by navigating to `APIs & Services > Credentials` in the **top bar**.
5. **Download the JSON key file:**
   - After creating the service account, you'll see a list of service accounts
   - **Click on the service account email** (the one you just created - it ends in `.iam.gserviceaccount.com`)
   - In the service account details page, click on the **"Keys"** tab at the top
   - Click the **"Add Key"** button → Select **"Create new key"**
   - Choose **"JSON"** as the key type
   - Click **"Create"** - the JSON file will automatically download
   - **Rename the downloaded file to `credentials.json`** and move it to your Spendsight project root folder
   
   **Having trouble finding the download button?** See [GOOGLE_SHEETS_KEY_GUIDE.md](GOOGLE_SHEETS_KEY_GUIDE.md) for detailed step-by-step instructions
6. Create a Google Sheet and share it with the service account email

### 3. Configuration

Create a `.env` file in the project root:

```env
# Google Sheets Configuration
GOOGLE_SHEETS_ID=your_spreadsheet_id_here
GOOGLE_CREDENTIALS_PATH=credentials.json

# Flask Configuration
FLASK_SECRET_KEY=your_secret_key_here
FLASK_ENV=development

# Upload Configuration
UPLOAD_FOLDER=data/uploads
MAX_CONTENT_LENGTH=16777216  # 16MB
```

### 4. Run the Application

```bash
python backend/app.py
```

The application will be available at `http://localhost:5000`

## Usage

### Uploading Transactions

1. Download CSV files from your bank websites:
   - **Chase**: Go to Activity → Download
   - **Discover**: Go to Recent Activity → Download
2. Navigate to `http://localhost:5000/upload`
3. Select your bank and upload the CSV file
4. View processed transactions and insights on the dashboard

### Google Sheets Sync

Transactions are automatically synced to your Google Sheet after upload. The sheet will have tabs for:
- All Transactions
- Chase Transactions
- Discover Transactions
- Monthly Summaries
- Category Breakdowns

## CSV Format Support

### Chase
Expected columns: `Transaction Date`, `Post Date`, `Description`, `Category`, `Type`, `Amount`, `Memo`

### Discover
Expected columns: `Trans. Date`, `Post Date`, `Description`, `Amount`, `Category`

## Analytics Features

- **Category Analysis**: Spending breakdown by category
- **Trend Analysis**: Monthly spending trends
- **Merchant Analysis**: Top merchants by spending
- **Budget Tracking**: Set and monitor category budgets
- **Anomaly Detection**: Identify unusual transactions

## Future Enhancements

- [ ] Multiple bank account support
- [ ] Recurring transaction detection
- [ ] Budget recommendations
- [ ] Export reports to PDF
- [ ] Mobile app
- [ ] Receipt upload and OCR

## License

Personal use only

## Support

For issues or questions, please create an issue in this repository.

