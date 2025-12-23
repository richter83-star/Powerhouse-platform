# How to Check CI/CD Status

## View Failed Checks on GitHub

1. Go to your repository: https://github.com/richter83-star/Powerhouse-platform
2. Click on the commit with the red X
3. Click the red X icon to see which checks failed
4. Click on individual failed jobs to see error logs

## Common Issues & Fixes

### Backend CI Failures
- **Tests failing**: Run `pytest tests/ -v` locally
- **Linting errors**: Run `flake8 .` to see issues
- **Dependencies**: Check `requirements.txt` is up to date

### Frontend CI Failures  
- **Type errors**: Run `npx tsc --noEmit` locally
- **Build errors**: Run `npm run build` locally
- **Dependencies**: Check `package.json` and `package-lock.json`

### Security Scan Failures
- **CodeQL issues**: Check Security tab in GitHub
- **Vulnerabilities**: Update dependencies
- **Dependency review**: Check PR for dependency warnings

### Deployment Failures
- **Docker build**: Check Dockerfiles exist and are correct
- **Kubernetes**: Verify `k8s/` directory exists with manifests
- **Secrets**: Ensure GitHub secrets are configured (KUBECONFIG, etc.)

## Fix Workflow Issues

Some workflows may need:
- Missing `k8s/` directory for Kubernetes deployments
- Missing Dockerfiles
- Environment variables/secrets not configured
- Test database setup issues

## View Full Logs

1. Go to **Actions** tab in GitHub
2. Click on the failed workflow run
3. Click on the failed job
4. Expand failed steps to see detailed error messages

