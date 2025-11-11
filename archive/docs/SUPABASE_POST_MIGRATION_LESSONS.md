# Supabase Post-Migration Lessons

## Overview
After migrating Curriculum Studio's authentication workflow to Supabase (November 2025), we encountered a series of regressions during end-to-end testing on Streamlit Cloud. This document records the issues, root causes, fixes, and lessons learned so future maintenance cycles can avoid the same pitfalls.

## Key Issues & Fixes

### 1. Login Success → Instant Logout Loop
- **Symptom**: Users saw “Welcome back!” then were immediately redirected to the login page.
- **Root Cause**: Streamlit reruns cleared Supabase sessions. `supabase.auth.get_session()` returned empty after each rerun because the cached client owned the session, not the current user.
- **Fix**:
  - Removed `@st.cache_resource` from `get_supabase_client()` so each request creates a fresh client.
  - Persisted Supabase access/refresh tokens in `st.session_state` and revalidated sessions using `auth.get_user(access_token)`.
  - Added a refresh-path fallback using `auth.refresh_session(refresh_token)`.

### 2. Theme Configuration Crash
- **Symptom**: Background color reset to Streamlit default and console spammed `Invalid color passed for widgetBackgroundColor`.
- **Root Cause**: Temporary `.streamlit/config.toml` with empty theme values caused Streamlit to throw parse errors on every render.
- **Fix**: Deleted the broken config file and let the app fall back to default theming.

### 3. Admin Role Not Recognized
- **Symptom**: Admin e-mail logged in successfully but saw “Access Denied: Admin privileges required.”
- **Root Cause**: Role lookup queried the `curriculum_studio_users` table using the anonymous Supabase client, which is blocked by RLS.
- **Fix**: Switched role lookup to use the Supabase admin client (service role key) and added debug logging for role queries.

### 4. Hidden State Failures
- **Challenge**: Debugging was difficult without visibility into Supabase responses.
- **Fix**: Added an optional `DEBUG_AUTH` flag that surfaces masked tokens, Supabase API responses, and role lookup diagnostics in a “🔍 Auth Debug” panel. Setting `DEBUG_AUTH=2` in Streamlit secrets auto-expands the panel during testing.

## Lessons Learned
1. **Avoid Caching Auth Clients**: Session-bound auth clients should not be memoized across users. Each request/user needs an isolated client to avoid shared session state.
2. **Always Persist Tokens Explicitly**: Even when Supabase handles persistence in other environments, Streamlit reruns make it essential to save access & refresh tokens and rehydrate sessions manually.
3. **Debugging Hooks Matter**: A lightweight debug overlay (behind a feature flag) is invaluable when diagnosing hosted environments where logs are sparse.
4. **Respect RLS Boundaries**: Use the admin client for tables protected by row-level security, even if they “look” accessible.
5. **Keep Theme Config Simple**: Avoid untested `.streamlit/config.toml` tweaks in production unless they’re well-validated locally.

## Action Items
- Keep `DEBUG_AUTH` set to `0` in production, but document how to enable it during incident response.
- Document Supabase environment prerequisites (Site URL, Redirect URLs) alongside secrets so new deployments don’t miss required settings.
- Schedule a periodic audit (monthly) ensuring admin accounts retain correct roles and Supabase auth settings.

---
*Document created: 2025-11-11*
*Maintainers: Curriculum Studio Engineering*
