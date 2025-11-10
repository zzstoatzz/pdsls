# pdsx

general-purpose cli for atproto record operations

📚 **[documentation](https://pdsx.zzstoatzz.io)**

## installation

```bash
uv add pdsx
# or
uvx pdsx --help
```

## quick start

**important**: flags like `-r`, `--handle`, `--password` go BEFORE the command (`ls`, `get`, etc.)

```bash
# read anyone's posts (no auth needed)
uvx pdsx -r zzstoatzz.io ls app.bsky.feed.post -o json | jq -r '.[].text'

# update your bio (requires auth)
export ATPROTO_HANDLE=your.handle ATPROTO_PASSWORD=your-app-password
uvx pdsx edit app.bsky.actor.profile/self description='new bio'
```

## features

- crud operations for atproto records (list, get, create, update, delete)
- **blob upload**: upload images, videos, and other binary content
- **cursor pagination**: paginate through large collections
- optional auth: reads with `--repo` flag don't require authentication
- shorthand URIs: use `app.bsky.feed.post/abc123` when authenticated
- multiple output formats: compact (default), json, yaml, table
- unix-style aliases: `ls`, `cat`, `rm`, `edit`, `touch`/`add`
- jq-friendly json output
- python 3.10+, type-safe

<details>
<summary>usage examples</summary>

### read operations (no auth with -r)

```bash
# list records from any repo (note: -r goes BEFORE ls)
pdsx -r zzstoatzz.io ls app.bsky.feed.post --limit 5 -o json

# read someone's bio
pdsx -r zzstoatzz.io ls app.bsky.actor.profile -o json | jq -r '.[0].description'
```

### pagination

```bash
# get first page (note: -r before ls, --cursor after)
pdsx -r zzstoatzz.io ls app.bsky.feed.post --limit 10

# output includes cursor if more pages exist:
# next page cursor: 3lyqmkpiprs2w

# get next page
pdsx -r zzstoatzz.io ls app.bsky.feed.post --limit 10 --cursor 3lyqmkpiprs2w
```

### blob upload (auth required)

```bash
# upload an image
pdsx upload-blob ./photo.jpg

# returns blob reference like:
# {
#   "$type": "blob",
#   "ref": {"$link": "bafkreif..."},
#   "mimeType": "image/jpeg",
#   "size": 123456
# }

# use blob reference in records (e.g., create post with image)
# copy the blob reference output and use it in your record creation
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

both `ls` and `cat`/`get` support four output formats:

### compact (default for ls)
```
app.bsky.feed.post (3 records)
3m4ryxwq5dt2i: {"created_at":"2025-11-04T07:25:17.061883+00:00","text":"..."}
```

### json
```bash
pdsx ls app.bsky.feed.post -o json | jq '.[].text'
pdsx cat app.bsky.feed.post/3m4ryxwq5dt2i -o json
```

### yaml
```bash
pdsx ls app.bsky.feed.post -o yaml
pdsx cat app.bsky.actor.profile/self -o yaml
```

### table (default for cat/get)
```bash
pdsx ls app.bsky.feed.post -o table
pdsx cat app.bsky.actor.profile/self  # default
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
