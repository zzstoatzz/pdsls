# pdsls examples

## read anyone's bio
```bash
uvx pdsls --repo did:plc:o53crari67ge7bvbv273lxln list app.bsky.actor.profile -o json | jq -r '.[0].description'
```

## update your bio
```bash
export ATPROTO_HANDLE=your.handle ATPROTO_PASSWORD=your-password
uvx pdsls edit app.bsky.actor.profile/self description='new bio'
```

## read anyone's posts
```bash
uvx pdsls -r did:plc:o53crari67ge7bvbv273lxln list app.bsky.feed.post --limit 5 -o json | jq -r '.[] | .text'
```

**atproto gives you full read access to anyone's public data. auth only required for writes.**
