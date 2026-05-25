"""
email_service.py — EcoBreaker Email Service

Sends verification emails. Supports multiple providers via environment variables:
  - RESEND_API_KEY  → uses Resend (resend.com) — recommended
  - SMTP_HOST + SMTP_USER + SMTP_PASSWORD → SMTP (Gmail, etc.)
  - If neither is set: logs the verification link to console (dev mode)

Set FRONTEND_URL in .env to your frontend URL (e.g. https://eco-breaker.vercel.app)
"""
import os
import smtplib
import urllib.request
import urllib.error
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@ecobreaker.com")
FROM_NAME = os.getenv("FROM_NAME", "EcoBreaker")


def _build_email_html(username: str, verify_url: str) -> str:
    return f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Verify your EcoBreaker account</title>
</head>
<body style="margin:0;padding:0;background:#020617;font-family:'Georgia',serif;">
  <div style="max-width:560px;margin:40px auto;padding:0 16px;">
    <div style="background:#0f172a;border:1px solid rgba(56,189,248,0.2);border-radius:16px;overflow:hidden;">

      <!-- Header -->
      <div style="background:linear-gradient(135deg,#0ea5e9,#3b82f6);padding:28px 32px;text-align:center;">
        <h1 style="margin:0;font-size:24px;color:#fff;font-style:italic;letter-spacing:-0.5px;">
          ✦ EcoBreaker
        </h1>
        <p style="margin:6px 0 0;font-size:13px;color:rgba(255,255,255,0.8);font-style:italic;">
          Challenging perspectives, one article at a time
        </p>
      </div>

      <!-- Body -->
      <div style="padding:32px;">
        <h2 style="margin:0 0 12px;color:#e2e8f0;font-size:20px;font-style:italic;">
          Welcome, {username}! 👋
        </h2>
        <p style="margin:0 0 20px;color:#94a3b8;font-size:14px;line-height:1.7;font-style:italic;">
          Thanks for joining EcoBreaker. Click the button below to verify your email address
          and unlock full author access — start writing and publishing immediately.
        </p>

        <!-- CTA Button -->
        <div style="text-align:center;margin:28px 0;">
          <a href="{verify_url}"
             style="display:inline-block;background:linear-gradient(135deg,#0ea5e9,#3b82f6);
                    color:#fff;text-decoration:none;padding:14px 36px;border-radius:10px;
                    font-size:15px;font-weight:700;font-style:italic;
                    box-shadow:0 4px 20px rgba(14,165,233,0.35);">
            ✓ Verify My Email &amp; Become an Author
          </a>
        </div>

        <p style="margin:0 0 8px;color:#64748b;font-size:12px;font-style:italic;text-align:center;">
          Or copy this link into your browser:
        </p>
        <p style="word-break:break-all;background:#020617;border:1px solid rgba(56,189,248,0.15);
                  border-radius:8px;padding:10px 12px;color:#38bdf8;font-size:11px;margin:0 0 24px;">
          {verify_url}
        </p>

        <div style="border-top:1px solid rgba(56,189,248,0.1);padding-top:20px;">
          <p style="margin:0;color:#475569;font-size:12px;font-style:italic;">
            This link expires in <strong style="color:#94a3b8;">24 hours</strong>.
            If you didn't create an account, you can safely ignore this email.
          </p>
        </div>
      </div>

      <!-- Footer -->
      <div style="background:#020617;padding:16px 32px;text-align:center;">
        <p style="margin:0;color:#334155;font-size:11px;font-style:italic;">
          © 2026 EcoBreaker · Challenging perspectives, one article at a time
        </p>
      </div>
    </div>
  </div>
</body>
</html>
"""


def send_verification_email(to_email: str, username: str, token: str) -> bool:
    """
    Send a verification email to the user.
    Returns True if sent successfully, False otherwise.
    The verification link will open the frontend /verify-email page with the token.
    """
    verify_url = f"{FRONTEND_URL}/verify-email?token={token}"
    subject = "Verify your EcoBreaker account ✦"
    html_body = _build_email_html(username, verify_url)

    # ── Try Resend API ──────────────────────────────────────────────────────
    resend_key = os.getenv("RESEND_API_KEY")
    if resend_key:
        try:
            payload = json.dumps({
                "from": f"{FROM_NAME} <{FROM_EMAIL}>",
                "to": [to_email],
                "subject": subject,
                "html": html_body,
            }).encode("utf-8")
            req = urllib.request.Request(
                "https://api.resend.com/emails",
                data=payload,
                headers={
                    "Authorization": f"Bearer {resend_key}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read())
                print(f"[Email] Verification email sent via Resend to {to_email} (id={result.get('id')})")
                return True
        except Exception as e:
            print(f"[Email] Resend failed: {e}")

    # ── Try SMTP ────────────────────────────────────────────────────────────
    smtp_host = os.getenv("SMTP_HOST")
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    if smtp_host and smtp_user and smtp_pass:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{FROM_NAME} <{FROM_EMAIL}>"
            msg["To"] = to_email
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(FROM_EMAIL, to_email, msg.as_string())
            print(f"[Email] Verification email sent via SMTP to {to_email}")
            return True
        except Exception as e:
            print(f"[Email] SMTP failed: {e}")

    # ── Dev fallback: print to console ──────────────────────────────────────
    print("\n" + "=" * 60)
    print("[Email DEV MODE] No email provider configured.")
    print(f"  To: {to_email}")
    print(f"  Subject: {subject}")
    print(f"  Verify URL: {verify_url}")
    print("=" * 60 + "\n")
    return False
