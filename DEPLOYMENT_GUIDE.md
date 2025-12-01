# Streamlit Cloud Deployment Guide

## Problem Solved
The app was failing on Streamlit Cloud with "gcloud command not found" error. This guide shows how to set up service account authentication for cloud deployment.

## Steps to Deploy on Streamlit Cloud

### 1. Create Earth Engine Service Account

1. Go to **Google Cloud Console**: https://console.cloud.google.com/
2. Select your project: `gee-python-419405`
3. Navigate to: **IAM & Admin** → **Service Accounts**
4. Click **"Create Service Account"**

   **Service account details:**
   - Name: `earth-engine-streamlit`
   - Description: `Service account for Streamlit Earth Engine app`
   - Click **"Create and Continue"**

5. **Grant permissions:**
   - Role: `Earth Engine Resource Writer` (or `Editor`)
   - Click **"Continue"** → **"Done"**

6. **Create JSON key:**
   - Click on the newly created service account
   - Go to **"Keys"** tab
   - Click **"Add Key"** → **"Create new key"**
   - Choose **JSON** format
   - Click **"Create"** (a JSON file will download)

### 2. Register Service Account with Earth Engine

1. Copy the service account email from the JSON file (looks like: `earth-engine-streamlit@gee-python-419405.iam.gserviceaccount.com`)

2. Go to **Earth Engine Asset Manager**: https://code.earthengine.google.com/

3. Register the service account:
   ```bash
   earthengine set_project gee-python-419405
   earthengine create asset users/YOUR_USERNAME --asset-writers earth-engine-streamlit@gee-python-419405.iam.gserviceaccount.com
   ```

   Or use the Earth Engine Code Editor:
   - Go to: https://code.earthengine.google.com/
   - Share your assets with the service account email

### 3. Configure Streamlit Cloud Secrets

1. Go to your Streamlit Cloud app: https://share.streamlit.io/
2. Select your app: **bkk-pm2.5-test**
3. Click **"Settings"** (⚙️) → **"Secrets"**

4. **Add the following secrets** (copy from your downloaded JSON file):

   ```toml
   [ee_service_account]
   type = "service_account"
   project_id = "gee-python-419405"
   private_key_id = "YOUR_PRIVATE_KEY_ID_FROM_JSON"
   private_key = "-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY_FROM_JSON\n-----END PRIVATE KEY-----\n"
   client_email = "earth-engine-streamlit@gee-python-419405.iam.gserviceaccount.com"
   client_id = "YOUR_CLIENT_ID_FROM_JSON"
   auth_uri = "https://accounts.google.com/o/oauth2/auth"
   token_uri = "https://oauth2.googleapis.com/token"
   auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
   client_x509_cert_url = "YOUR_CERT_URL_FROM_JSON"
   ```

   **Important Notes:**
   - Copy the exact values from your JSON file
   - The `private_key` should include `\n` for line breaks
   - Keep all quotes as shown

5. Click **"Save"**

### 4. Update Your GitHub Repository

1. Push the updated `app.py` to GitHub:
   ```bash
   cd "C:\Users\Tin Ko Oo\Pictures\Screenshots"
   git add app.py
   git commit -m "Add service account authentication for Streamlit Cloud"
   git push origin main
   ```

2. Streamlit Cloud will automatically redeploy your app

### 5. Verify Deployment

1. Wait for redeployment (1-2 minutes)
2. Visit your app: https://bkk-pm25-test.streamlit.app/
3. The app should now load without authentication errors

## Local Development vs Cloud

The updated app automatically detects the environment:

- **Local**: Uses your personal Earth Engine credentials (`ee.Initialize()`)
- **Streamlit Cloud**: Uses service account credentials from secrets

No code changes needed - it works in both environments!

## Security Best Practices

1. **Never commit secrets to GitHub**
   - Add `.streamlit/secrets.toml` to `.gitignore`
   - Only commit `.streamlit/secrets.toml.example`

2. **Service account permissions**
   - Grant minimum required permissions
   - Use `Earth Engine Resource Writer` role only

3. **Key rotation**
   - Rotate service account keys periodically
   - Delete old keys after rotation

## Troubleshooting

### Error: "Service account not found"
- Make sure you added secrets in Streamlit Cloud settings
- Check that secret name is exactly `ee_service_account`

### Error: "Permission denied"
- Register service account with Earth Engine
- Check service account has proper IAM roles

### Error: "Invalid key format"
- Ensure `private_key` includes `\n` for newlines
- Copy the entire key including BEGIN/END lines

### App still not working
- Check Streamlit Cloud logs for detailed errors
- Verify all fields in secrets.toml match your JSON file
- Ensure project ID is correct: `gee-python-419405`

## Quick Reference

**Your Project Details:**
- Project ID: `gee-python-419405`
- Your Email: `tinkooo.b@gmail.com`
- App URL: https://bkk-pm25-test.streamlit.app/
- GitHub Repo: https://github.com/mrtinkooo/bkk-pm2.5-test

## Additional Resources

- [Earth Engine Service Accounts](https://developers.google.com/earth-engine/guides/service_account)
- [Streamlit Secrets Management](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)
- [Google Cloud Service Accounts](https://cloud.google.com/iam/docs/service-accounts)
