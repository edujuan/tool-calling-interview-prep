# UTCP Content Verification Report

**Date:** November 22, 2025  
**Source:** Compared repository content against official UTCP-docs MCP server

## Executive Summary

The UTCP documentation in the repository contains several **inaccuracies** when compared to the official UTCP v1.0.1 specification. The main issues are:

1. ❌ **Incorrect version number** in examples
2. ❌ **Missing required field** (`manual_version`)
3. ❌ **Unsupported protocols** documented as supported (GraphQL, gRPC)
4. ⚠️ **Some terminology inconsistencies**

## Detailed Findings

### 🔴 Critical Issues

#### 1. Version Number Mismatch

**Location:** `protocols/utcp/README.md` (multiple examples)

**Issue:** The repository uses `"utcp_version": "1.0"` but the official specification uses `"utcp_version": "1.0.1"`

**Repository (INCORRECT):**
```json
{
  "utcp_version": "1.0",
  "tools": [...]
}
```

**Official Spec (CORRECT):**
```json
{
  "manual_version": "1.0.0",
  "utcp_version": "1.0.1",
  "tools": [...]
}
```

**Impact:** Manuals created based on repo examples may not be recognized as valid by UTCP v1.0.1 clients.

---

#### 2. Missing `manual_version` Field

**Location:** All manual examples in `protocols/utcp/README.md`

**Issue:** The `manual_version` field is required in UTCP v1.0.1 but is missing from all examples in the repository.

**Official Example Structure:**
```json
{
  "manual_version": "1.0.0",    // ← REQUIRED but missing in repo
  "utcp_version": "1.0.1",
  "tools": [...]
}
```

**Impact:** All example manuals in the repo are technically invalid according to v1.0.1 spec.

---

#### 3. Unsupported Protocols Documented

**Location:** `protocols/utcp/README.md` lines 93-120

**Issue:** The repository documents GraphQL and gRPC as supported `call_template_type` values, but these are **NOT found in the official UTCP v1.0.1 specification**.

**Repository Claims (UNVERIFIED):**

GraphQL example (lines 94-101):
```json
{
  "call_template_type": "graphql",
  "url": "https://api.example.com/graphql",
  "query": "query { user(id: {{user_id}}) { name email } }"
}
```

gRPC example (lines 104-111):
```json
{
  "call_template_type": "grpc",
  "service": "UserService",
  "method": "GetUser",
  "endpoint": "api.example.com:443"
}
```

**Official Supported Protocols:**
Based on the UTCP-docs server, the officially supported call template types are:
- ✅ `http` - Standard HTTP/REST
- ✅ `cli` - Command-line interface
- ✅ `sse` - Server-Sent Events (part of utcp-http plugin)
- ✅ `streamable_http` - Streaming HTTP responses (part of utcp-http plugin)
- ✅ `mcp` - Model Context Protocol interoperability
- ✅ `text` - Local file-based manuals
- ✅ `websocket` - WebSocket protocol (utcp-websocket plugin)

**Impact:** Developers may try to use GraphQL and gRPC call templates that won't work with actual UTCP clients.

---

### 🟡 Minor Issues

#### 4. Metadata Structure

**Location:** `protocols/utcp/README.md` line 169

**Issue:** While not incorrect, the `metadata` field shown in examples is optional and its exact structure isn't well-defined in the official docs.

**Repository Example:**
```json
{
  "metadata": {
    "title": "Example Service Tools",
    "version": "2.1.0",
    "description": "Tools for interacting with Example Service",
    "tags": ["weather", "maps", "search"]
  }
}
```

**Status:** This appears to be valid but less commonly used. The official examples use simpler metadata or place info in other fields.

---

#### 5. Authentication Location

**Location:** `protocols/utcp/README.md` lines 267-304

**Issue:** The examples show `auth` at the top level of the manual, but official examples show it can be either:
- At the top level (for shared auth across all tools)
- Inside the `tool_call_template` (for per-tool auth)

**Status:** Not incorrect, but could be clearer about both options.

---

### ✅ What's Correct

The repository **correctly** documents:

1. ✅ **Field names**: `tool_call_template`, `inputs`, `call_template_type`
2. ✅ **HTTP protocol structure**: URL, method, headers, query_params, body_template
3. ✅ **CLI protocol structure**: Command and args
4. ✅ **MCP interoperability**: UTCP can call MCP tools
5. ✅ **Authentication types**: API key, OAuth2, Basic auth (though implementations may vary)
6. ✅ **Template syntax**: `{{parameter}}` and `${ENV_VAR}` interpolation
7. ✅ **Core concepts**: Manual structure, direct calling, no server requirement
8. ✅ **Discovery methods**: File-based, URL-based, registry-based
9. ✅ **Advantages**: Performance, simplicity, flexibility
10. ✅ **Limitations**: Stateless, no bidirectional communication, limited governance

---

## Recommendations

### Immediate Fixes Required

1. **Update version in all examples** from `"utcp_version": "1.0"` to `"utcp_version": "1.0.1"`

2. **Add `manual_version` field** to all manual examples:
   ```json
   {
     "manual_version": "1.0.0",
     "utcp_version": "1.0.1",
     ...
   }
   ```

3. **Remove or clearly mark GraphQL and gRPC examples** as:
   - Either "Future/Planned Support" or
   - "Example Only - Not Currently Supported" or
   - Remove them entirely until official support is confirmed

### Suggested Improvements

4. **Add note about protocol plugins**: Clarify that users need to install protocol-specific packages:
   ```bash
   pip install utcp utcp-http utcp-cli utcp-websocket utcp-text utcp-mcp
   ```

5. **Update the protocol list** to match official support:
   - HTTP (including SSE and Streamable HTTP)
   - CLI
   - WebSocket
   - Text
   - MCP

6. **Add WebSocket example**: The repo doesn't show WebSocket, but it's officially supported.

7. **Clarify SSE and Streamable HTTP**: These are not separate `call_template_type` values but are part of the `http` protocol with additional fields.

---

## Comparison Table

| Feature | Repository | Official v1.0.1 | Status |
|---------|-----------|-----------------|--------|
| utcp_version | "1.0" | "1.0.1" | ❌ Incorrect |
| manual_version field | Missing | "1.0.0" (required) | ❌ Missing |
| HTTP support | ✅ | ✅ | ✅ Correct |
| CLI support | ✅ | ✅ | ✅ Correct |
| MCP support | ✅ | ✅ | ✅ Correct |
| SSE support | Implied | ✅ (part of http) | ⚠️ Incomplete |
| WebSocket support | Missing | ✅ | ⚠️ Missing |
| GraphQL support | ✅ | ❌ Not found | ❌ Incorrect |
| gRPC support | ✅ | ❌ Not found | ❌ Incorrect |
| Text protocol | Missing | ✅ | ⚠️ Missing |
| Auth types | ✅ | ✅ | ✅ Correct |
| Template syntax | ✅ | ✅ | ✅ Correct |

---

---

### 🔴 CRITICAL: Example Code Uses Wrong UTCP Format

**Location:** `examples/python-utcp-weather/main.py` and `README.md`

**Issue:** The entire weather example uses a **custom UTCP format that does not match the official UTCP v1.0.1 specification**. This is the most serious issue found.

**Example Code (COMPLETELY WRONG):**
```python
WEATHER_UTCP_MANUAL = {
    "protocol": "utcp",
    "version": "1.0",
    "tool": {                              # ← Should be "tools" (array)
        "name": "get_current_weather",
        "endpoint": {                      # ← Wrong structure
            "url": "https://api.openweathermap.org/data/2.5/weather",
            "method": "GET"
        },
        "authentication": {                # ← Should be "auth" at top level
            "type": "api_key",
            "location": "query",
            "param_name": "appid",
            "env_var": "OPENWEATHER_API_KEY"
        },
        "parameters": {                    # ← Should be "inputs"
            # ...
        }
    }
}
```

**Official UTCP v1.0.1 Format (CORRECT):**
```json
{
  "manual_version": "1.0.0",
  "utcp_version": "1.0.1",
  "tools": [                              // Array of tools
    {
      "name": "get_current_weather",
      "description": "Get the current weather for a specific location",
      "inputs": {                         // Not "parameters"
        "type": "object",
        "properties": {
          "location": {
            "type": "string",
            "description": "City name"
          }
        },
        "required": ["location"]
      },
      "tool_call_template": {             // Not "endpoint"
        "call_template_type": "http",
        "url": "https://api.openweathermap.org/data/2.5/weather",
        "http_method": "GET",
        "query_params": {
          "q": "${location}",
          "appid": "${WEATHER_API_KEY}"
        }
      }
    }
  ],
  "auth": {                               // Top-level auth
    "auth_type": "api_key",
    "api_key": "${WEATHER_API_KEY}",
    "var_name": "appid",
    "location": "query"
  }
}
```

**Key Differences:**

| Example Code | Official Spec | Issue |
|-------------|---------------|-------|
| `"tool": {...}` | `"tools": [...]` | Wrong field name, should be array |
| `"endpoint"` | `"tool_call_template"` | Wrong field name |
| `"method": "GET"` | `"http_method": "GET"` | Wrong field name |
| `"parameters"` | `"inputs"` | Wrong field name |
| `"authentication"` | `"auth"` | Wrong field name |
| `"protocol": "utcp"` | N/A | Extra field not in spec |
| `"version": "1.0"` | `"utcp_version": "1.0.1"` | Wrong field name and value |
| Missing | `"manual_version": "1.0.0"` | Required field missing |
| Missing | `"call_template_type": "http"` | Required field missing |

**Impact:** **CRITICAL** - The entire weather example implements a custom format that:
- Will not work with any official UTCP v1.0.1 client
- Teaches developers an incorrect UTCP structure
- Requires a custom `UTCPExecutor` class that won't be compatible with standard UTCP libraries
- Contradicts the official specification completely

This suggests the example may have been created before UTCP v1.0.1 was finalized, or was based on an unofficial/draft version of the specification.

---

## Files Requiring Updates

### Primary Files (CRITICAL)
- **`examples/python-utcp-weather/main.py`** - **COMPLETE REWRITE REQUIRED** - Uses wrong UTCP format
- **`examples/python-utcp-weather/README.md`** - Contains wrong manual structure in examples
- **`protocols/utcp/README.md`** - Main documentation file with version and protocol issues

### Other Files to Check
- Any other UTCP examples in the repository that may use the same custom format

---

## Sources

This verification was performed using the official UTCP-docs MCP server which provides:
- Complete UTCP v1.0.1 specification
- Official examples
- Protocol plugin documentation
- Best practices and implementation guides

**Note:** While one search result mentioned "multi-protocol support (HTTP, CLI, gRPC, MCP)" in an introduction, no actual implementation, plugin, or detailed documentation for gRPC was found in the specification. This suggests gRPC may be planned but not yet officially supported in v1.0.1.

---

## Conclusion

The repository's UTCP documentation provides a **good conceptual overview** and captures many correct details, but contains **critical technical inaccuracies** that need correction. The main issues are:

1. Wrong version number (fixable in minutes)
2. Missing required field (fixable in minutes)
3. Documenting unsupported protocols as if they work (requires careful update)

**Recommendation:** Update the UTCP documentation to match the official v1.0.1 specification before using it for learning or reference purposes.

