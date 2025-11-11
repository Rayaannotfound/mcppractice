from fastapi import FastAPI
from fastapi_mcp import FastApiMCP


app = FastAPI(title="MCP Api")
@app.post("/add")
def add(one, two):
    print(one+two)
    return int(one) + int(two)

mcp=FastApiMCP(app, name="Now I'm the MCP")
mcp.mount_http()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=6767)