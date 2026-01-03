-- Reaper ChatGPT Bridge (Lua)
-- Minimal, file-based bridge for sending prompts to an external processor
-- and reading responses back. Designed to work with scripts/send_to_chatgpt_lua.ps1.

-- Configuration
local function _script_dir()
    local source = debug.getinfo(1, "S").source
    if source:sub(1, 1) == "@" then
        source = source:sub(2)
    end
    return source:match("^(.*[\\/])") or ""
end

local function _detect_workspace()
    local env = os.getenv("AGI_WORKSPACE") or os.getenv("AGI_WORKSPACE_ROOT") or os.getenv("WORKSPACE_ROOT")
    if env and #env > 0 then
        return env
    end
    local dir = _script_dir()
    if dir ~= "" then
        local trimmed = dir:gsub("[\\/]+$", "")
        return trimmed:match("^(.*)[/\\\\][^/\\\\]+$") or ""
    end
    return ""
end

local WORKSPACE = _detect_workspace()
if WORKSPACE == "" then
    error("Workspace not set. Define AGI_WORKSPACE or WORKSPACE_ROOT.")
end
WORKSPACE = WORKSPACE:gsub("\\", "/")
local REQUEST_DIR = WORKSPACE .. "/outputs/lua_requests"
local RESPONSE_DIR = WORKSPACE .. "/outputs/trinity_responses"

-- Utilities
local function ensure_dir(path)
    -- Windows-friendly mkdir (no error if exists)
    local cmd = string.format('if not exist "%s" mkdir "%s"', path, path)
    os.execute(cmd)
end

local function file_exists(path)
    local f = io.open(path, 'r')
    if f then f:close() return true end
    return false
end

local function read_all(path)
    local f = io.open(path, 'rb')
    if not f then return nil end
    local content = f:read('*a')
    f:close()
    return content
end

local function write_all(path, content)
    local f = assert(io.open(path, 'wb'))
    f:write(content)
    f:close()
end

-- Minimal JSON encoder (encode only). Escapes control characters safely.
local json = (function()
    local function escape_str(s)
        s = tostring(s or '')
        s = s:gsub('\\', '\\\\')
             :gsub('"', '\\"')
             :gsub('\r', '\\r')
             :gsub('\n', '\\n')
             :gsub('\t', '\\t')
        -- Escape remaining control chars < 0x20
        s = s:gsub("[%z\1-\31]", function(c)
            return string.format("\\u%04X", string.byte(c))
        end)
        return '"' .. s .. '"'
    end

    local function encode_val(v)
        local t = type(v)
        if t == 'nil' then return 'null' end
        if t == 'string' then return escape_str(v) end
        if t == 'number' or t == 'boolean' then return tostring(v) end
        if t == 'table' then
            local is_array = true
            local max_i = 0
            for k,_ in pairs(v) do
                if type(k) ~= 'number' then is_array = false break end
                if k > max_i then max_i = k end
            end
            if is_array then
                local parts = {}
                for i = 1, max_i do parts[#parts+1] = encode_val(v[i]) end
                return '[' .. table.concat(parts, ',') .. ']'
            else
                local parts = {}
                for k,val in pairs(v) do
                    parts[#parts+1] = escape_str(tostring(k)) .. ':' .. encode_val(val)
                end
                return '{' .. table.concat(parts, ',') .. '}'
            end
        end
        return 'null'
    end

    return { encode = encode_val, decode = nil }
end)()

-- Ensure base directories exist
ensure_dir(REQUEST_DIR)
ensure_dir(RESPONSE_DIR)

-- Public API
local M = {}

-- Generate a simple unique id
local function gen_id()
    math.randomseed(os.time() + math.random(1, 999999))
    return string.format('lua_%d_%04d', os.time(), math.random(0, 9999))
end

-- Sends a prompt to the request directory and returns request_id and file path
function M.send_prompt(prompt, opts)
    opts = opts or {}
    local req_id = (opts.id) or gen_id()
    local req = {
        id = req_id,
        prompt = tostring(prompt or ''),
        source = 'reaper',
        timestamp = os.time(),
        meta = opts.meta or {}
    }
    local filename = string.format('%s/req_%s.json', REQUEST_DIR, req_id)
    write_all(filename, json.encode(req))
    return req_id, filename
end

-- Attempts to read a response for the given request id; returns table or nil
function M.try_read_response(req_id)
    local path = string.format('%s/resp_%s.json', RESPONSE_DIR, req_id)
    if not file_exists(path) then return nil end
    local raw = read_all(path)
    if not raw then return nil end
    -- If a JSON decoder is available (e.g., dkjson/cjson), try it; otherwise return raw
    if json.decode then
        local ok, resp = pcall(json.decode, raw)
        if ok and resp then return resp end
    end
    return { raw = raw }
end

-- Busy-wait with a small sleep loop (Reaper-safe): waits up to timeout_sec
function M.wait_response(req_id, timeout_sec)
    timeout_sec = timeout_sec or 30
    local start = os.time()
    while (os.time() - start) < timeout_sec do
        local resp = M.try_read_response(req_id)
        if resp then return resp end
        if reaper and reaper.defer then
            reaper.defer(function() end) -- yield to Reaper UI loop
        else
            -- fallback: tiny sleep using busy-wait
            local t0 = os.clock()
            while (os.clock() - t0) < 0.05 do end
        end
    end
    return nil
end

-- Convenience: send and wait for response
function M.ask(prompt, timeout_sec)
    local id = M.send_prompt(prompt)
    return M.wait_response(id, timeout_sec)
end

return M
