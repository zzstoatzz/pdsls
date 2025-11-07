# pdsx

general-purpose cli for atproto record operations

## installation

```bash
uv add pdsx
# or
uvx pdsx --help
```

## quick start

```bash
# read anyone's posts (no auth)
uvx pdsx -r did:plc:o53crari67ge7bvbv273lxln ls app.bsky.feed.post -o json | jq -r '.[].text'

# update your bio (with auth)
export ATPROTO_HANDLE=your.handle ATPROTO_PASSWORD=your-password
uvx pdsx edit app.bsky.actor.profile/self description='new bio'
```

## features

- crud operations for atproto records (list, get, create, update, delete)
- optional auth: reads with `--repo` flag don't require authentication
- shorthand URIs: use `app.bsky.feed.post/abc123` when authenticated
- multiple output formats: compact (default), json, yaml, table
- unix-style aliases: `ls`, `cat`, `rm`, `edit`, `touch`/`add`
- jq-friendly json output
- python 3.10+, type-safe

<details>
<summary>usage examples</summary>

### read operations (no auth with --repo)

```bash
# list records from any repo
pdsx -r did:plc:... ls app.bsky.feed.post --limit 5 -o json

# read someone's bio
pdsx -r did:plc:o53crari67ge7bvbv273lxln ls app.bsky.actor.profile -o json | jq -r '.[0].description'
```

### write operations (auth required)

```bash
# update using shorthand URI
pdsx edit app.bsky.actor.profile/self description='new bio'

# delete using shorthand URI
pdsx rm app.bsky.feed.post/abc123

# create a record
pdsx create app.bsky.feed.like subject='at://...' createdAt='2024-01-01T00:00:00Z'
```

**note**: when authenticated, use shorthand URIs (`collection/rkey`) instead of full AT-URIs (`at://did:plc:.../collection/rkey`)

</details>

<details>
<summary>output formats</summary>

### compact (default)
```
app.bsky.feed.post (3 records)
3m4ryxwq5dt2i: {"created_at":"2025-11-04T07:25:17.061883+00:00","text":"..."}
```

### json
```bash
pdsx ls app.bsky.feed.post -o json | jq '.[].text'
```

### table
```bash
pdsx ls app.bsky.feed.post -o table
```

</details>

<details>
<summary>development</summary>

```bash
git clone https://github.com/zzstoatzz/pdsx
cd pdsx
uv sync
uv run pytest
uv run ty check
```

</details>

## license

mit
