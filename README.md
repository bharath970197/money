# MoneyFlow — Python Web Application

The MoneyFlow application is being migrated from Electron to a Python Flask web backend. The original frontend HTML, CSS and browser scripts are retained in the complete project package; the browser adapter maps the existing frontend API calls to Flask endpoints.

## Features
- Registration and login
- Income and expense tracking
- Bank account records
- AutoPay records
- Savings goals
- Admin overview

## Local setup
```powershell
py -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000.

## Deployment
A Render Blueprint (`render.yaml`) and `Procfile` are included. Review hosting resources and pricing before deploying. The JSON database requires persistent storage for data to survive service restarts/redeployments.

## Compatibility and security
Passwords use PBKDF2-HMAC-SHA512 with the same parameters as the original local database. The original Electron/Node backend is retained in `legacy-electron/` in the complete source package, but is not used by Flask. The original bank Account Aggregator integration code is also retained for reference; live integration requires valid provider credentials. Never store ATM PINs, CVVs, OTPs, UPI PINs or net-banking passwords.

The documented demo administrator is `admin@expense.local` / `admin123`; replace demo credentials before production use. Do not commit `.env` files or the local `expense-database.json`.