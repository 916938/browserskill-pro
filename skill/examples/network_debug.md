# Network Debugging

Use `network` only when the user specifically asks for request-level diagnosis.

1. State what request family you need to inspect, such as API calls for a save button.
2. Start narrow capture with a filter when the daemon supports it.
3. Avoid collecting or returning `Cookie`, `Set-Cookie`, `Authorization`, token-bearing query strings, or unrelated request bodies.
4. Stop capture as soon as the relevant request is found.
5. Summarize method, URL path, status, timing, and high-level error body only when it is safe.

If the bug can be diagnosed from DOM text, URL, title, console-visible state, or screenshots, prefer those lower-risk tools before `network`.

