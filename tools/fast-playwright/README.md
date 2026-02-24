# fast-playwright

## Capability Summary
Interactive FastMCP browser automation server for session-based web workflows with accessibility snapshots and low-latency tool calls.

## Primary MCP Tools
- `browser_navigate`
- `browser_click`
- `browser_type`
- `browser_screenshot`
- `browser_network_requests`

## Session Guidance
Use this tool when the workflow needs persistent browser state across multiple actions (navigation, interaction, inspection). It is preferred for interactive exploration and task sequences that depend on accessibility snapshots and request-level diagnostics.

## CLI
- `--help`
- `--version`
- `--json` (tool responses are structured by the MCP server protocol)

## Startup
- `bin/start-mcp`
- `bin/start-mcp --help`
