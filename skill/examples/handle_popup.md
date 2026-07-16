# Handle Popup or Background Tab

Use this pattern after clicking a link or button that appears to do nothing.

1. Do not repeat the original click immediately.
2. Run `wait_for.py` for the expected URL, title, or visible text.
3. Take a fresh `snapshot.py --auto` and compare URL/title.
4. List tabs in the session with `tab_list`:

   ```powershell
   & scripts\invoke.ps1 -Session "popup-task" -Action "tab_list"
   ```

5. If a new destination tab exists, activate it for the session with `tab_select` (pass its `tab_id`).
6. If no tab appears, the browser may have blocked a popup or new window. Ask the user to allow popups for that site, then retry once.
7. If the clicked element is a link, recover its real `href` with bounded `evaluate`, then call `navigate` directly.

