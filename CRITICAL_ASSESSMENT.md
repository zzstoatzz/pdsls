# Critical Assessment of pdsx from an ATProto Engineer's Perspective

## Testing Scenarios & Findings

### Scenario 1: Creating a Post with an Image
**What a protocol-aware user would try:**
```bash
# Upload image first
pdsx upload-blob ./photo.jpg
# Returns: {"$type": "blob", "ref": {"$link": "bafkreif..."}, "mimeType": "image/jpeg", "size": 123456}

# Try to create post with embedded image
pdsx create app.bsky.feed.post \
  text='Check out this photo!' \
  embed='{"$type":"app.bsky.embed.images","images":[{"alt":"desc","image":{"$type":"blob","ref":{"$link":"bafkreif..."}}}]}'
```

**Problem:** ❌ **FAILS**
The `parse_key_value_args()` function in `parsing.py` only supports primitive types:
```python
RecordValue = str | int | float | bool | None
```

It cannot parse nested objects/arrays needed for embeds. The embed would be stored as a string literal, creating an invalid record.

**Impact:** Cannot create posts with images, videos, or any embedded content.

---

### Scenario 2: Creating a Post with Rich Text (Mentions/Links)
**What a protocol-aware user would try:**
```bash
pdsx create app.bsky.feed.post \
  text='Hey @alice.bsky.social check this out https://example.com' \
  facets='[{"index":{"byteStart":4,"byteEnd":23},"features":[{"$type":"app.bsky.richtext.facet#mention","did":"did:plc:..."}]}]'
```

**Problem:** ❌ **FAILS**
Same issue - `facets` is an array of objects, which `RecordValue` doesn't support. Text mentions/links won't be clickable/interactive.

**Impact:** Posts created by pdsx have no clickable links, mentions, or hashtags.

---

### Scenario 3: Creating a Quote Post
**What a protocol-aware user would try:**
```bash
pdsx create app.bsky.feed.post \
  text='Great point!' \
  embed='{"$type":"app.bsky.embed.record","record":{"uri":"at://did:plc:.../app.bsky.feed.post/abc","cid":"bafyrei..."}}'
```

**Problem:** ❌ **FAILS**
Cannot embed quoted posts due to `RecordValue` limitation.

**Impact:** Cannot create quote posts.

---

### Scenario 4: Creating a Threaded Reply
**What a protocol-aware user would try:**
```bash
pdsx create app.bsky.feed.post \
  text='Great idea!' \
  reply='{"root":{"uri":"at://...","cid":"..."},"parent":{"uri":"at://...","cid":"..."}}'
```

**Problem:** ❌ **FAILS**
`reply` field requires nested object with strong refs (URI + CID). Not supported.

**Impact:** Cannot create proper threaded conversations.

---

### Scenario 5: Creating a Post with Multiple Images
**What a protocol-aware user would try:**
```bash
pdsx create app.bsky.feed.post \
  text='Photo gallery' \
  embed='{"$type":"app.bsky.embed.images","images":[...array of 4 images...]}'
```

**Problem:** ❌ **FAILS**
Cannot pass arrays in record fields.

---

### Scenario 6: Validating Record Schema
**What a protocol-aware user would expect:**
```bash
pdsx create app.bsky.feed.post \
  text='x'  # Only 1 character - should this warn about low quality?

# Or missing required fields
pdsx create app.bsky.feed.like \
  subject='incomplete'  # Missing createdAt should error
```

**Problem:** ⚠️ **NO VALIDATION**
The tool doesn't validate records against Lexicon schemas before creation. Invalid records might be rejected by PDS or create corrupt data.

**Impact:** Users can create malformed records that violate schema constraints.

---

### Scenario 7: Reading with Reverse Pagination
**What a protocol-aware user would try:**
```bash
pdsx -r user.bsky.social ls app.bsky.feed.post --limit 10 --reverse
```

**Problem:** ❌ **NOT SUPPORTED**
Only forward pagination with `--cursor` is supported. ATProto supports reverse iteration through repos.

---

### Scenario 8: Inspecting Record with CID
**What a protocol-aware user would try:**
```bash
pdsx get at://did:plc:.../app.bsky.feed.post/abc --verify-cid bafyrei...
```

**Problem:** ❌ **NOT SUPPORTED**
No CID verification. When reading, can't verify content integrity.

---

### Scenario 9: Updating with Optimistic Locking
**What a protocol-aware user would expect:**
```bash
pdsx edit app.bsky.feed.post/abc description='updated' --expected-cid bafyrei...
```

**Problem:** ❌ **NOT SUPPORTED**
Updates don't verify the current CID before applying changes. Risk of clobbering concurrent updates.

---

### Scenario 10: Using Shorthand with GET
**What a protocol-aware user would try:**
```bash
# User is authenticated
pdsx get app.bsky.feed.post/abc123
```

**Problem:** ❌ **FAILS**
`get_record()` doesn't support shorthand URIs - only full AT-URIs work. Inconsistent with `edit` and `rm` which DO support shorthand.

```python
# From operations.py line 69-70
parts = uri.replace("at://", "").split("/")
if len(parts) != 3:
    raise ValueError(f"invalid URI format: {uri}")
```

---

### Scenario 11: Listing Collections in a Repo
**What a protocol-aware user would try:**
```bash
pdsx -r user.bsky.social collections
# Should list: app.bsky.feed.post, app.bsky.feed.like, app.bsky.actor.profile, etc.
```

**Problem:** ❌ **NOT SUPPORTED**
No way to discover what collections exist in a repo.

---

### Scenario 12: Resolving Handle to DID
**What a protocol-aware user would try:**
```bash
pdsx resolve alice.bsky.social
# Should return: did:plc:abc123...
```

**Problem:** ❌ **NOT SUPPORTED**
No handle resolution utility. Protocol-aware users often need DIDs for durable references.

---

### Scenario 13: Batch Creating Records
**What a protocol-aware user would try:**
```bash
pdsx batch-create app.bsky.feed.post < posts.jsonl
# Each line is a complete record
```

**Problem:** ❌ **NOT SUPPORTED**
No batch operations. Must run separate commands for each record.

---

### Scenario 14: Complex Field Updates
**What a protocol-aware user would try:**
```bash
# Update nested field in profile
pdsx edit app.bsky.actor.profile/self avatar='{"$type":"blob",...}'
```

**Problem:** ❌ **FAILS**
Cannot update fields with complex values.

---

## Summary of Critical Limitations

### 🚨 Show-Stoppers (Cannot do basic ATProto operations)

1. **No support for nested objects/arrays** (`RecordValue` primitive-only type)
   - Cannot create posts with images/videos
   - Cannot create posts with rich text (mentions, links, hashtags)
   - Cannot create quote posts
   - Cannot create threaded replies
   - Cannot use any embed types

2. **No Lexicon schema validation**
   - Can create invalid records
   - No type checking
   - No required field enforcement

3. **Inconsistent shorthand URI support**
   - `edit` and `rm` support shorthand
   - `get` does not support shorthand
   - Confusing UX

### ⚠️ Major Gaps (Protocol features missing)

4. **No CID handling**
   - No optimistic locking for updates
   - No content verification
   - No strong references

5. **No rich text support**
   - No facet creation helpers
   - Manual byte offset calculation required (error-prone)

6. **Limited pagination**
   - No reverse pagination
   - No timestamp-based filtering

7. **No repository introspection**
   - Can't list collections
   - Can't see repo metadata
   - Can't inspect MST structure

8. **No batch operations**
   - One record at a time only
   - Inefficient for bulk operations

9. **No handle/DID utilities**
   - No resolution helpers
   - Users must manually resolve handles

### ✅ What Works Well

1. **PDS auto-discovery** (recently added) - Great!
2. **Basic CRUD for primitive records** - Profile bio, simple records work
3. **Blob upload** - Returns proper blob reference
4. **Cursor pagination** - Forward pagination works
5. **Multiple output formats** - JSON/table/compact
6. **Unix-style UX** - Familiar command names
7. **Auth handling** - Smart about when auth is needed

---

## Recommendations

### Priority 1: Support Complex Record Values

Extend `RecordValue` and `parse_key_value_args()` to support:
```python
RecordValue = str | int | float | bool | None | dict[str, Any] | list[Any]
```

Add JSON parsing for complex fields:
```python
# Accept JSON strings for complex values
if value.startswith('{') or value.startswith('['):
    result[key] = json.loads(value)
```

Or add a `--json` mode:
```bash
pdsx create app.bsky.feed.post --json < post.json
```

### Priority 2: Add Helper Commands for Common Operations

```bash
pdsx post 'Hello world!'  # Create simple post
pdsx post 'Check this out!' --image ./photo.jpg  # Post with image
pdsx post 'Great point!' --quote at://...  # Quote post
pdsx reply at://... 'I agree!'  # Threaded reply
pdsx mention '@alice.bsky.social' # Create mention facet
```

### Priority 3: Fix Inconsistencies

- Make `get` support shorthand URIs like `edit` and `rm`
- Implement YAML output or remove from enum
- Add `--verify-cid` to update operations

### Priority 4: Add Schema Validation

Use the atproto SDK's built-in Lexicon models:
```python
from atproto import models

# Validate before creating
if collection == 'app.bsky.feed.post':
    models.AppBskyFeedPost.Record.model_validate(record)
```

### Priority 5: Add Utility Commands

```bash
pdsx resolve <handle>           # Handle → DID
pdsx collections <repo>          # List collections
pdsx inspect <uri>              # Show record + metadata
pdsx validate <collection> <json>  # Validate against schema
```

---

## Conclusion

**pdsx is a solid foundation** but currently only handles ~30% of real-world ATProto operations.

For a **"general-purpose cli for atproto record operations"**, it's critically limited by:
- Primitive-only record values
- No complex type support
- Missing essential ATProto features

**It works well for**:
- Reading public data
- Simple profile updates (bio, display name)
- Learning ATProto basics

**It fails for**:
- Creating posts with media
- Creating posts with rich text
- Social graph operations (follows, likes with proper refs)
- Any operation requiring nested data structures

**Grade: C+**
- Great UX design
- Good architecture
- Critical functionality gaps
- Would frustrate protocol-aware users who expect full CRUD on all record types
