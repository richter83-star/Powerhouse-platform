# Testing Signup & Login

## Quick Test Steps

### 1. Test Signup
1. Open http://localhost:3000/signup in your browser
2. Fill in the form:
   - Email: `test@example.com`
   - Password: `TestPassword123!`
   - Full Name: `Test User`
   - Company Name: `Test Company` (optional)
   - Job Title: `Tester` (optional)
3. Click "Sign Up"
4. **Expected**: Account created and automatically logged in, redirected to dashboard

### 2. Test Manual Login
1. If you're logged in, log out first
2. Go to http://localhost:3000/login
3. Enter your credentials:
   - Email: `test@example.com`
   - Password: `TestPassword123!`
4. Click "Sign In"
5. **Expected**: Successful login, redirected to dashboard

### 3. Verify User in Database
```bash
docker-compose exec postgres psql -U postgres -d powerhouse -c "SELECT email, full_name, is_active, is_locked FROM users ORDER BY created_at DESC LIMIT 5;"
```

**Expected**: Your test user should appear in the list with `is_active = 1` and `is_locked = 0`

## Troubleshooting

### If signup fails:
- Check frontend logs: `docker-compose logs frontend -f`
- Verify DATABASE_URL is set: `docker-compose exec frontend printenv DATABASE_URL`
- Check database connection: `docker-compose ps postgres`

### If login fails:
- Verify user was created in database (see step 3 above)
- Check password hash is set: `docker-compose exec postgres psql -U postgres -d powerhouse -c "SELECT email, length(password_hash) as pwd_len FROM users WHERE email='test@example.com';"`
- Check frontend logs for authentication errors

### Common Issues:
1. **"Table User does not exist"** → Prisma schema not properly mapped. Check `@@map("users")` in schema.
2. **"Invalid credentials"** → Password hash mismatch. Verify bcrypt is hashing correctly.
3. **"Account locked"** → Check `is_locked` field in database. Should be 0 for new users.

## Success Indicators

✅ Signup creates user in `users` table  
✅ User can login immediately after signup  
✅ Manual login works with correct credentials  
✅ User appears in dashboard after login  
✅ No errors in frontend logs  
✅ Database connection is stable  

