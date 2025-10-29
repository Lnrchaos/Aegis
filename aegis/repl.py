from __future__ import annotations
import sys
from pathlib import Path
from .parser import parse, ParseError
from .runtime import RuntimeErrorAegis, current_stack
from .interpreter import evaluate
from .env import make_global_env


HELP = """
Commands:
  .help         Show this help
  .load FILE    Execute a file in the current REPL environment
  .show VAR     Show a variable value
  .mode [red|blue] Show or set mode
  .exit         Quit
Multiline: end a block with a closing brace '}'.
""".strip()


def start_repl() -> None:
    env = make_global_env()
    # default mode if not set
    try:
        env.get("MODE")
    except Exception:
        env.define("MODE", "blue")
    print("Aegis REPL. Ctrl+C to exit. Type .help for help.")
    buffer: list[str] = []
    while True:
        try:
            prompt = ".. " if buffer else ">> "
            line = input(prompt)
        except (EOFError, KeyboardInterrupt):
            print()
            return
        # optional colorization preview on submission (does not affect execution)
        if REPL_COLORIZE and not buffer and not line.startswith('.'):
            _print_colorized(line)
        if not line.strip() and not buffer:
            continue
        # Handle Ctrl+O team commands (convert to colon commands)
        if line.startswith('\x0f'):  # Ctrl+O
            if line == '\x0fredteam' or line == '\x0fred':
                line = ':redteam'
            elif line == '\x0fblueteam' or line == '\x0fblue':
                line = ':blueteam'
        
        # Handle colon team commands
        if line.strip() == ':redteam':
            env.define("MODE", "red")
            print("[red team] Offensive security mode activated")
            print("[red team] Available: attack, exploit, payload, inject, brute")
            continue
        elif line.strip() == ':blueteam':
            env.define("MODE", "blue") 
            print("[blue team] Defensive security mode activated")
            print("[blue team] Available: defend, protect, monitor, quarantine, alert")
            continue
        
        # commands
        if not buffer and line.startswith("."):
            cmd, *rest = line.strip().split(maxsplit=1)
            if cmd == ".help":
                print(HELP)
                continue
            if cmd == ".exit":
                return
            if cmd == ".mode":
                if not rest:
                    try:
                        print(f"mode: {env.get('MODE')}")
                    except Exception:
                        print("mode: unknown")
                    continue
                m = rest[0].strip().lower()
                if m not in ("red", "blue", "redteam", "blueteam"):
                    print("Usage: .mode red|blue|redteam|blueteam")
                    continue
                # Normalize team names
                if m == "redteam":
                    m = "red"
                elif m == "blueteam":
                    m = "blue"
                env.define("MODE", m)
                print(f"[ok] mode set to {m} team")
                # Set team-specific environment
                if m == "red":
                    print("[red team] Offensive security mode activated")
                    print("[red team] Available: attack, exploit, payload, inject, brute")
                else:
                    print("[blue team] Defensive security mode activated") 
                    print("[blue team] Available: defend, protect, monitor, quarantine, alert")
                continue
            if cmd == ".load":
                if not rest:
                    print("Usage: .load FILE")
                    continue
                path = rest[0].strip()
                p = Path(path)
                if not p.exists():
                    print(f"Not found: {path}")
                    continue
                try:
                    source = p.read_text(encoding="utf-8")
                    program = parse(source)
                    result = evaluate(program, env)
                    if result is not None:
                        print(result)
                except ParseError as pe:
                    print(f"Parse error: {pe}")
                except RuntimeErrorAegis as re:
                    print(f"Runtime error: {re}")
                    st = current_stack()
                    if st:
                        print("Stack:")
                        for f in reversed(st):
                            print(f"  at {f}()")
                continue
            if cmd == ".show":
                if not rest:
                    print("Usage: .show VARIABLE")
                    continue
                var_name = rest[0].strip()
                try:
                    value = env.get(var_name)
                    print(f"{var_name} = {value}")
                except Exception as e:
                    print(f"Variable '{var_name}' not found: {e}")
                continue
        # keyword-mode handling (only when not in a multiline buffer)
        if not buffer and _handle_keyword_line(line, env):
            continue
        # multiline handling
        buffer.append(line)
        # heuristic: if braces balanced and not ending with unfinished token, run
        src = "\n".join(buffer)
        if _balanced_braces(src):
            try:
                program = parse(src)
                result = evaluate(program, env)
                if result is not None:
                    print(result)
            except ParseError as pe:
                print(f"Parse error: {pe}")
            except RuntimeErrorAegis as re:
                print(f"Runtime error: {re}")
                st = current_stack()
                if st:
                    print("Stack:")
                    for f in reversed(st):
                        print(f"  at {f}()")
            finally:
                buffer.clear()


def _balanced_braces(s: str) -> bool:
    count = 0
    in_string = False
    escape = False
    for ch in s:
        if in_string:
            if escape:
                escape = False
                continue
            if ch == "\\":
                escape = True
                continue
            if ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
            continue
        if ch == '{':
            count += 1
        elif ch == '}':
            count -= 1
    return count == 0



# ---------------- Keyword/command handling ----------------

def _handle_keyword_line(line: str, env) -> bool:
    s = line.strip()
    if not s:
        return False
    # Ignore comments
    if s.startswith("~"):
        return True
    # Scan for presence of any cybersecurity keyword anywhere in line
    lower = s.lower()
    if not any(f" {kw} " in f" {lower} " for kw in _CYBER_KEYWORDS):
        return False
    tokens = _freeform_tokenize(s)
    if not tokens:
        return False
    # Control-flow handling: if/while/until/when
    low_tokens = [t.lower() for t in tokens]
    if "after" in low_tokens:
        _handle_after(tokens, env)
        return True
    if "if" in low_tokens or "when" in low_tokens:
        # normalize 'when' to 'if' for freeform REPL conditions
        tokens = ["if" if t.lower() == "when" else t for t in tokens]
        _handle_if_chain(tokens, env)
        return True
    if "while" in low_tokens or "until" in low_tokens:
        _handle_loop(tokens, env)
        return True
    # Split by 'and' for chaining (case-insensitive), preserving quoted groups
    chains = _split_on_and(tokens)
    handled_any = False
    for toks in chains:
        if not toks:
            continue
        # Scan entire token list for known keywords; dispatch starting at each occurrence
        dispatched = False
        for i, t in enumerate(toks):
            key = t.lower()
            if key in _KEYWORD_DISPATCH:
                sub = toks[i:]
                if _KEYWORD_DISPATCH[key](sub, env):
                    handled_any = True
                    dispatched = True
                    break
        if not dispatched:
            # If chain contains no known keyword, fall back to normal evaluation of full line
            return False
    return handled_any


def _freeform_tokenize(s: str) -> list[str]:
    tokens: list[str] = []
    cur: list[str] = []
    in_quotes = False
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == '"':
            in_quotes = not in_quotes
            i += 1
            continue
        if not in_quotes and ch in "()":
            if cur:
                tokens.append("".join(cur))
                cur = []
            tokens.append(ch)
            i += 1
            continue
        if not in_quotes and ch.isspace():
            if cur:
                tokens.append("".join(cur))
                cur = []
            i += 1
            continue
        cur.append(ch)
        i += 1
    if cur:
        tokens.append("".join(cur))
    return tokens


def _split_on_and(tokens: list[str]) -> list[list[str]]:
    parts: list[list[str]] = []
    cur: list[str] = []
    for t in tokens:
        if t.lower() == "and":
            if cur:
                parts.append(cur)
                cur = []
            continue
        cur.append(t)
    if cur:
        parts.append(cur)
    return parts


def _eval_condition(words: list[str], env) -> bool:
    # Delegate to full boolean expression evaluator
    return _eval_condition_expr(words, env)


# ---------- Boolean expression parser (recursive descent) ----------

def _eval_condition_expr(words: list[str], env) -> bool:
    # parse tokens into a boolean expression with precedence and parentheses
    toks = _tokenize_condition(words)
    idx = {"i": 0}

    def peek():
        return toks[idx["i"]] if idx["i"] < len(toks) else None

    def consume():
        t = peek()
        idx["i"] += 1
        return t

    def parse_primary():
        t = peek()
        if t is None:
            return False
        if t == "(":
            consume()
            v = parse_or()
            if peek() == ")":
                consume()
            return v
        if t == "not":
            consume()
            return not parse_primary()
        # identifiers / status checks / literals
        return _eval_atom(consume(), env)

    def parse_and():
        v = parse_primary()
        while True:
            t = peek()
            if t == "and":
                consume()
                rhs = parse_primary()
                v = v and rhs
            elif t == "nor":
                consume()
                rhs = parse_primary()
                v = not (v or rhs)
            else:
                break
        return v

    def parse_or():
        v = parse_and()
        while True:
            t = peek()
            if t == "or":
                consume()
                rhs = parse_and()
                v = v or rhs
            else:
                break
        return v

    return bool(parse_or())


def _tokenize_condition(words: list[str]) -> list[str]:
    # words may include parentheses already; also split embedded ones
    out: list[str] = []
    for w in words:
        if w == "":
            continue
        if w == "(" or w == ")":
            out.append(w)
            continue
        if w.startswith("(") or w.endswith(")"):
            s = w
            while s.startswith("("):
                out.append("(")
                s = s[1:]
            trail = 0
            while s.endswith(")"):
                trail += 1
                s = s[:-1]
            if s:
                out.append(s.lower())
            out.extend(")" for _ in range(trail))
            continue
        out.append(w.lower())
    return out


def _eval_atom(atom: str, env) -> bool:
    # Handle simple status checks and comparisons in flat forms around the atom
    # We interpret sequences like: <name> [is|in|for|as] <value>
    if atom in {"true", "yes", "on", "active"}:
        return True
    if atom in {"false", "no", "off", "inactive"}:
        return False
    # status map
    sec = _ensure_sec(env)
    if atom == "tunnel":
        return bool(sec.get("tunnel", False))
    if atom == "firewall":
        return bool(sec.get("firewall", True))
    if atom == "keylogger":
        return bool(sec.get("keylogger", False))
    # FALLBACK: presence of keyword considered truthy
    return atom in _CYBER_KEYWORDS


def _handle_if_chain(tokens: list[str], env) -> None:
    # Supports: if <cond> then <actions> [unless <guard>] [however <cond2> then <actions2>] [yet|else <else-actions>]
    ws = [t.lower() for t in tokens]
    try:
        if_idx = ws.index("if")
    except ValueError:
        return
    # find then or block splitters
    try:
        then_idx = ws.index("then", if_idx + 1)
    except ValueError:
        # if cond {actions} style not supported here; prompt
        print("if: expected 'then' with actions in REPL freeform mode")
        return
    cond_words = tokens[if_idx+1:then_idx]
    rest = tokens[then_idx+1:]
    # handle optional guard: ... unless <guard>
    guard_words: list[str] | None = None
    out_actions = rest
    if "unless" in [r.lower() for r in rest]:
        rlow = [r.lower() for r in rest]
        u = rlow.index("unless")
        out_actions = rest[:u]
        guard_words = rest[u+1:]
    # handle however chains
    branches = [(cond_words, out_actions)]
    tail = rest
    # however cond then actions (can repeat)
    while True:
        rlow = [r.lower() for r in tail]
        if "however" in rlow and "then" in rlow:
            h = rlow.index("however")
            try:
                t = rlow.index("then", h+1)
            except ValueError:
                break
            branches.append((tail[h+1:t], tail[t+1:]))
            tail = tail[t+1:]
            continue
        break
    # optional else/yet/otherwise
    else_actions: list[str] | None = None
    rlow = [r.lower() for r in tail]
    for kw in ("otherwise", "yet", "else"):
        if kw in rlow:
            k = rlow.index(kw)
            else_actions = tail[k+1:]
            break
    # Evaluate in order
    executed = False
    for cwords, actions in branches:
        if _eval_condition(cwords, env):
            if guard_words and _eval_condition(guard_words, env):
                # guarded out
                executed = True
                break
            _execute_actions(actions, env)
            executed = True
            break
    if not executed and else_actions:
        _execute_actions(else_actions, env)


def _handle_loop(tokens: list[str], env) -> None:
    ws = [t.lower() for t in tokens]
    limit = 10  # safety cap
    if "while" in ws:
        i = ws.index("while")
        # expect: while <cond> do <actions>
        if "do" in ws[i+1:]:
            d = ws.index("do", i+1)
            cond = tokens[i+1:d]
            actions = tokens[d+1:]
        else:
            # fallback to then
            if "then" in ws[i+1:]:
                d = ws.index("then", i+1)
                cond = tokens[i+1:d]
                actions = tokens[d+1:]
            else:
                print("while: expected 'do' or 'then'")
                return
        count = 0
        while _eval_condition(cond, env):
            _execute_actions(actions, env)
            count += 1
            if count >= limit:
                print("[warn] while: iteration limit reached")
                break
        return
    if "until" in ws:
        i = ws.index("until")
        # until <cond> do <actions>
        if "do" in ws[i+1:]:
            d = ws.index("do", i+1)
            cond = tokens[i+1:d]
            actions = tokens[d+1:]
        else:
            if "then" in ws[i+1:]:
                d = ws.index("then", i+1)
                cond = tokens[i+1:d]
                actions = tokens[d+1:]
            else:
                print("until: expected 'do' or 'then'")
                return
        count = 0
        while not _eval_condition(cond, env):
            _execute_actions(actions, env)
            count += 1
            if count >= limit:
                print("[warn] until: iteration limit reached")
                break


def _handle_after(tokens: list[str], env) -> None:
    # after <number> (ms|s|seconds|millis) then <actions>
    ws = [t.lower() for t in tokens]
    try:
        i = ws.index("after")
    except ValueError:
        return
    # find numeric value
    delay_ms = 0
    val = None
    unit = "ms"
    for j in range(i+1, len(tokens)):
        w = tokens[j]
        if w.isdigit():
            val = int(w)
            # look ahead for unit
            if j+1 < len(ws):
                u = ws[j+1]
                if u in {"ms", "millis", "milliseconds"}:
                    unit = "ms"
                elif u in {"s", "sec", "secs", "second", "seconds"}:
                    unit = "s"
            break
    if val is None:
        txt = _prompt("Delay milliseconds?")
        try:
            val = int(txt)
        except Exception:
            val = 0
    delay_ms = val if unit == "ms" else int(val * 1000)
    # find actions after 'then' or end
    if "then" in ws:
        t = ws.index("then")
        actions = tokens[t+1:]
    else:
        actions = tokens[j+1:]
    time_mod = env.get("time")
    _call_native(time_mod, "sleep_ms", [delay_ms])
    _execute_actions(actions, env)


def _execute_actions(tokens: list[str], env) -> None:
    # execute chained actions separated by 'and'
    for chain in _split_on_and(tokens):
        for i, t in enumerate(chain):
            key = t.lower()
            if key in _KEYWORD_DISPATCH:
                if _KEYWORD_DISPATCH[key](chain[i:], env):
                    break

def _handle_generate(tokens: list[str], env) -> bool:
    # tokens start with 'generate'
    if len(tokens) == 1:
        # ask what to generate
        kind = _prompt("What would you like to generate? (table/payload)")
        if not kind:
            return True
        tokens = ["generate", kind] + []
    sub = tokens[1].lower() if len(tokens) >= 2 else ""
    if sub == "table":
        _action_generate_table(env, tokens[2:])
        return True
    if sub == "payload":
        # parse pattern: payload for <platform> [version words...]
        platform = None
        version = None
        if "for" in [t.lower() for t in tokens[2:]]:
            idx = [t.lower() for t in tokens].index("for")
            if idx + 1 < len(tokens):
                platform = tokens[idx + 1]
                if idx + 2 < len(tokens):
                    version = " ".join(tokens[idx + 2:])
        if not platform:
            platform = _prompt("Target platform for payload (e.g., android, ios, windows)?") or "unspecified"
        if version is None:
            version = _prompt("Any version or variant? (press Enter to skip)") or ""
        _action_generate_payload(env, platform, version)
        return True
    # unknown subcommand
    print("generate: expected 'table' or 'payload'")
    return True


def _action_generate_table(env, args: list[str]) -> None:
    import hashlib
    import os
    from pathlib import Path
    
    # Create cache directory
    cache_dir = Path.home() / ".aegis" / "cache" / "rainbow_tables"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate actual rainbow table
    table_name = f"rainbow_table_{hashlib.md5(str(os.urandom(8)).encode()).hexdigest()[:8]}.txt"
    table_path = cache_dir / table_name
    
    # Create rainbow table with common passwords
    common_passwords = [
        "password", "123456", "admin", "root", "guest", "user", "test",
        "12345", "qwerty", "abc123", "password123", "admin123", "root123",
        "letmein", "welcome", "monkey", "dragon", "master", "hello",
        "login", "pass", "1234", "123456789", "12345678", "1234567"
    ]
    
    with open(table_path, 'w') as f:
        f.write("# Rainbow Table Generated by Aegis\n")
        f.write(f"# Generated: {os.popen('date').read().strip()}\n")
        f.write("# Hash Algorithm: MD5\n\n")
        
        for password in common_passwords:
            hash_value = hashlib.md5(password.encode()).hexdigest()
            f.write(f"{hash_value}:{password}\n")
    
    # Store table info
    table_info = {
        "type": "rainbow_table",
        "path": str(table_path),
        "size": len(common_passwords),
        "algorithm": "MD5",
        "entries": common_passwords
    }
    
    env.define("LAST_GENERATED", table_info)
    print(f"[ok] Generated rainbow table with {len(common_passwords)} entries")
    print(f"[ok] Saved to: {table_path}")


def _action_generate_payload(env, platform: str, version: str) -> None:
    import os
    import hashlib
    from pathlib import Path
    
    # Create cache directory
    cache_dir = Path.home() / ".aegis" / "cache" / "payloads"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate actual payload
    payload_name = f"payload_{platform}_{version}_{hashlib.md5(str(os.urandom(8)).encode()).hexdigest()[:8]}.aeg"
    payload_path = cache_dir / payload_name
    
    # Create platform-specific payload
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if platform.lower() in ["android", "andriod"]:
        payload_code = f'''~ Android {version} Payload Generated by Aegis
~ Target: {platform} {version}
~ Generated: {timestamp}

def android_payload() {{
    ~ Android-specific payload code
    set target = "{platform} {version}"
    set action = "exploit"
    
    ~ Simulate Android exploit
    set message = "Executing Android payload for " + target
    
    ~ Return success status
    return {{"status": "success", "target": target, "message": message}}
}}

~ Execute payload
android_payload()
'''
    elif platform.lower() in ["windows", "win"]:
        payload_code = f'''~ Windows {version} Payload Generated by Aegis
~ Target: {platform} {version}
~ Generated: {timestamp}

def windows_payload() {{
    ~ Windows-specific payload code
    set target = "{platform} {version}"
    set action = "exploit"
    
    ~ Simulate Windows exploit
    set message = "Executing Windows payload for " + target
    
    ~ Return success status
    return {{"status": "success", "target": target, "message": message}}
}}

~ Execute payload
windows_payload()
'''
    else:
        payload_code = f'''~ {platform} {version} Payload Generated by Aegis
~ Target: {platform} {version}
~ Generated: {timestamp}

def generic_payload() {{
    ~ Generic payload code
    set target = "{platform} {version}"
    set action = "exploit"
    
    ~ Simulate generic exploit
    set message = "Executing payload for " + target
    
    ~ Return success status
    return {{"status": "success", "target": target, "message": message}}
}}

~ Execute payload
generic_payload()
'''
    
    # Write payload to file
    with open(payload_path, 'w') as f:
        f.write(payload_code)
    
    # Store payload info
    payload_info = {
        "type": "payload",
        "platform": platform,
        "version": version,
        "path": str(payload_path),
        "size": len(payload_code),
        "code": payload_code
    }
    
    env.define("LAST_GENERATED", payload_info)
    pretty = platform + (" " + version if version else "")
    print(f"[ok] Generated {pretty} payload")
    print(f"[ok] Saved to: {payload_path}")
    print(f"[ok] Payload size: {len(payload_code)} characters")


def _prompt(message: str) -> str:
    try:
        return input(f"? {message} ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return ""


# Registry for extensibility
_KEYWORD_DISPATCH = {
    "generate": _handle_generate,
}


# ---------------- Additional cybersecurity keyword handlers ----------------

def _ensure_sec(env):
    try:
        sec = env.get("SECURITY")
    except Exception:
        sec = {"tunnel": False, "firewall": True, "keylogger": False}
        env.define("SECURITY", sec)
    return sec


def _record_action(env, action: str, detail: str = "") -> None:
    try:
        actions = env.get("LAST_ACTIONS")
    except Exception:
        actions = []
        env.define("LAST_ACTIONS", actions)
    actions.append({"action": action, "detail": detail})


def _call_native(mod, name: str, args: list):
    fn = mod.get(name)
    if fn is None:
        return None
    return fn(args)


def _handle_firewall(tokens: list[str], env) -> bool:
    sec = _ensure_sec(env)
    # detect desired state in tokens
    words = [t.lower() for t in tokens]
    if "down" in words or "disable" in words or "deactivate" in words:
        sec["firewall"] = False
        print("[ok] Firewall set to down (stub)")
    elif "up" in words or "enable" in words or "activate" in words:
        sec["firewall"] = True
        print("[ok] Firewall set to up (stub)")
    else:
        sec["firewall"] = not sec.get("firewall", True)
        print(f"[ok] Firewall toggled to {'up' if sec['firewall'] else 'down'} (stub)")
    _record_action(env, "firewall", "toggle")
    return True


def _handle_tunnel(tokens: list[str], env) -> bool:
    sec = _ensure_sec(env)
    words = [t.lower() for t in tokens]
    if "active" in words or "up" in words or "on" in words or "activate" in words:
        sec["tunnel"] = True
        print("[ok] Tunnel set to active (stub)")
    elif "inactive" in words or "down" in words or "off" in words or "deactivate" in words:
        sec["tunnel"] = False
        print("[ok] Tunnel set to inactive (stub)")
    else:
        sec["tunnel"] = not sec.get("tunnel", False)
        print(f"[ok] Tunnel toggled to {'active' if sec['tunnel'] else 'inactive'} (stub)")
    _record_action(env, "tunnel", "toggle")
    return True


def _handle_keylogger(tokens: list[str], env) -> bool:
    sec = _ensure_sec(env)
    # detection is a stub: set flag if words contain detected
    detected = any(t.lower() in {"detected", "present", "found"} for t in tokens)
    sec["keylogger"] = detected
    print(f"[ok] Keylogger status: {'detected' if detected else 'not detected'} (stub)")
    _record_action(env, "keylogger", "status")
    return True


def _handle_hash(tokens: list[str], env) -> bool:
    text = " ".join(tokens[1:]) if len(tokens) > 1 else ""
    if not text:
        text = _prompt("Text to hash?")
    if not text:
        return True
    crypto = env.get("crypto")
    digest = _call_native(crypto, "sha256", [text])
    print(digest)
    _record_action(env, "hash", text)
    return True


def _handle_encrypt(tokens: list[str], env) -> bool:
    text = " ".join(tokens[1:]) if len(tokens) > 1 else ""
    if not text:
        text = _prompt("Text to encode (base64 stub)?")
    if not text:
        return True
    encoding = env.get("encoding")
    out = _call_native(encoding, "base64_encode", [text])
    print(out)
    _record_action(env, "encrypt", "base64")
    return True


def _handle_decrypt(tokens: list[str], env) -> bool:
    text = " ".join(tokens[1:]) if len(tokens) > 1 else ""
    if not text:
        text = _prompt("Base64 to decode?")
    if not text:
        return True
    encoding = env.get("encoding")
    out = _call_native(encoding, "base64_decode", [text])
    print(out)
    _record_action(env, "decrypt", "base64")
    return True


def _handle_inject(tokens: list[str], env) -> bool:
    target = " ".join(tokens[1:]) if len(tokens) > 1 else ""
    if not target:
        target = _prompt("Inject into what target?")
    
    # Check if we have a payload to inject
    try:
        last_generated = env.get("LAST_GENERATED")
        if last_generated and last_generated.get("type") == "payload":
            payload_path = last_generated.get("path")
            if payload_path and Path(payload_path).exists():
                # Execute the payload
                print(f"[ok] Injecting payload from {payload_path} into {target}")
                try:
                    with open(payload_path, 'r') as f:
                        payload_code = f.read()
                    
                    # Parse and execute the payload
                    from .parser import parse
                    from .interpreter import evaluate
                    program = parse(payload_code)
                    result = evaluate(program, env)
                    
                    print(f"[ok] Payload executed successfully on {target}")
                    if result:
                        print(f"[ok] Result: {result}")
                except Exception as e:
                    print(f"[error] Failed to execute payload: {e}")
            else:
                print(f"[error] Payload file not found: {payload_path}")
        else:
            print(f"[error] No payload available. Generate one first with 'payload' command.")
    except Exception:
        print(f"[error] No payload available. Generate one first with 'payload' command.")
    
    _record_action(env, "inject", target)
    return True


def _handle_attack(tokens: list[str], env) -> bool:
    print("[ok] Attack action queued (stub)")
    _record_action(env, "attack")
    return True


def _handle_defend(tokens: list[str], env) -> bool:
    print("[ok] Defend action engaged (stub)")
    _record_action(env, "defend")
    return True


def _handle_activate(tokens: list[str], env) -> bool:
    print("[ok] Activated (stub)")
    _record_action(env, "activate", " ".join(tokens[1:]))
    return True


def _handle_deactivate(tokens: list[str], env) -> bool:
    print("[ok] Deactivated (stub)")
    _record_action(env, "deactivate", " ".join(tokens[1:]))
    return True


def _ensure_store(env):
    try:
        store = env.get("DATASTORE")
    except Exception:
        store = {}
        env.define("DATASTORE", store)
    return store


def _handle_read(tokens: list[str], env) -> bool:
    store = _ensure_store(env)
    key = tokens[1] if len(tokens) > 1 else _prompt("Key to read?")
    if not key:
        return True
    print(store.get(key))
    _record_action(env, "read", key)
    return True


def _handle_write(tokens: list[str], env) -> bool:
    store = _ensure_store(env)
    key = tokens[1] if len(tokens) > 1 else _prompt("Key to write?")
    if not key:
        return True
    value = " ".join(tokens[2:]) if len(tokens) > 2 else _prompt("Value?")
    store[key] = value
    print("[ok] written")
    _record_action(env, "write", key)
    return True


def _handle_save(tokens: list[str], env) -> bool:
    return _handle_write(tokens, env)


def _handle_load(tokens: list[str], env) -> bool:
    return _handle_read(tokens, env)


def _handle_analyze(tokens: list[str], env) -> bool:
    text = " ".join(tokens[1:]) if len(tokens) > 1 else _prompt("What to analyze?")
    print(f"[ok] Analyzed (stub): {text}")
    _record_action(env, "analyze", text)
    return True


def _handle_protect(tokens: list[str], env) -> bool:
    print("[ok] Protection enabled (stub)")
    _record_action(env, "protect")
    return True


def _handle_override(tokens: list[str], env) -> bool:
    print("[ok] Override issued (stub)")
    _record_action(env, "override")
    return True


def _handle_contain(tokens: list[str], env) -> bool:
    print("[ok] Incident contained (stub)")
    _record_action(env, "contain")
    return True


def _handle_payload(tokens: list[str], env) -> bool:
    # Direct payload generation - no "generate" prefix needed
    if len(tokens) == 1:
        # Just "payload" - ask for platform
        platform = _prompt("Target platform for payload (e.g., android, ios, windows)?") or "unspecified"
        version = _prompt("Any version or variant? (press Enter to skip)") or ""
        _action_generate_payload(env, platform, version)
        return True
    
    # Parse: payload for <platform> [version]
    platform = None
    version = None
    if "for" in [t.lower() for t in tokens[1:]]:
        idx = [t.lower() for t in tokens].index("for")
        if idx + 1 < len(tokens):
            platform = tokens[idx + 1]
            if idx + 2 < len(tokens):
                version = " ".join(tokens[idx + 2:])
    
    if not platform:
        platform = _prompt("Target platform for payload (e.g., android, ios, windows)?") or "unspecified"
    if version is None:
        version = _prompt("Any version or variant? (press Enter to skip)") or ""
    
    _action_generate_payload(env, platform, version)
    return True


def _handle_table(tokens: list[str], env) -> bool:
    return _handle_generate(["generate", "table"] + tokens[1:], env)


def _handle_brute(tokens: list[str], env) -> bool:
    print("[ok] Brute action stubbed (no real brute-force)")
    _record_action(env, "brute")
    return True


def _handle_break(tokens: list[str], env) -> bool:
    print("[ok] Breakpoint reached (stub)")
    _record_action(env, "break")
    return True


def _handle_pause(tokens: list[str], env) -> bool:
    dur = tokens[1] if len(tokens) > 1 else _prompt("Pause milliseconds?")
    try:
        ms = int(dur)
    except Exception:
        ms = 250
    time_mod = env.get("time")
    _call_native(time_mod, "sleep_ms", [ms])
    print(f"[ok] Paused {ms}ms")
    _record_action(env, "pause", str(ms))
    return True


def _handle_enter(tokens: list[str], env) -> bool:
    print("[ok] Enter scope (stub)")
    _record_action(env, "enter")
    return True


def _handle_exit(tokens: list[str], env) -> bool:
    print("[ok] Exit scope (stub) — use .exit to leave REPL")
    _record_action(env, "exit")
    return True


def _handle_corrupt(tokens: list[str], env) -> bool:
    print("[ok] Corrupt action ignored (stub)")
    _record_action(env, "corrupt")
    return True


def _handle_manipulate(tokens: list[str], env) -> bool:
    print("[ok] Manipulate action stub")
    _record_action(env, "manipulate")
    return True


def _handle_trace(tokens: list[str], env) -> bool:
    target = " ".join(tokens[1:]) if len(tokens) > 1 else "system"
    print(f"[ok] Tracing {target} (stub)")
    _record_action(env, "trace", target)
    return True


def _handle_monitor(tokens: list[str], env) -> bool:
    target = " ".join(tokens[1:]) if len(tokens) > 1 else "system"
    # Use the real monitor function if available
    try:
        monitor_func = env.get("monitor")
        if monitor_func:
            result = monitor_func([target, 1])
            if result.get("success"):
                print(f"[ok] Monitoring {target} - CPU: {result['metrics']['cpu_percent']}%")
            else:
                print(f"[error] Monitor failed: {result.get('error', 'Unknown error')}")
        else:
            print(f"[ok] Monitoring {target} (stub)")
    except Exception as e:
        print(f"[ok] Monitoring {target} (stub) - {e}")
    _record_action(env, "monitor", target)
    return True


def _handle_quarantine(tokens: list[str], env) -> bool:
    target = " ".join(tokens[1:]) if len(tokens) > 1 else "threat"
    print(f"[ok] Quarantined {target} (stub)")
    _record_action(env, "quarantine", target)
    return True


def _handle_alert(tokens: list[str], env) -> bool:
    message = " ".join(tokens[1:]) if len(tokens) > 1 else "Security alert"
    print(f"[ALERT] {message}")
    _record_action(env, "alert", message)
    return True


# Extend dispatch table
_KEYWORD_DISPATCH.update({
    "firewall": _handle_firewall,
    "tunnel": _handle_tunnel,
    "keylogger": _handle_keylogger,
    "hash": _handle_hash,
    "encrypt": _handle_encrypt,
    "decrypt": _handle_decrypt,
    "inject": _handle_inject,
    "attack": _handle_attack,
    "defend": _handle_defend,
    "activate": _handle_activate,
    "deactivate": _handle_deactivate,
    "read": _handle_read,
    "write": _handle_write,
    "save": _handle_save,
    "load": _handle_load,
    "analyze": _handle_analyze,
    "protect": _handle_protect,
    "override": _handle_override,
    "contain": _handle_contain,
    "payload": _handle_payload,
    "table": _handle_table,
    "brute": _handle_brute,
    "break": _handle_break,
    "pause": _handle_pause,
    "enter": _handle_enter,
    "exit": _handle_exit,
    "corrupt": _handle_corrupt,
    "manipulate": _handle_manipulate,
    # flow readability no-ops
    "before": lambda t,e: True,
    "since": lambda t,e: True,
    "because": lambda t,e: True,
    # new executable context keywords
    "trace": lambda t,e: _handle_trace(t,e),
    "monitor": lambda t,e: _handle_monitor(t,e),
    "quarantine": lambda t,e: _handle_quarantine(t,e),
    "alert": lambda t,e: _handle_alert(t,e),
})


# Keyword list for scanning
_CYBER_KEYWORDS = {
    "override", "firewall", "tunnel", "keylogger", "generate", "hash", "encrypt", "decrypt",
    "protect", "attack", "defend", "activate", "deactivate", "analyze", "contain", "payload",
    "load", "manipulate", "inject", "read", "write", "save", "corrupt", "break", "pause",
    "enter", "exit", "table", "brute", "trace", "monitor", "quarantine", "alert",
}


# ---------------- Syntax colorization ----------------

REPL_COLORIZE = True

COLOR_SCHEME = {
    "control": "\x1b[38;5;81m",      # Color A
    "loop": "\x1b[38;5;135m",         # Color B
    "logical": "\x1b[38;5;178m",      # Color C
    "cyber": "\x1b[38;5;203m",        # Color D
    "number": "\x1b[38;5;71m",        # Color E
    "symbol": "\x1b[38;5;244m",       # Color F
    "reset": "\x1b[0m",
}

_CONTROL_FLOW_WORDS = {"if", "then", "else", "however", "unless", "yet"}
_LOOP_WORDS = {"while", "do", "when"}
_LOGICAL_WORDS = {"and", "or", "not", "nor", "as", "is", "for", "in"}


def _print_colorized(s: str) -> None:
    try:
        colored = _colorize_line(s)
        if colored != s:
            print(colored)
    except Exception:
        # fail-open: no colorization on error
        pass


def _colorize_line(s: str) -> str:
    # Split by quotes to avoid coloring inside strings
    parts: list[str] = []
    buf: list[str] = []
    in_quotes = False
    for ch in s:
        if ch == '"':
            if buf:
                parts.append(_colorize_segment("".join(buf)))
                buf = []
            parts.append('"')
            in_quotes = not in_quotes
            continue
        if in_quotes:
            parts.append(ch)
            continue
        buf.append(ch)
    if buf:
        parts.append(_colorize_segment("".join(buf)))
    return "".join(parts)


def _colorize_segment(seg: str) -> str:
    if not seg:
        return seg
    out: list[str] = []
    i = 0
    while i < len(seg):
        ch = seg[i]
        if ch.isalpha() or ch == "_":
            j = i
            while j < len(seg) and (seg[j].isalnum() or seg[j] == "_"):
                j += 1
            word = seg[i:j]
            low = word.lower()
            color = None
            if low in _CYBER_KEYWORDS:
                color = COLOR_SCHEME["cyber"]
            elif low in _CONTROL_FLOW_WORDS:
                color = COLOR_SCHEME["control"]
            elif low in _LOOP_WORDS:
                color = COLOR_SCHEME["loop"]
            elif low in _LOGICAL_WORDS:
                color = COLOR_SCHEME["logical"]
            if color:
                out.append(f"{color}{word}{COLOR_SCHEME['reset']}")
            else:
                out.append(word)
            i = j
            continue
        if ch.isdigit():
            j = i
            has_dot = False
            while j < len(seg) and (seg[j].isdigit() or (seg[j] == "." and not has_dot)):
                if seg[j] == ".":
                    has_dot = True
                j += 1
            num = seg[i:j]
            out.append(f"{COLOR_SCHEME['number']}{num}{COLOR_SCHEME['reset']}")
            i = j
            continue
        if ch in "=+-*/(){}[]:;. ,":
            out.append(f"{COLOR_SCHEME['symbol']}{ch}{COLOR_SCHEME['reset']}")
            i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def main():
    """Entry point for the aegis command."""
    try:
        start_repl()
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        print(f"Error: {e}")
        return 1
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
