# TODO

## User pages (authentication + recycling points)

- [ ] Add `users` and `recycling_entries` tables to `bins.db` (via `app.py` init)
- [ ] Seed a default user for demo (so login works without registering)
- [ ] Add endpoints:
  - [ ] `POST /user/register`
  - [ ] `POST /user/login`
  - [ ] `POST /user/logout`
  - [ ] `GET /user/session`
  - [ ] `POST /user/recycle` (record today’s recycle + award points)
  - [ ] `GET /user/profile` (points + recent entries)
- [x] Add new pages under `static/`:
  - [x] `static/user.html` (login + recycle form + points dashboard)
  - [x] `static/user.js` (client logic)
- [ ] Wire navigation link from `index.html` to `static/user.html`
- [ ] Add server-side point calculation rule (demo): points = floor(amountKg * 2)
- [ ] Basic security:
  - [ ] store password as hash (werkzeug)
  - [ ] validate username + amount inputs

## Testing

- [ ] Run server and verify demo login
- [ ] Verify recording a recycle entry awards points and updates UI
- [ ] Verify unauthorized access is blocked

