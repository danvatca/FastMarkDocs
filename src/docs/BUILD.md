# Documentation Build Guide

This guide explains how to build and test the FastMarkDocs documentation locally using Jekyll before pushing changes to GitHub.

## Quick Start

### Option 1: Using the Build Script (Recommended)

```bash
# First time setup
./build-docs.sh setup

# Build and serve locally
./build-docs.sh serve
```

### Option 2: Using Make

```bash
# First time setup
make docs-setup

# Build and serve locally
make docs-serve
```

### Option 3: Using PowerShell (Windows)

```powershell
# First time setup
.\build-docs.ps1 setup

# Build and serve locally
.\build-docs.ps1 serve
```

## Prerequisites

### Required Software

1. **Ruby** (version 2.7 or higher)
   - **macOS**: `brew install ruby`
   - **Ubuntu/Debian**: `sudo apt-get install ruby-full`
   - **Windows**: Download from [RubyInstaller](https://rubyinstaller.org/)

2. **Bundler** (Ruby gem manager)
   - Automatically installed by the build scripts
   - Manual install: `gem install bundler`

### Verification

Check that you have the required tools:

```bash
ruby --version    # Should be 2.7+
bundle --version  # Should be 2.0+
```

## Build Scripts Overview

### Bash Script (`build-docs.sh`)

The main build script for Unix-like systems (macOS, Linux):

```bash
./build-docs.sh [COMMAND]
```

**Available Commands:**
- `setup` - Install dependencies and setup environment
- `build` - Build the documentation only
- `serve` - Build and serve documentation locally (default)
- `validate` - Validate the built documentation
- `clean` - Clean build artifacts
- `help` - Show help message

**Environment Variables:**
- `DOCS_PORT` - Port for local server (default: 4000)
- `DOCS_HOST` - Host for local server (default: 127.0.0.1)

**Examples:**
```bash
# First time setup
./build-docs.sh setup

# Build and serve on default port (4000)
./build-docs.sh serve

# Serve on custom port
DOCS_PORT=3000 ./build-docs.sh serve

# Build only (no server)
./build-docs.sh build

# Clean build artifacts
./build-docs.sh clean
```

### PowerShell Script (`build-docs.ps1`)

The build script for Windows systems:

```powershell
.\build-docs.ps1 [COMMAND] [-Port PORT] [-Host HOST]
```

**Examples:**
```powershell
# First time setup
.\build-docs.ps1 setup

# Build and serve on default port
.\build-docs.ps1 serve

# Serve on custom port
.\build-docs.ps1 serve -Port 3000

# Build only
.\build-docs.ps1 build
```

### Makefile (`Makefile.docs`)

Convenient Make targets for common tasks:

```bash
# Show available commands
make docs-help

# Setup environment
make docs-setup

# Build and serve
make docs-serve

# Serve on custom port
make docs-serve DOCS_PORT=3000

# Clean build
make docs-clean

# Full rebuild
make docs-rebuild

# Production build
make docs-production

# Show statistics
make docs-stats
```

## Manual Jekyll Commands

If you prefer to run Jekyll commands directly:

### Setup

```bash
cd docs
bundle install
```

### Build

```bash
cd docs
bundle exec jekyll build
```

### Serve Locally

```bash
cd docs
bundle exec jekyll serve --livereload --incremental
```

### Production Build

```bash
cd docs
JEKYLL_ENV=production bundle exec jekyll build
```

## Directory Structure

```
fastapi-markdown-docs/
├── docs/                    # Documentation source
│   ├── _config.yml         # Jekyll configuration
│   ├── Gemfile             # Ruby dependencies
│   ├── index.md            # Homepage
│   ├── getting-started.md  # Getting started guide
│   ├── user-guide.md       # User guide
│   ├── api-reference.md    # API reference
│   ├── examples.md         # Examples
│   ├── advanced.md         # Advanced guide
│   └── _site/              # Generated site (after build)
├── build-docs.sh           # Build script (Unix)
├── build-docs.ps1          # Build script (Windows)
└── Makefile.docs           # Make targets
```

## Local Development Workflow

### 1. Initial Setup

```bash
# Clone the repository
git clone https://github.com/danvatca/fastmarkdocs.git
cd fastmarkdocs

# Setup documentation environment
./build-docs.sh setup
```

### 2. Make Changes

Edit the markdown files in the `docs/` directory:
- `docs/user-guide.md` - User guide
- `docs/api-reference.md` - API reference
- `docs/examples.md` - Examples
- `docs/advanced.md` - Advanced topics

### 3. Test Locally

```bash
# Start local server with live reload
./build-docs.sh serve
```

Visit `http://localhost:4000` to see your changes. The server will automatically reload when you save files.

### 4. Validate Build

```bash
# Validate the build
./build-docs.sh validate

# Or check with Make
make docs-lint
```

### 5. Production Test

```bash
# Test production build
make docs-production
```

### 6. Commit and Push

```bash
git add docs/
git commit -m "Update documentation"
git push origin main
```

## Troubleshooting

### Common Issues

#### Ruby Version Issues

**Problem**: Jekyll requires Ruby 2.7+

**Solution**:
```bash
# Check Ruby version
ruby --version

# Update Ruby (macOS with Homebrew)
brew upgrade ruby

# Update Ruby (Ubuntu)
sudo apt-get update && sudo apt-get upgrade ruby-full
```

#### Bundle Install Fails

**Problem**: Gem installation fails

**Solution**:
```bash
# Clear gem cache
gem cleanup

# Update bundler
gem update bundler

# Reinstall dependencies
cd docs
rm Gemfile.lock
bundle install
```

#### Port Already in Use

**Problem**: Port 4000 is already in use

**Solution**:
```bash
# Use a different port
DOCS_PORT=3000 ./build-docs.sh serve

# Or with Make
make docs-serve DOCS_PORT=3000

# Or with PowerShell
.\build-docs.ps1 serve -Port 3000
```

#### Permission Errors

**Problem**: Permission denied when installing gems

**Solution**:
```bash
# Use user-local gem installation
bundle config set --local path 'vendor/bundle'
bundle install
```

#### Build Fails

**Problem**: Jekyll build fails with errors

**Solution**:
```bash
# Check for syntax errors
make docs-lint

# Clean and rebuild
./build-docs.sh clean
./build-docs.sh build

# Check Jekyll doctor
cd docs
bundle exec jekyll doctor
```

### Getting Help

1. **Check Jekyll logs**: Look for error messages in the build output
2. **Validate markdown**: Ensure your markdown syntax is correct
3. **Check file paths**: Verify all links and image paths are correct
4. **Test incrementally**: Build after small changes to isolate issues

## GitHub Pages Deployment

The documentation is automatically deployed to GitHub Pages when changes are pushed to the `main` branch.

### GitHub Pages Configuration

The site is configured to deploy from the `docs/` directory on the `main` branch:

1. Repository Settings → Pages
2. Source: Deploy from a branch
3. Branch: `main`
4. Folder: `/docs`

### Custom Domain (Optional)

To use a custom domain:

1. Add a `CNAME` file to the `docs/` directory
2. Update the `url` and `baseurl` in `docs/_config.yml`
3. Configure DNS settings with your domain provider

## Performance Tips

### Faster Builds

1. **Use incremental builds**: `--incremental` flag (enabled by default in scripts)
2. **Enable caching**: Jekyll automatically caches builds
3. **Limit file watching**: Use specific file patterns if needed

### Optimized Serving

1. **Use live reload**: `--livereload` flag (enabled by default)
2. **Serve on local network**: Use `--host 0.0.0.0` to access from other devices
3. **Custom port**: Use different port if 4000 is busy

## Advanced Configuration

### Custom Jekyll Configuration

Edit `docs/_config.yml` to customize:

```yaml
# Site settings
title: Your Site Title
description: Your site description
url: "https://yourusername.github.io"
baseurl: "/your-repo-name"

# Build settings
markdown: kramdown
highlighter: rouge
theme: minima

# Plugins
plugins:
  - jekyll-feed
  - jekyll-sitemap
  - jekyll-seo-tag
```

### Custom Themes

To use a different theme:

1. Update `docs/Gemfile`:
   ```ruby
   gem "your-theme-name"
   ```

2. Update `docs/_config.yml`:
   ```yaml
   theme: your-theme-name
   ```

3. Run setup again:
   ```bash
   ./build-docs.sh setup
   ```

### Custom Plugins

Add plugins to `docs/Gemfile`:

```ruby
group :jekyll_plugins do
  gem "jekyll-feed"
  gem "jekyll-sitemap"
  gem "jekyll-seo-tag"
  gem "your-custom-plugin"
end
```

## Continuous Integration

### GitHub Actions

The repository includes a GitHub Actions workflow that automatically builds and deploys the documentation. See `.github/workflows/` for configuration.

### Local CI Testing

Test the build process locally before pushing:

```bash
# Run full build and validation
./build-docs.sh build
./build-docs.sh validate

# Test production build
make docs-production

# Check for issues
make docs-lint
```

---

This build system ensures that your documentation changes are properly tested locally before being deployed to GitHub Pages, maintaining high quality and preventing broken deployments. 