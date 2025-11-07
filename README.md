# pdsls

general-purpose cli for atproto record operations

## installation

```bash
uv add pdsls
# or
uvx pdsls --help
```

## quick start

set your credentials:

```bash
export ATPROTO_HANDLE=your.handle
export ATPROTO_PASSWORD=your-password
```

list posts (compact format by default):

```bash
pdsls ls app.bsky.feed.post --limit 10
```

json output for jq:

```bash
pdsls ls app.bsky.feed.post -o json | jq '.[].text'
```

table view:

```bash
pdsls ls app.bsky.feed.post -o table
```

## features

- crud operations for atproto records (list, get, create, update, delete)
- multiple output formats: compact (default), json, yaml, table
- unix-style command aliases: `ls`, `cat`, `rm`, `edit`, `touch`/`add`
- clean json output for jq/pipe interoperability
- tty-aware formatting
- type-safe with strict typing
- python 3.10+ support

## usage

### list records

```bash
# using full command
pdsls list app.bsky.feed.post --limit 5

# using alias
pdsls ls app.bsky.feed.post --limit 5 -o json
```

### get a record

```bash
# using full command
pdsls get at://did:plc:example/app.bsky.feed.post/123

# using alias
pdsls cat at://did:plc:example/app.bsky.feed.post/123
```

### create a record

```bash
pdsls create app.bsky.feed.like subject='at://...' createdAt='2024-01-01T00:00:00Z'

# using alias
pdsls touch app.bsky.feed.like subject='at://...' createdAt='2024-01-01T00:00:00Z'
```

### update a record

```bash
pdsls update at://did:plc:example/app.bsky.feed.post/123 text='updated text'

# using alias
pdsls edit at://did:plc:example/app.bsky.feed.post/123 text='updated text'
```

### delete a record

```bash
pdsls delete at://did:plc:example/app.bsky.feed.post/123

# using alias
pdsls rm at://did:plc:example/app.bsky.feed.post/123
```

## output formats

### compact (default)

one line per record with json:

```
app.bsky.feed.post (3 records)
3m4ryxwq5dt2i: {"created_at":"2025-11-04T07:25:17.061883+00:00","text":"..."}
3m4ryxvw4l32z: {"created_at":"2025-11-04T07:25:16.201083+00:00","text":"..."}
```

### json

clean json for piping to jq:

```bash
pdsls ls app.bsky.feed.post -o json | jq '.[].text'
```

### table

pretty table for terminal viewing:

```bash
pdsls ls app.bsky.feed.post -o table
```

## development

```bash
# clone repo
git clone https://github.com/zzstoatzz/pdsls
cd pdsls

# install with dev dependencies
uv sync

# run tests
uv run pytest

# run type checker
uv run ty check

# run pre-commit hooks
uv run pre-commit run --all-files
```

## license

mit
