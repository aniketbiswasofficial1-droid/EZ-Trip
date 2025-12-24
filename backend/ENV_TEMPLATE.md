# Backend Environment Variables
# Copy this file to .env and fill in your actual values

# Google OAuth Configuration
GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Microsoft Outlook/Office 365 Email Configuration
# Use your Outlook/Office 365 email credentials
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USE_TLS=True
SMTP_USERNAME=your_email@outlook.com
SMTP_PASSWORD=yourpassword
EMAIL_FROM_ADDRESS=EZ Trip <your_email@outlook.com>
EMAIL_FROM_NAME=EZ Trip

# Alternative: If using Gmail instead
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USE_TLS=True
# SMTP_USERNAME=your_email@gmail.com
# SMTP_PASSWORD=your_gmail_app_password
# EMAIL_FROM_ADDRESS=EZ Trip <your_email@gmail.com>

# Database
MONGODB_URI=mongodb://localhost:27017/test_database

# Other settings (if needed)
CORS_ORIGINS=http://localhost:3000
