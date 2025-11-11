from fastmcp import FastMCP
import os
import smtplib
import ssl
from email.message import EmailMessage
from typing import Optional, List

mcp = FastMCP(name="Email Sender MCP")
# need to decide on oh idk an actual email client I can use

def _get_env(name: str, required: bool = True) -> Optional[str]:
    val = os.environ.get(name)
    if required and not val:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return val


def _split_list(s: str) -> List[str]:
    return [p.strip() for p in s.split(",") if p.strip()] if s else []


@mcp.tool()
def send_email(
    to: str,
    subject: str,
    body: str,
    cc: str = "",
    bcc: str = "",
):

    try:
        host = _get_env("SMTP_HOST")
        port = int(_get_env("SMTP_PORT"))
        user = _get_env("SMTP_USER")
        password = _get_env("SMTP_PASS")
        from_addr = _get_env("SMTP_FROM")
        agent_intro = os.environ.get("USER_INTRO", "Email tool")

        # The message contents
        msg = EmailMessage()
        msg["From"] = from_addr
        msg["To"] = to
        if cc:
            msg["Cc"] = cc
        msg["Subject"] = subject
        msg.set_content(body)

        all_recipients = _split_list(to) + _split_list(cc) + _split_list(bcc)

        if not all_recipients:
            return {"ok": False, "error": "No recipients provided."}

        # still in progress
        if port == 465:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(host, port, context=context) as server:
                server.login(user, password)
                resp = server.send_message(msg, from_addr=from_addr, to_addrs=all_recipients)
        else:
            with smtplib.SMTP(host, port) as server:
                server.ehlo()
                try:
                    server.starttls(context=ssl.create_default_context())
                    server.ehlo()
                except smtplib.SMTPNotSupportedError:
                    pass
                server.login(user, password)
                resp = server.send_message(msg, from_addr=from_addr, to_addrs=all_recipients)


        if resp:
            return {"ok": False, "error": f"Some recipients were refused: {resp}"}


        mid = msg.get("Message-ID") or "<local-generated>"
        return {
            "ok": True,
            "message_id": str(mid),
            "recipients": all_recipients,
            "agent": agent_intro,
        }

    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


if __name__ == "__main__":
    mcp.run()
