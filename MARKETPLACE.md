# Publishing DevFlow to the VS Code Marketplace

A clean, step-by-step guide. Takes about 20 minutes end-to-end if it's your first time.

## 1. One-time setup

### 1.1 Install `vsce`

```bash
npm install -g @vscode/vsce
```

### 1.2 Create a Publisher

Go to <https://marketplace.visualstudio.com/manage> and sign in with the Microsoft account you want to publish under. Click **Create publisher**. Pick a unique `publisherId` — this is what goes in `package.json → "publisher"`.

Update `package.json`:

```json
"publisher": "<your-publisher-id>"
```

### 1.3 Create an Azure DevOps Personal Access Token

Publishing requires a PAT, **not** a Marketplace key.

1. Go to <https://dev.azure.com/> → sign in with the same account.
2. User icon → **Personal access tokens** → **New Token**.
3. Settings:
   - **Organization**: *All accessible organizations*
   - **Expiration**: 1 year (you'll rotate it)
   - **Scopes**: switch to **Custom defined** → **Marketplace** → check **Manage**.
4. Copy the token. You'll only see it once.

### 1.4 Log vsce into your publisher

```bash
vsce login <your-publisher-id>
# paste the PAT when prompted
```

## 2. Pre-publish checklist

Before every publish, verify:

- [ ] `package.json` — `version` bumped (semver). `vsce` won't publish the same version twice.
- [ ] `package.json` — `repository.url` points at the real repo.
- [ ] `README.md` — renders cleanly on GitHub (Marketplace reuses it).
- [ ] `CHANGELOG.md` — one new entry describing what changed.
- [ ] `icon.png` — 128×128 or larger, square, present at the path in `package.json`.
- [ ] `.vscodeignore` — excludes `.venv/`, `node_modules/`, `backend/__pycache__/`, `webview/node_modules/`, test files, raw sources you don't ship.
- [ ] `npm run compile` succeeds from a clean clone.
- [ ] `npm test` and `npm run test:py` are green.

## 3. Package locally and smoke-test

```bash
npm run compile
npm run package
# produces devflow-toolkit-<version>.vsix
```

Install the `.vsix` in a fresh VS Code window:

```bash
code --install-extension devflow-toolkit-<version>.vsix
```

Reload. Open the DevFlow panel. Confirm:

- Sidebar icon shows the new DevFlow mark.
- Panel renders without "Webview Not Built".
- `Cmd/Ctrl+Shift+P` → `DevFlow: Open Panel` works.
- Backend starts (check the output channel if it doesn't).

## 4. Publish

```bash
npm run publish
```

Or for a specific version bump:

```bash
vsce publish patch   # 1.0.0 -> 1.0.1
vsce publish minor   # 1.0.0 -> 1.1.0
vsce publish major   # 1.0.0 -> 2.0.0
```

The listing appears at `https://marketplace.visualstudio.com/items?itemName=<publisher>.devflow-toolkit` within a few minutes.

## 5. After publishing

- Tag the release in git: `git tag v1.0.0 && git push --tags`.
- Add the Marketplace badge to the README:
  ```
  [![Version](https://img.shields.io/visual-studio-marketplace/v/<publisher>.devflow-toolkit)](https://marketplace.visualstudio.com/items?itemName=<publisher>.devflow-toolkit)
  ```

## Common gotchas

| Symptom | Fix |
|---------|-----|
| `ERROR: Make sure to edit the README.md` | Remove the generated Yo Code template text |
| `ERROR: Missing publisher name` | Run `vsce login <publisherId>` again |
| Published, but icon not shown | Icon path in `package.json` must be relative and the file must not be in `.vscodeignore` |
| `.vsix` is >50 MB | You're bundling `node_modules` or `.venv` — add them to `.vscodeignore` |
| Backend fails on user machines | Ship a `requirements.txt` and document the first-run `pip install` in the README, or vendor a bootstrap step in `BackendManager` |

## Unpublishing / rolling back

```bash
vsce unpublish <publisher>.devflow-toolkit
```

Use this sparingly — unpublishing breaks installs for every existing user. Prefer shipping a fixed patch version.
