# Quick Remote Repository Setup

## Step 1: Create Remote Repository

### GitHub (Recommended)

1. **Go to**: https://github.com/new
2. **Repository name**: `powerhouse-platform` (or your choice)
3. **Description**: "Enterprise-grade multi-agent AI platform"
4. **Visibility**: 
   - ✅ **Private** (recommended for production code)
   - ⚠️ Public (if you want it open source)
5. **IMPORTANT**: 
   - ❌ DO NOT check "Add a README file"
   - ❌ DO NOT check "Add .gitignore"
   - ❌ DO NOT check "Choose a license"
   - (We already have these files)
6. **Click**: "Create repository"

### GitLab Alternative

1. **Go to**: https://gitlab.com/projects/new
2. **Project name**: `powerhouse-platform`
3. **Visibility**: Private
4. **DO NOT** initialize with README
5. **Click**: "Create project"

## Step 2: Connect Local Repository

Open terminal in your project root and run:

```bash
# Add remote (replace YOUR_USERNAME with your GitHub/GitLab username)
git remote add origin https://github.com/YOUR_USERNAME/powerhouse-platform.git

# Rename branch to main (if needed)
git branch -M main

# Push to remote
git push -u origin main
```

## Step 3: Authentication

When prompted for credentials:

**Username**: Your GitHub/GitLab username

**Password**: Use a **Personal Access Token** (not your account password)

### Create Personal Access Token

**GitHub:**
1. Go to: Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Name: "Powerhouse Platform"
4. Select scope: `repo` (full control of private repositories)
5. Click "Generate token"
6. **Copy the token immediately** (you won't see it again)
7. Use this token as your password

**GitLab:**
1. Go to: Preferences → Access Tokens
2. Name: "Powerhouse Platform"
3. Scopes: Check `write_repository`
4. Click "Create personal access token"
5. Copy and use as password

## Step 4: Verify

Check that everything worked:

```bash
# Check remote is set
git remote -v

# Should show:
# origin  https://github.com/YOUR_USERNAME/powerhouse-platform.git (fetch)
# origin  https://github.com/YOUR_USERNAME/powerhouse-platform.git (push)
```

Visit your repository URL to see your code online!

## Future Updates

After making changes:

```bash
git add .
git commit -m "Your descriptive commit message"
git push
```

## Troubleshooting

### "Remote origin already exists"
```bash
git remote remove origin
git remote add origin YOUR_NEW_URL
```

### "Authentication failed"
- Make sure you're using a Personal Access Token, not your password
- Check token hasn't expired
- Verify token has `repo` scope (GitHub) or `write_repository` (GitLab)

### "Large file" errors
- GitHub has 100MB file size limit
- GitLab has 10MB file size limit
- Use Git LFS for large files if needed

## Next Steps

- Set up branch protection rules (Settings → Branches)
- Add collaborators (Settings → Collaborators)
- Configure CI/CD (see `.github/workflows/`)
- Set up webhooks for deployments

