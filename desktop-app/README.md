# MoneyFlow Desktop (Electron)

This folder preserves the Electron desktop runtime separately from the Flask web deployment.

## Run locally

1. Install Node.js.
2. From this folder run `npm install`.
3. Place the shared application UI under the repository `src/` directory.
4. Run `npm start`.

The hosted website continues to run through the Flask application at the repository root. Electron is a desktop runtime and is not launched by Render's web service.

Do not commit real credentials, local user databases, PINs, CVVs, or OTPs.