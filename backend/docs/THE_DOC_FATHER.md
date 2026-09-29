# THE DOC FATHER

All you need to get started
🏊🏿‍♂️
🏊🏿‍♂️
🏊🏿‍♂️
🏊🏿‍♂️
🏊🏿‍♂️
---

## Global Standards

**Base URL:** `/api`

**Request Headers (authenticated endpoints):**
```
Content-Type: application/json
Authorization: Bearer <supabase_jwt>
```

**How errors look like:**
```json
{ "detail": "Human-readable error message" }
```

**Validation error envelope (422):**
```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "error description",
      "type": "error_type"
    }
  ]
}
```

**Auth:** JWT issued by Supabase. Validated against JWKS (`{SUPABASE_URL}/auth/v1/.well-known/jwks.json`) or `SUPABASE_JWT_SECRET` fallback.
- Issuer: `{SUPABASE_URL}/auth/v1`
- Audience: `"authenticated"`
- **Admin role:** must be set in JWT `app_metadata.role == "admin"` — NOT `user_metadata`

**How the frontend authenticates:** Use the Supabase JS client (`@supabase/supabase-js`) to sign in — call `supabase.auth.signInWithPassword(...)` (or OAuth equivalent) against `https://<your-supabase-project>.supabase.co`. Supabase returns an `access_token` (a JWT). Pass that token as `Authorization: Bearer <access_token>` on every request to this backend and the backend validates it automatically. To get the current session token at any time call `supabase.auth.getSession()` and read `session.access_token`.

> **Secrets:** The Supabase project URL and anon key you need to initialise the client are stored in the repository's GitHub Secrets. check the repo Settings → Secrets and variables → Actions.
>
> **⚠️ Do NOT use the service role key on the frontend.** That key has full database access. Only the `anon` public key goes in client-side code.

---

## Endpoint Index

| Method | Path | Auth |
|--------|------|------|
| GET | `/api/health` | Public |
| GET | `/api/auth/me` | User |
| GET | `/api/auth/admin/status` | User |
| POST | `/api/waitlist` | Public |
| GET | `/api/assessments/me` | User |
| PUT | `/api/assessments/me` | User |
| POST | `/api/assessments/submit` | User |
| POST | `/api/recommendations/generate` | User |
| GET | `/api/recommendations/me` | User |
| PATCH | `/api/recommendations/me/progress` | User |
| PATCH | `/api/recommendations/admin/users/{user_id}` | Admin |
| GET | `/api/recommendations/admin/rules` | Admin |
| PATCH | `/api/recommendations/admin/rules/{problem_id}` | Admin |
| GET | `/api/recommendations/admin/protocols` | Admin |
| PATCH | `/api/recommendations/admin/protocols/{protocol_id}` | Admin |
| GET | `/api/followups/me` | User |
| GET | `/api/followups/me/next` | User |
| POST | `/api/followups/{followup_id}/check-in` | User |

---

## Health

### `GET /api/health`

**Auth:** None

**Success `200`:**
```json
{
  "status": "healthy",
  "app": "EVOLVE MVP",
  "version": "0.1.0"
}
```

No failure cases.

---

## Auth

### `GET /api/auth/me`

**Auth:** Required (any authenticated user)

**Success `200`:**
```json
{
  "uid": "a1b2c3d4-0000-0000-0000-111122223333",
  "email": "jane@example.com",
  "display_name": "Jane Doe",
  "is_active": true,
  "is_admin": false,
  "created_at": "2026-01-01T00:00:00Z"
}
```

| Field | Type | Notes |
|-------|------|-------|
| `uid` | `string` | Supabase user UUID |
| `email` | `string \| null` | May be null |
| `display_name` | `string \| null` | May be null |
| `is_active` | `boolean` | Always `true` for valid JWTs |
| `is_admin` | `boolean` | Derived from `app_metadata.role` in JWT |
| `created_at` | `ISO 8601 datetime` | |

**Failures:**

| Code | Body | What the client did |
|------|------|---------------------|
| `401` | `{"detail": "Not authenticated"}` | Sent no `Authorization` header, or the token was garbage |
| `401` | `{"detail": "Token has expired"}` | Token was valid but the session expired — call `supabase.auth.refreshSession()` and retry |
| `401` | `{"detail": "Invalid token"}` | Token was tampered with or signed with the wrong secret |

---

### `GET /api/auth/admin/status`

**Auth:** Required (any authenticated user)

**Success `200`:**
```json
{ "is_admin": true }
```

**Failures:** Same as `GET /api/auth/me`.

---

## Waitlist

### `POST /api/waitlist`

**Auth:** None

**Request body:**
```json
{
  "email": "jane@example.com",
  "name": "Jane Doe",
  "flag_code": "SCARRING_ALOPECIA",
  "notes": "Noticed thinning patches over the last 6 months"
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `email` | `string` | Yes | Valid email format |
| `name` | `string \| null` | No | Max 100 chars |
| `flag_code` | `string \| null` | No | Max 64 chars |
| `notes` | `string \| null` | No | Max 2000 chars |

**Behavior:**
- Email is normalized to lowercase and trimmed.
- If the email already exists, the entry is updated with any new `name`, `flag_code`, or `notes` provided in the current payload.
- Confirmation email is sent (background task) only on **new** signups.

**Success `201` (new signup):**
```json
{
  "id": "d9f3a1b2-aaaa-bbbb-cccc-000011112222",
  "email": "jane@example.com",
  "name": "Jane Doe",
  "flag_code": "SCARRING_ALOPECIA",
  "notes": "Noticed thinning patches over the last 6 months",
  "created_at": "2026-01-15T10:30:00Z",
  "message": "Waitlist signup confirmed. A confirmation email has been sent."
}
```

**Success `201` (existing email re-submitted):**

Same shape. `flag_code` and `notes` reflect only what was in the **current** request payload — previously stored values are never leaked back. `message` will be `"Waitlist entry updated."`.

**Failures:**

| Code | Body | What the client did |
|------|------|---------------------|
| `422` | `{"detail": [{"loc": ["body", "email"], "msg": "value is not a valid email address", "type": "value_error"}]}` | Sent `"email": "notanemail"` |
| `422` | `{"detail": [{"loc": ["body", "name"], "msg": "String should have at most 100 characters", "type": "string_too_long"}]}` | Sent a `name` longer than 100 characters |
| `422` | `{"detail": [{"loc": ["body", "notes"], "msg": "String should have at most 2000 characters", "type": "string_too_long"}]}` | Sent `notes` exceeding 2000 characters |

---

## Assessments

### `GET /api/assessments/me`

**Auth:** Required

**Success `200`:**
```json
{
  "user_id": "a1b2c3d4-0000-0000-0000-111122223333",
  "status": "completed",
  "current_step": "completed",
  "answers": {
    "hair_type": "4c",
    "scalp_condition": "dry",
    "breakage_level": "moderate"
  },
  "results": {
    "traits": {
      "scalp_type": "dry",
      "porosity": "high",
      "elasticity": "low",
      "thickness": "fine",
      "density": "medium"
    },
    "flags": [
      { "affects": "elasticity", "message": "Low protein retention detected" }
    ],
    "tier": "GREEN",
    "flag_code": null,
    "trigger_reason": null,
    "escalation_flags": [],
    "referral_summary": null
  },
  "updated_at": "2026-01-15T10:30:00Z"
}
```

`status` values: `"in_progress"` | `"completed"` | `"escalated"`

`results` is `null` when the assessment is still in progress.

When `status` is `"escalated"`, `results.tier` is `"RED"` and `results.referral_summary` contains clinical referral data:
```json
{
  "results": {
    "tier": "RED",
    "flag_code": "SCARRING_ALOPECIA",
    "trigger_reason": "Scarring pattern detected",
    "referral_summary": {
      "urgency": "high",
      "recommended_specialist": "dermatologist",
      "notes": "Seek professional evaluation before starting any hair routine"
    }
  }
}
```

**Failures:**

| Code | Body | What the client did |
|------|------|---------------------|
| `401` | `{"detail": "Not authenticated"}` | No or invalid `Authorization` header |
| `404` | `{"detail": "Assessment not found"}` | The user has never submitted or drafted an assessment |

---

### `PUT /api/assessments/me`

Saves a draft (in-progress) assessment. Overwrites previous answers. Does not run the engine.

**Auth:** Required

**Request body:**
```json
{
  "current_step": "C",
  "answers": {
    "hair_type": "3b",
    "porosity_test": "floats",
    "scalp_feel": "normal"
  }
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `current_step` | `string` | No | Default `"A"`. Tracks UI step: A–F |
| `answers` | `object` | No | Key-value pairs; any shape accepted |

**Success `200`:** Same shape as `GET /api/assessments/me`. `results` is always `null`, `status` is always `"in_progress"`.

**Failures:**

| Code | Body | What the client did |
|------|------|---------------------|
| `401` | `{"detail": "Not authenticated"}` | No or invalid `Authorization` header |
| `422` | Validation error envelope | Sent `answers` as a string or array instead of an object |

---

### `POST /api/assessments/submit`

Finalizes the assessment. Runs escalation engine + trait evaluation. Locks in results.

**Auth:** Required

**Request body:**
```json
{
  "answers": {
    "hair_type": "4c",
    "scalp_condition": "itchy_flaking",
    "breakage_level": "severe",
    "shedding": "excessive",
    "history": "recent_thinning"
  }
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `answers` | `object` | Yes | Finalized answers dictionary — must not be omitted or null |

**Success `200` (non-escalated):**
```json
{
  "user_id": "a1b2c3d4-0000-0000-0000-111122223333",
  "status": "completed",
  "current_step": "completed",
  "answers": { "hair_type": "4c", "scalp_condition": "dry" },
  "results": {
    "traits": {
      "scalp_type": "dry",
      "porosity": "high",
      "elasticity": "low",
      "thickness": "fine",
      "density": "medium"
    },
    "flags": [],
    "tier": "GREEN",
    "flag_code": null,
    "trigger_reason": null,
    "escalation_flags": [],
    "referral_summary": null
  },
  "updated_at": "2026-01-15T10:30:00Z"
}
```

**Success `200` (escalated — answers triggered clinical concern):**
```json
{
  "user_id": "a1b2c3d4-0000-0000-0000-111122223333",
  "status": "escalated",
  "current_step": "completed",
  "answers": { "scalp_condition": "scarring", "history": "recent_thinning" },
  "results": {
    "traits": { "scalp_type": "dry", "porosity": "high", "elasticity": "low", "thickness": "fine", "density": "low" },
    "flags": [{ "affects": "scalp", "message": "Possible scarring alopecia pattern" }],
    "tier": "RED",
    "flag_code": "SCARRING_ALOPECIA",
    "trigger_reason": "Scarring pattern with recent thinning detected",
    "escalation_flags": ["SCARRING_ALOPECIA"],
    "referral_summary": {
      "urgency": "high",
      "recommended_specialist": "dermatologist"
    }
  },
  "updated_at": "2026-01-15T10:30:00Z"
}
```

**Failures:**

| Code | Body | What the client did |
|------|------|---------------------|
| `401` | `{"detail": "Not authenticated"}` | No or invalid `Authorization` header |
| `422` | `{"detail": [{"loc": ["body", "answers"], "msg": "Field required", "type": "missing"}]}` | Omitted the `answers` field entirely |
| `422` | `{"detail": [{"loc": ["body", "answers"], "msg": "Input should be a valid dictionary", "type": "dict_type"}]}` | Sent `"answers": ["hair_type", "4c"]` (array instead of object) |

---

## Recommendations

### `POST /api/recommendations/generate`

Runs the recommendation engine against the user's completed assessment and saves the resulting routine. Automatically schedules follow-up check-ins at weeks 2, 4, and 8. If a routine already exists, it is fully reset and rescheduled.

**Auth:** Required

**Request body:**
```json
{
  "concern": "breakage",
  "tier": "GREEN"
}
```

| Field | Type | Required | Allowed values |
|-------|------|----------|----------------|
| `concern` | `string` | Yes | `"breakage"` `"dryness"` `"split_ends"` `"length_retention"` `"stunted_growth"` `"scalp"` `"tangling"` `"over_conditioning"` `"hygral_fatigue"` |
| `tier` | `string \| null` | No | `"GREEN"` `"AMBER"` `"RED"` — sending `"RED"` immediately blocks the request |

**Success `200`:**
```json
{
  "user_id": "a1b2c3d4-0000-0000-0000-111122223333",
  "active_problems": ["breakage", "dryness"],
  "cause_explanation_keys": ["low_elasticity", "high_porosity"],
  "protocols": ["moisture_retention", "protein_balance"],
  "roadmap": [
    {
      "phase": 1,
      "name": "Foundation",
      "days": "1-30",
      "actions": [
        {
          "id": "moisturize_daily",
          "type": "routine",
          "instruction": "Apply leave-in conditioner on damp hair",
          "class": "moisturize",
          "cadence": "daily",
          "evidence": "Reduces hygral stress on high-porosity strands",
          "caution_note": null
        }
      ],
      "checkpoint_day": 30,
      "checkpoint_metric": "breakage_reduction"
    },
    {
      "phase": 2,
      "name": "Strengthening",
      "days": "31-60",
      "actions": [
        {
          "id": "protein_treatment_weekly",
          "type": "treatment",
          "instruction": "Apply light protein treatment once per week",
          "class": "protein",
          "cadence": "weekly",
          "evidence": "Restores elasticity in low-elasticity hair",
          "caution_note": "Do not over-apply — protein overload causes brittleness"
        }
      ],
      "checkpoint_day": 60,
      "checkpoint_metric": "elasticity_improvement"
    }
  ],
  "product_weight_ceiling": "light",
  "hard_guards_fired": [],
  "realistic_timeline_weeks": { "breakage": 12, "dryness": 8 },
  "is_customized": false,
  "admin_notes": null,
  "current_phase": 1,
  "current_day": 1,
  "started_at": null,
  "completed_actions": [],
  "progress_percentage": 0,
  "status": "active"
}
```

`product_weight_ceiling` values: `"ultralight"` | `"light"` | `"medium"` | `"rich"`

`status` values: `"active"` | `"paused_escalated"`

**Failures:**

| Code | Body | What the client did |
|------|------|---------------------|
| `400` | `{"detail": "Escalation precondition: assessment tier is RED. Recommendation engine cannot be invoked."}` | Sent `"tier": "RED"` in the body, or the user's assessment is already escalated / answers re-evaluated to RED |
| `400` | `{"detail": "Hair ID assessment must be completed before generating recommendations."}` | User has no assessment on record, or their assessment `status` is `"in_progress"` (they never called `/assessments/submit`) |
| `401` | `{"detail": "Not authenticated"}` | No or invalid `Authorization` header |
| `422` | `{"detail": [{"loc": ["body", "concern"], "msg": "Input should be 'breakage', 'dryness', ...", "type": "literal_error"}]}` | Sent `"concern": "hair_loss"` — not a valid concern value |
| `422` | `{"detail": [{"loc": ["body", "concern"], "msg": "Field required", "type": "missing"}]}` | Omitted `concern` entirely |

---

### `GET /api/recommendations/me`

**Auth:** Required

**Success `200`:** Same shape as `POST /api/recommendations/generate` success.

**Failures:**

| Code | Body | What the client did |
|------|------|---------------------|
| `401` | `{"detail": "Not authenticated"}` | No or invalid `Authorization` header |
| `404` | `{"detail": "No active routine found for this user."}` | Called this before ever calling `POST /recommendations/generate` |

---

### `PATCH /api/recommendations/me/progress`

Updates the user's self-reported routine progress. Partial updates — only send what changed.

**Auth:** Required

**Request body (full example):**
```json
{
  "current_phase": 2,
  "current_day": 14,
  "completed_actions": ["moisturize_daily", "protein_treatment_weekly"],
  "progress_percentage": 35,
  "started_at": "2026-01-15T00:00:00Z"
}
```

**Request body (partial — both are valid):**
```json
{ "progress_percentage": 50 }
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `current_phase` | `integer \| null` | No | 1–10 |
| `current_day` | `integer \| null` | No | 1–365 |
| `completed_actions` | `string[] \| null` | No | Max 100 items |
| `progress_percentage` | `integer \| null` | No | 0–100 |
| `started_at` | `ISO 8601 datetime \| null` | No | |

> **Note:** `status` cannot be set via this endpoint. Routine status transitions are system-controlled — `"paused_escalated"` is only set by the check-in escalation engine.

**Success `200`:** Same shape as `GET /api/recommendations/me`.

**Failures:**

| Code | Body | What the client did |
|------|------|---------------------|
| `401` | `{"detail": "Not authenticated"}` | No or invalid `Authorization` header |
| `404` | `{"detail": "No active routine found"}` | User has no routine — `POST /recommendations/generate` first |
| `422` | `{"detail": [{"loc": ["body", "progress_percentage"], "msg": "Input should be less than or equal to 100", "type": "less_than_equal"}]}` | Sent `"progress_percentage": 150` |
| `422` | `{"detail": [{"loc": ["body", "current_phase"], "msg": "Input should be greater than or equal to 1", "type": "greater_than_equal"}]}` | Sent `"current_phase": 0` |
| `422` | `{"detail": [{"loc": ["body", "current_day"], "msg": "Input should be less than or equal to 365", "type": "less_than_equal"}]}` | Sent `"current_day": 400` |

---

### `PATCH /api/recommendations/admin/users/{user_id}`

Admin override: customizes a specific user's routine (roadmap, notes, product weight).

**Auth:** Admin

**Path parameter:** `user_id` — UUID string of the target user

**Request body:**
```json
{
  "admin_notes": "Adjusted for sulfate sensitivity — avoid SLS-based cleansers",
  "product_weight_ceiling": "ultralight"
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `roadmap` | `Phase[] \| null` | No | Full phase array — overwrites existing roadmap |
| `admin_notes` | `string \| null` | No | Freeform clinical notes |
| `product_weight_ceiling` | `string \| null` | No | `"ultralight"` `"light"` `"medium"` `"rich"` |

Sets `is_customized = true` on the routine.

**Success `200`:** Same shape as `GET /api/recommendations/me`, with `"is_customized": true`.

**Failures:**

| Code | Body | What the client did |
|------|------|---------------------|
| `400` | `{"detail": "Invalid user UUID format."}` | Passed `user_id` as `"abc123"` instead of a valid UUID |
| `400` | `{"detail": "No valid fields provided for update."}` | Sent an empty `{}` body |
| `401` | `{"detail": "Not authenticated"}` | No or invalid `Authorization` header |
| `403` | `{"detail": "Admin access required"}` | Valid JWT but `app_metadata.role` is not `"admin"` |
| `404` | `{"detail": "User routine not found."}` | The UUID is valid but that user hasn't generated a routine yet |
| `422` | `{"detail": [{"loc": ["body", "product_weight_ceiling"], "msg": "Input should be ...", "type": "literal_error"}]}` | Sent `"product_weight_ceiling": "heavy"` — not a valid value |

---

### `GET /api/recommendations/admin/rules`

Returns all recommendation rules ordered by priority (ascending).

**Auth:** Admin

**Success `200`:** Array of rule objects:
```json
[
  {
    "problem_id": "breakage",
    "display_name": "Breakage & Retention",
    "priority": 1,
    "is_active": true,
    "protocol_id": "moisture_retention",
    "classifier": { "any_of": ["low_elasticity"] },
    "score_boosters": [],
    "hard_guards": [],
    "realistic_timeline_weeks": { "breakage": 12 },
    "root_cause_explanation_key": "low_elasticity",
    "always_runs_as_module": false
  }
]
```

**Failures:**

| Code | Body | What the client did |
|------|------|---------------------|
| `401` | `{"detail": "Not authenticated"}` | No or invalid `Authorization` header |
| `403` | `{"detail": "Admin access required"}` | Valid JWT but not admin |

---

### `PATCH /api/recommendations/admin/rules/{problem_id}`

Updates a specific recommendation rule.

**Auth:** Admin

**Path parameter:** `problem_id` — e.g. `"breakage"`

**Request body (all optional):**
```json
{
  "is_active": false,
  "priority": 3
}
```

| Field | Type |
|-------|------|
| `display_name` | `string \| null` |
| `priority` | `integer \| null` |
| `is_active` | `boolean \| null` |
| `classifier` | `object \| null` |
| `score_boosters` | `array \| null` |
| `hard_guards` | `array \| null` |
| `realistic_timeline_weeks` | `object \| null` |
| `protocol_id` | `string \| null` |

**Success `200`:** Single rule object (same shape as items in `GET /admin/rules`).

**Failures:**

| Code | Body | What the client did |
|------|------|---------------------|
| `400` | `{"detail": "No valid fields provided for update."}` | Sent empty `{}` |
| `401` | `{"detail": "Not authenticated"}` | No or invalid `Authorization` header |
| `403` | `{"detail": "Admin access required"}` | Valid JWT but not admin |
| `404` | `{"detail": "Rule not found."}` | `problem_id` like `"dandruff"` doesn't exist in the rules table |

---

### `GET /api/recommendations/admin/protocols`

Returns all treatment protocols ordered by ID.

**Auth:** Admin

**Success `200`:** Array of protocol objects:
```json
[
  {
    "id": "moisture_retention",
    "name": "Moisture Retention Protocol",
    "problem_id": "breakage",
    "phases": [
      {
        "phase": 1,
        "actions": [
          { "id": "moisturize_daily", "type": "routine", "cadence": "daily" }
        ]
      }
    ],
    "is_active": true
  }
]
```

**Failures:**

| Code | Body | What the client did |
|------|------|---------------------|
| `401` | `{"detail": "Not authenticated"}` | No or invalid `Authorization` header |
| `403` | `{"detail": "Admin access required"}` | Valid JWT but not admin |

---

### `PATCH /api/recommendations/admin/protocols/{protocol_id}`

Updates a specific protocol.

**Auth:** Admin

**Path parameter:** `protocol_id` — string ID of the protocol

**Request body (all optional):**
```json
{
  "name": "Updated Moisture Protocol",
  "is_active": false
}
```

| Field | Type |
|-------|------|
| `name` | `string \| null` |
| `problem_id` | `string \| null` |
| `phases` | `array \| null` |
| `is_active` | `boolean \| null` |

**Success `200`:** Single protocol object (same shape as items in `GET /admin/protocols`).

**Failures:**

| Code | Body | What the client did |
|------|------|---------------------|
| `400` | `{"detail": "No valid fields provided for update."}` | Sent empty `{}` |
| `401` | `{"detail": "Not authenticated"}` | No or invalid `Authorization` header |
| `403` | `{"detail": "Admin access required"}` | Valid JWT but not admin |
| `404` | `{"detail": "Protocol not found."}` | `protocol_id` like `"deep_conditioning"` doesn't exist |

---

## Followups

Follow-ups are automatically scheduled at weeks 2, 4, and 8 when a recommendation is generated. They start with `status: "scheduled"` and are dispatched (emailed) by the background job which flips them to `status: "sent"`. The frontend does not create follow-ups — it only reads them and submits check-ins.

### Followup object shape

```json
{
  "id": "f7e6d5c4-0000-0000-0000-aabbccddeeff",
  "user_id": "a1b2c3d4-0000-0000-0000-111122223333",
  "routine_id": "b2c3d4e5-0000-0000-0000-222233334444",
  "scheduled_week": 2,
  "due_date": "2026-03-01T00:00:00Z",
  "status": "sent",
  "sent_at": "2026-03-01T08:00:00Z",
  "response_rating": null,
  "response_notes": null,
  "response_symptoms": [],
  "completed_at": null,
  "action_taken": null,
  "user_email": "jane@example.com",
  "created_at": "2026-01-15T00:00:00Z",
  "updated_at": "2026-03-01T08:00:00Z"
}
```

`status` values: `"scheduled"` | `"due"` | `"sent"` | `"completed"`

`action_taken` values (populated after check-in): `"escalated"` | `"advanced_phase"` | `"maintained"` | `"completed"`

`response_rating` allowed values: `"improving"` | `"no_change"` | `"worse"` | `"severe_reaction"`

---

### `GET /api/followups/me`

Returns all follow-ups for the current user, ordered by `due_date` ascending.

**Auth:** Required

**Success `200`:** Array of followup objects (see shape above). Returns `[]` if no follow-ups exist yet (i.e. user hasn't generated a recommendation).

```json
[
  {
    "id": "f7e6d5c4-0000-0000-0000-aabbccddeeff",
    "scheduled_week": 2,
    "due_date": "2026-03-01T00:00:00Z",
    "status": "sent",
    ...
  },
  {
    "id": "a1a2a3a4-0000-0000-0000-bbbbccccdddd",
    "scheduled_week": 4,
    "due_date": "2026-03-15T00:00:00Z",
    "status": "scheduled",
    ...
  }
]
```

**Failures:**

| Code | Body | What the client did |
|------|------|---------------------|
| `401` | `{"detail": "Not authenticated"}` | No or invalid `Authorization` header |

---

### `GET /api/followups/me/next`

Returns the single earliest non-completed follow-up for the current user. Use this to show the user their next upcoming check-in.

**Auth:** Required

**Success `200`:** Single followup object (see shape above).

**Failures:**

| Code | Body | What the client did |
|------|------|---------------------|
| `401` | `{"detail": "Not authenticated"}` | No or invalid `Authorization` header |
| `404` | `{"detail": "No upcoming follow-up scheduled"}` | All follow-ups are `"completed"`, or user has no follow-ups at all |

---

### `POST /api/followups/{followup_id}/check-in`

Submits a check-in response for a scheduled follow-up. Triggers either phase advancement or clinical escalation depending on the rating.

**Auth:** Required

**Path parameter:** `followup_id` — UUID

> **Where does the frontend get this?** Call `GET /api/followups/me` or `GET /api/followups/me/next` first. Both return followup objects with an `id` field. Use that `id` as the `followup_id` in this URL.

**Request body:**
```json
{
  "response_rating": "improving",
  "response_notes": "Hair feels stronger, less breakage on wash day",
  "response_symptoms": []
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `response_rating` | `string` | Yes | Must be exactly one of: `"improving"` `"no_change"` `"worse"` `"severe_reaction"` |
| `response_notes` | `string \| null` | No | Max 2000 chars |
| `response_symptoms` | `string[]` | No | Max 50 items. Defaults to `[]` |

**Success `200` — improving/no_change (phase advanced):**
```json
{
  "followup": {
    "id": "f7e6d5c4-0000-0000-0000-aabbccddeeff",
    "status": "completed",
    "response_rating": "improving",
    "response_notes": "Hair feels stronger, less breakage on wash day",
    "response_symptoms": [],
    "completed_at": "2026-03-02T09:00:00Z",
    "action_taken": "advanced_phase",
    ...
  },
  "action_taken": "advanced_phase",
  "message": "Great progress! Your routine has been advanced to the next phase.",
  "escalated": false,
  "escalation_advisory": null,
  "current_phase": 2
}
```

**Success `200` — improving/no_change (already at max phase):**
```json
{
  "followup": { "action_taken": "maintained", ... },
  "action_taken": "maintained",
  "message": "Routine maintained at maximum phase.",
  "escalated": false,
  "escalation_advisory": null,
  "current_phase": 3
}
```

**Success `200` — worse/severe_reaction (escalated):**
```json
{
  "followup": {
    "id": "f7e6d5c4-0000-0000-0000-aabbccddeeff",
    "status": "completed",
    "response_rating": "severe_reaction",
    "response_symptoms": ["scalp_burning", "hair_loss"],
    "action_taken": "escalated",
    ...
  },
  "action_taken": "escalated",
  "message": "Your response has been flagged for clinical review. Please consult a professional.",
  "escalated": true,
  "escalation_advisory": "Adverse reaction reported. Routine has been paused. Please seek professional consultation.",
  "current_phase": null
}
```

When escalated, the user's routine `status` is also flipped to `"paused_escalated"`. A subsequent `GET /api/recommendations/me` will reflect this.

**`action_taken` logic:**

| Rating | Condition | Result |
|--------|-----------|--------|
| `"improving"` or `"no_change"` | Phase < max | `"advanced_phase"` — `current_phase` incremented |
| `"improving"` or `"no_change"` | Phase at max | `"maintained"` — phase unchanged |
| `"worse"` or `"severe_reaction"` | Any | `"escalated"` — routine paused, advisory returned |
| Any | Routine not found | `"completed"` — neutral message, no phase change |

**Failures:**

| Code | Body | What the client did |
|------|------|---------------------|
| `400` | `{"detail": "Follow-up check-in has already been completed"}` | Called check-in on a follow-up that already has `status: "completed"` |
| `401` | `{"detail": "Not authenticated"}` | No or invalid `Authorization` header |
| `404` | `{"detail": "Follow-up not found"}` | `followup_id` doesn't exist, or it belongs to a different user — both look the same intentionally (IDOR protection) |
| `422` | `{"detail": [{"loc": ["body", "response_rating"], "msg": "Invalid rating: good. Must be one of ...", "type": "value_error"}]}` | Sent `"response_rating": "good"` — not in the allowed set |
| `422` | `{"detail": [{"loc": ["body", "response_notes"], "msg": "String should have at most 2000 characters", "type": "string_too_long"}]}` | Sent `response_notes` longer than 2000 characters |
| `422` | `{"detail": [{"loc": ["body", "response_symptoms"], "msg": "List should have at most 50 items", "type": "too_long"}]}` | Sent more than 50 items in `response_symptoms` |
| `422` | `{"detail": [{"loc": ["body", "response_rating"], "msg": "Field required", "type": "missing"}]}` | Omitted `response_rating` entirely |

---

*This document is the single source of truth for the EVOLVE MVP backend API. Keep it updated when endpoints change.*
