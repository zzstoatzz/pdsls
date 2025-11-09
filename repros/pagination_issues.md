# pagination implementation issues

found during critical review on 2025-11-08

## critical bugs

### 1. cursor breaks json output
**severity**: critical
**impact**: breaks piping to jq and other json processors

```bash
# this fails with json parse error
pdsx -r jlowin.dev ls app.bsky.feed.post --limit 2 -o json | jq '.[0].text'
```

**root cause**: cursor message goes to stdout after json, breaking json structure

**fix**: cursor should go to stderr for structured output formats (json/yaml)

### 2. no --all flag for automatic pagination
**severity**: medium
**impact**: poor ux - users must manually copy/paste cursors

**current workflow** (tedious):
```bash
pdsx ls collection --limit 50
# copy cursor from output
pdsx ls collection --limit 50 --cursor <paste>
# repeat...
```

**desired workflow**:
```bash
pdsx ls collection --all  # fetches all pages automatically
```

## usability issues

### 3. cursor display is not copy-friendly
the cursor just prints at bottom:
```
next page cursor: 3lyqmkpiprs2w
```

**improvements**:
- make it more prominent
- maybe suggest the next command?
- or provide a copyable format

### 4. no progress indication
users don't know:
- how many total pages
- how many records total
- their progress through pagination

**suggestion**: add metadata like:
```
records: 50 (page 1, more available)
next: pdsx ls collection --limit 50 --cursor <cursor>
```

### 5. compact output still ugly
the compact format shows pydantic's `py_type` everywhere:
```json
{"py_type":"app.bsky.feed.post","reply":{"py_type":"app.bsky.feed.post#replyRef"}}
```

**fix**: strip py_type fields before display

## missing features

### 6. no --reverse flag
the api supports `reverse` param but we don't expose it

### 7. cursor in json output mode
when using `-o json`, maybe include cursor in the output structure?

```json
{
  "records": [...],
  "cursor": "abc123",
  "has_more": true
}
```

but this breaks backward compat with current json array format...

### 8. no validation of cursor format
if user passes invalid cursor, what happens? should validate or show better error

## documentation needs
- need concept docs for pagination
- need examples of multi-page workflows
- need to explain cursor format (opaque)
