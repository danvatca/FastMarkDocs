# FastMarkDocs Documentation

This directory contains the complete documentation for FastMarkDocs, hosted on GitHub Pages.

## Documentation Structure

- **[index.md](index.md)** - Homepage and project overview
- **[getting-started.md](getting-started.md)** - Installation and basic setup guide
- **[user-guide.md](user-guide.md)** - Comprehensive usage guide
- **[api-reference.md](api-reference.md)** - Complete API documentation
- **[examples.md](examples.md)** - Real-world examples and tutorials
- **[advanced.md](advanced.md)** - Advanced features and configuration
- **[_config.yml](_config.yml)** - Jekyll configuration for GitHub Pages

## Local Development

To run the documentation locally:

### Prerequisites

- Ruby 2.7 or higher
- Bundler gem

### Setup

1. Install dependencies:
   ```bash
   cd docs
   bundle install
   ```

2. Run the local server:
   ```bash
   bundle exec jekyll serve
   ```

3. Open http://localhost:4000 in your browser

### Making Changes

1. Edit the markdown files directly
2. The site will automatically rebuild when you save changes
3. Refresh your browser to see updates

## Contributing to Documentation

### Adding New Pages

1. Create a new `.md` file in the docs directory
2. Add the Jekyll front matter:
   ```yaml
   ---
   layout: default
   title: Your Page Title
   description: Brief description for SEO
   ---
   ```
3. Add the page to the navigation in `_config.yml`

### Writing Guidelines

- Use clear, concise language
- Include code examples for all features
- Test all code examples before publishing
- Use consistent formatting and structure
- Add appropriate headings for navigation

### Code Examples

- Always include working code examples
- Use realistic data in examples
- Show both basic and advanced usage
- Include error handling where appropriate
- Test examples with the latest version of FastMarkDocs

## Deployment

The documentation is automatically deployed to GitHub Pages when changes are pushed to the main branch. The site is available at: https://danvatca.github.io/fastmarkdocs

## Feedback

If you find issues with the documentation or have suggestions for improvement:

1. [Open an issue](https://github.com/danvatca/fastmarkdocs/issues) on GitHub
2. Submit a pull request with improvements
3. Contact the maintainers at dan.vatca@gmail.com 