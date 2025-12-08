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

---

## Step 2: Copy Your Repository URL

After creating the repository, you'll see a page with setup instructions. Copy the **HTTPS** URL:

**Example URLs:**
- GitHub: `https://github.com/richter83-star/powerhouse-platform.git`
- GitLab: `https://gitlab.com/richter83-star/powerhouse-platform.git`

---

## Step 3: Run These Commands

Once you have your repository URL, run these commands in PowerShell:

```powershell
# 1. Rename branch to 'main' (GitHub standard)
git branch -M main

# 2. Add remote (REPLACE WITH YOUR ACTUAL URL)
git remote add origin https://github.com/YOUR_USERNAME/powerhouse-platform.git

# 3. Verify remote was added
git remote -v

# 4. Push to remote
git push -u origin main
```

---

## Step 4: Authentication

### If using HTTPS:

**GitHub** will prompt for:
- **Username**: Your GitHub username
- **Password**: Use a **Personal Access Token** (NOT your GitHub password)

**To create a Personal Access Token:**
1. Go to: https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Name: "Powerhouse Platform"
4. Expiration: 90 days (or your preference)
5. Scopes: Check `repo` (full control of private repositories)
6. Click "Generate token"
7. **COPY THE TOKEN** (you won't see it again!)
8. Use this token as your password when pushing

### If using SSH (Recommended for future):

```powershell
# Check if you have SSH key
ls ~/.ssh

# If no SSH key, generate one:
ssh-keygen -t ed25519 -C "richter83@gmail.com"

# Copy public key to clipboard
cat ~/.ssh/id_ed25519.pub | clip

# Add to GitHub: https://github.com/settings/keys
# Click "New SSH key", paste, save
```

---

## Step 5: Verify Success

After pushing, you should see:
```
Enumerating objects: 452, done.
Counting objects: 100% (452/452), done.
...
To https://github.com/YOUR_USERNAME/powerhouse-platform.git
 * [new branch]      main -> main
Branch 'main' set up to track remote branch 'main' from 'origin'.
```

**Check your repository online** - you should see all 452 files!

---

## Troubleshooting

### "remote origin already exists"
```powershell
git remote remove origin
git remote add origin YOUR_URL
```

### "Authentication failed"
- Use Personal Access Token instead of password
- Or set up SSH keys

### "Permission denied"
- Check repository visibility (Private vs Public)
- Verify you have write access to the repository

---

## Next Steps After Setup

Once connected:
```powershell
# Check status
git status

# See remote info
git remote -v

# Pull latest (if working from multiple machines)
git pull origin main
```

---

**Ready? Create your repository and then run the commands above!** 🚀

