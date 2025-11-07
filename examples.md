# pdsls examples

all tested and working.

## read anyone's bio (no auth required)
```bash
uvx pdsls list app.bsky.actor.profile --repo did:plc:o53crari67ge7bvbv273lxln -o json | jq -r '.[0].description'
```
output:
```
(maybe) interesting stuff i (@zzstoatzz.io) do - narrated by claude!
```

## update your own bio (requires auth)
```bash
# set credentials
export ATPROTO_HANDLE=your.handle
export ATPROTO_PASSWORD=your-password

# update bio
uvx pdsls edit at://your-did/app.bsky.actor.profile/self description='new bio'
```

## read anyone's posts (no auth required)
```bash
uvx pdsls list app.bsky.feed.post --repo did:plc:o53crari67ge7bvbv273lxln --limit 5 -o json | jq -r '.[] | .text'
```
output:
```
just shipped pdsls v0.0.1a2 - a general-purpose cli for atproto record operations 🚀
```

---

**key insight**: atproto gives you full read access to anyone's public data - no api keys needed. auth only required for writes.
