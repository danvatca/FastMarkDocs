# Setup Instructions for GitHub and PyPI Publishing

This document provides step-by-step instructions for setting up the FastMarkDocs project on GitHub with automated PyPI publishing.

## 1. Create GitHub Repository

1. Go to [GitHub](https://github.com) and create a new repository:
   - Repository name: `fastmarkdocs`
   - Description: "A powerful library for enhancing FastAPI applications with rich markdown-based API documentation"
   - Make it **Public**
   - Don't initialize with README (we already have one)

2. Push the code to GitHub:
   ```bash
   git init
   git add .
   git commit -m "Initial commit: FastMarkDocs library"
   git branch -M main
   git remote add origin https://github.com/danvatca/fastmarkdocs.git
   git push -u origin main
   ```

## 2. Configure GitHub Repository Settings

### Branch Protection
1. Go to Settings → Branches
2. Add rule for `main` branch:
   - ✅ Require a pull request before merging
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging
   - ✅ Require conversation resolution before merging
   - ✅ Include administrators

### GitHub Pages (Optional)
1. Go to Settings → Pages
2. Source: Deploy from a branch
3. Branch: `main` / `docs` (if you want to host documentation)

## 3. Set Up PyPI Publishing

### Create PyPI Account
1. Create account at [PyPI](https://pypi.org/account/register/)
2. Enable 2FA for security
3. Create account at [TestPyPI](https://test.pypi.org/account/register/) for testing

### Configure Trusted Publishing (Recommended)
1. Go to PyPI → Account Settings → Publishing
2. Add a new pending publisher:
   - PyPI project name: `fastmarkdocs`
   - Owner: `danvatca`
   - Repository name: `fastmarkdocs`
   - Workflow name: `publish.yml`
   - Environment name: `pypi`

3. Repeat for TestPyPI with environment name: `testpypi`

### Alternative: API Tokens (if not using trusted publishing)
1. Generate API tokens:
   - PyPI: Account Settings → API tokens → Add API token
   - TestPyPI: Account Settings → API tokens → Add API token

2. Add secrets to GitHub repository:
   - Go to Settings → Secrets and variables → Actions
   - Add repository secrets:
     - `PYPI_API_TOKEN`: Your PyPI API token
     - `TEST_PYPI_API_TOKEN`: Your TestPyPI API token

## 4. Configure GitHub Environments

1. Go to Settings → Environments
2. Create environment: `pypi`
   - Add protection rules:
     - ✅ Required reviewers: `danvatca`
     - ✅ Wait timer: 0 minutes
   - Environment secrets (if using API tokens):
     - `PYPI_API_TOKEN`: Your PyPI API token

3. Create environment: `testpypi`
   - Environment secrets (if using API tokens):
     - `TEST_PYPI_API_TOKEN`: Your TestPyPI API token

## 5. Set Up Codecov (Optional)

1. Go to [Codecov](https://codecov.io/)
2. Sign in with GitHub
3. Add the repository
4. Copy the upload token
5. Add to GitHub Secrets: `CODECOV_TOKEN`

## 6. Test the Setup

### Test CI Pipeline
1. Create a small change and push to a feature branch
2. Create a pull request
3. Verify that CI runs and passes

### Test Publishing Pipeline
1. Create a release on GitHub:
   - Go to Releases → Create a new release
   - Tag version: `v0.1.0`
   - Release title: `v0.1.0 - Initial Release`
   - Description: Copy from CHANGELOG.md
   - ✅ Set as the latest release

2. Verify the publishing workflow runs
3. Check that the package appears on PyPI and TestPyPI

## 7. Post-Setup Tasks

### Update README Badges
The README already includes badges that will work once the repository is public:
- CI status badge
- Codecov badge
- PyPI version badge
- Python version support badge

### Set Up Dependabot
Dependabot is already configured and will start creating PRs for dependency updates.

### Configure Branch Protection
The CI workflow will provide status checks for branch protection rules.

## 8. Release Process

For future releases:

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Commit changes: `git commit -m "Bump version to X.Y.Z"`
4. Create and push tag: `git tag vX.Y.Z && git push origin vX.Y.Z`
5. Create GitHub release from the tag
6. The publish workflow will automatically deploy to PyPI

## 9. Troubleshooting

### Common Issues

**CI Fails on First Run:**
- Check that all dependencies are correctly specified
- Verify Python version compatibility

**Publishing Fails:**
- Ensure PyPI project name is available
- Check that trusted publishing is configured correctly
- Verify environment secrets are set

**Dependabot PRs Fail:**
- Check that auto-merge is enabled in repository settings
- Verify branch protection rules allow auto-merge

### Getting Help

- Check GitHub Actions logs for detailed error messages
- Review PyPI publishing documentation
- Contact maintainer: dan.vatca@gmail.com

## 10. Security Considerations

- ✅ Use trusted publishing instead of API tokens when possible
- ✅ Enable 2FA on PyPI and GitHub accounts
- ✅ Use environment protection rules for production deployments
- ✅ Regularly update dependencies via Dependabot
- ✅ Review security advisories in GitHub Security tab

---

**Note:** This setup provides a professional, production-ready CI/CD pipeline with automated testing, security checks, and publishing to PyPI. 