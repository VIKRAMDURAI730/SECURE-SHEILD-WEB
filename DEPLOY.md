# Deploy to a permanent public link (Render)

Your app is set up to deploy on **Render** (free tier). You get a URL like `https://purchase-xxxx.onrender.com` that works from any device.

## Prerequisites

- A **GitHub** (or GitLab / Bitbucket) account
- Your project in a **Git repository** (local git + pushed to GitHub)

---

## Step 1: Push your code to GitHub

If the project is not in Git yet:

```bash
cd d:\purchase
git init
git add .
git commit -m "Initial commit - Purchase app"
```

Create a new repository on [github.com](https://github.com/new) (e.g. name: `purchase`), then:

```bash
git remote add origin https://github.com/YOUR_USERNAME/purchase.git
git branch -M main
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username.

---

## Step 2: Deploy on Render

1. Go to **[render.com](https://render.com)** and sign up / log in (free).
2. Click **Dashboard** → **New** → **Web Service**.
3. Connect your **GitHub** account if asked and select the **purchase** repo (or the repo where you pushed the code).
4. Render will detect the app. If you have `render.yaml` in the repo it may prefill. Otherwise set:
   - **Name:** `purchase` (or any name)
   - **Runtime:** Python
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT`
5. Choose **Free** plan.
6. Click **Create Web Service**.

Render will build and deploy. When it finishes, you’ll see a URL like:

**https://purchase-xxxx.onrender.com**

That is your **permanent public link**. Open it on any PC or phone.

---

## Step 3: Use your link

- **First time:** Register on the site (Create account), then log in.
- **Free tier:** The service may “sleep” after ~15 minutes of no use; the first open after that can take 30–60 seconds to wake up.
- **Data:** On the free tier, the SQLite database can be reset when the app restarts or redeploys. For long-term data, you’d add a Render PostgreSQL database later.

---

## Optional: Deploy with Blueprint (render.yaml)

If `render.yaml` is in your repo:

1. In Render Dashboard: **New** → **Blueprint**.
2. Connect the same GitHub repo.
3. Render will read `render.yaml` and create the web service automatically.
4. Use the URL Render gives you as your permanent public link.

---

## Troubleshooting

| Issue | What to do |
|-------|------------|
| Build fails | Check the **Logs** tab on Render. Ensure `requirements.txt` and `gunicorn` are correct. |
| “Application failed to respond” | Confirm **Start Command** is exactly: `gunicorn app:app --bind 0.0.0.0:$PORT` |
| Can’t log in / 500 error | Check **Logs** for Python errors. Ensure the app starts without errors. |

Your permanent public link will look like: **https://purchase-xxxx.onrender.com**
