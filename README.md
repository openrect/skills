# Codex Skills

Installable Codex skills from this repository.

## Available Skills

- `check-rate-limit-reset-credits`: Safely checks local Codex/ChatGPT rate-limit reset credits from `~/.codex/auth.json` without exposing tokens, cookies, raw responses, or full unique IDs.

## Install From GitHub

After this repository is pushed to GitHub, give Codex the GitHub URL for the skill folder, not just the repository root:

```text
https://github.com/<owner>/<repo>/tree/main/check-rate-limit-reset-credits
```

Prompt example:

```text
Use $skill-installer to install https://github.com/<owner>/<repo>/tree/main/check-rate-limit-reset-credits
```

Then restart Codex so the new skill is loaded.

You can also install by repo and path:

```text
Use $skill-installer to install check-rate-limit-reset-credits from <owner>/<repo> path check-rate-limit-reset-credits
```
