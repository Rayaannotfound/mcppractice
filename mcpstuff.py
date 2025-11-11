from fastmcp import FastMCP
from flask import Flask

mcp = FastMCP(name="Random Test Stuff")

@mcp.tool(
    name="add",
    description="Adds two numbers",
    tags = ["math", "random function", "arithmetic", "basic func"],
)
def add(first: float, second: float) -> int:
    if type(first) == str:
        first = 0
    if type(second) == str:
        second = 0
    print(first + second)
    return first + second


if __name__ == "__main__":
    mcp.run(http)