# Migration Guide: Tags → Sections

This guide helps you migrate from the old `Tags:` approach to the new `Section:` approach in FastMarkDocs v0.5.0.

## Overview

FastMarkDocs v0.5.0 introduces a cleaner, more semantic approach to organizing API documentation using **Sections** instead of **Tags**. This change provides better separation of concerns between FastAPI operational tags and documentation organization.

## What Changed

### Before (v1.x) - Tags Approach
```markdown
## GET /users
Get all users in the system.

### Description
Returns a list of users with pagination support.

Tags: users, admin
```

### After (v2.0+) - Section Approach
```markdown
## GET /users
Get all users in the system.

### Description
Returns a list of users with pagination support.

Section: User Management
```

## Key Differences

| Aspect | Old (Tags) | New (Sections) |
|--------|------------|----------------|
| **Keyword** | `Tags: tag1, tag2` | `Section: Section Name` |
| **Multiple Values** | ✅ Multiple tags supported | ❌ Single section per endpoint |
| **Naming** | `lowercase-tags` | `Title Case Sections` |
| **Purpose** | Mixed operational/documentation | Pure documentation organization |
| **FastAPI Integration** | Conflated with router tags | Separate from router tags |

## Migration Steps

### 1. Update Markdown Files

**Find and Replace:**
- `Tags:` → `Section:`
- Multiple tags → Single descriptive section name

**Example transformations:**
```diff
- Tags: users, list, admin
+ Section: User Management

- Tags: auth, login
+ Section: Authentication

- Tags: health, monitoring
+ Section: Health Checks
```

### 2. Section Naming Guidelines

Use descriptive, title-case section names:

| Old Tags | New Section |
|----------|-------------|
| `users, admin` | `User Management` |
| `auth, login, session` | `Authentication` |
| `health, ping` | `Health Checks` |
| `metrics, stats` | `Metrics` |
| `orders, billing` | `Order Management` |
| `settings, config` | `Configuration` |

### 3. Router Tags Still Work

FastAPI router tags continue to work as **scaffolding hints** during documentation generation:

```python
# This still works and provides scaffolding hints
router = APIRouter(prefix="/users", tags=["users"])

@router.get("/")
def get_users():
    """Get users endpoint"""
    return {"users": []}
```

When you run `fmd-init`, it will use `users` as a scaffolding hint and suggest `User Management` as the section name.

## Intelligent Section Inference

FastMarkDocs v0.5.0 includes intelligent section inference with a 6-step fallback chain:

1. **Router tags** (scaffolding hints)
2. **Endpoint tags** (scaffolding hints)  
3. **Path-based inference** (`/users` → `User Management`)
4. **File-based inference** (`users.py` → `User Management`)
5. **Function name inference** (`get_users` → `User Management`)
6. **Ultimate fallback** (`API`)

This means even without explicit sections, the system will intelligently organize your documentation.

## Validation Changes

### New Linting Rules

The `fmd-lint` tool now enforces section requirements:

```bash
# This will now fail
$ fmd-lint

❌ Missing Section: GET /users endpoint missing required Section: line
💡 Add 'Section: User Management' to your documentation
```

### Error Messages

All error messages now reference "sections" instead of "tags":

```
❌ Endpoint GET /users is missing required Section: line
💡 Choose an appropriate section name like 'User Management', 'Authentication', 'Health', etc.
```

## Configuration Updates

If you're using configuration files that reference `tag_order`, update them to `sections_order`:

```yaml
# Old
tag_order:
  - users
  - auth
  - health

# New  
sections_order:
  - "User Management"
  - "Authentication"
  - "Health Checks"
```

## Automated Migration

### Using sed (Unix/Linux/macOS)

```bash
# Basic Tags → Section replacement
find docs/ -name "*.md" -exec sed -i 's/^Tags:/Section:/g' {} \;

# Convert common tag patterns to sections
find docs/ -name "*.md" -exec sed -i 's/Section: users.*/Section: User Management/g' {} \;
find docs/ -name "*.md" -exec sed -i 's/Section: auth.*/Section: Authentication/g' {} \;
find docs/ -name "*.md" -exec sed -i 's/Section: health.*/Section: Health Checks/g' {} \;
```

### Using Python Script

```python
import re
from pathlib import Path

def migrate_file(file_path):
    content = file_path.read_text()
    
    # Replace Tags: with Section:
    content = re.sub(r'^Tags:\s*(.+)$', lambda m: f'Section: {convert_tags_to_section(m.group(1))}', content, flags=re.MULTILINE)
    
    file_path.write_text(content)

def convert_tags_to_section(tags_str):
    """Convert comma-separated tags to a single section name"""
    tags = [tag.strip() for tag in tags_str.split(',')]
    
    # Common mappings
    mappings = {
        'users': 'User Management',
        'auth': 'Authentication', 
        'health': 'Health Checks',
        'metrics': 'Metrics',
        'orders': 'Order Management',
        'settings': 'Configuration'
    }
    
    # Use first tag's mapping or title case
    first_tag = tags[0].lower()
    return mappings.get(first_tag, first_tag.replace('-', ' ').replace('_', ' ').title())

# Migrate all markdown files
for md_file in Path('docs').rglob('*.md'):
    migrate_file(md_file)
```

## Testing Your Migration

1. **Run the linter:**
   ```bash
   fmd-lint
   ```

2. **Check for missing sections:**
   ```bash
   # Should show no "missing section" errors
   fmd-lint --format json | jq '.incomplete_documentation[] | select(.issues[] | contains("missing_section"))'
   ```

3. **Verify section organization:**
   ```bash
   # Generate OpenAPI spec and check tag organization
   python -c "
   from your_app import app
   import json
   print(json.dumps(app.openapi()['tags'], indent=2))
   "
   ```

## Troubleshooting

### Common Issues

**Issue:** `fmd-lint` reports missing sections
```
❌ Endpoint GET /users is missing required Section: line
```

**Solution:** Add a `Section:` line to each endpoint in your markdown files.

**Issue:** Multiple sections per endpoint
```
Section: User Management, Admin Panel  # ❌ Not supported
```

**Solution:** Choose one primary section per endpoint:
```
Section: User Management  # ✅ Correct
```

**Issue:** Lowercase section names
```
Section: user management  # ❌ Not recommended
```

**Solution:** Use title case:
```
Section: User Management  # ✅ Recommended
```

## Benefits of the New Approach

1. **🎯 Clear Separation**: Documentation sections are separate from FastAPI operational tags
2. **📝 Better Organization**: Single, descriptive section names improve readability
3. **🤖 Intelligent Inference**: Automatic section detection reduces manual work
4. **🔍 Better Validation**: Stricter linting ensures complete documentation
5. **🚀 Future-Proof**: Cleaner architecture for future enhancements

## Need Help?

- **Documentation Issues**: Check the updated examples in the README
- **Migration Problems**: Use the automated scripts above
- **Complex Cases**: Create an issue on GitHub with your specific use case

## Version Compatibility

- **v1.x**: Uses `Tags:` approach (deprecated)
- **v2.0+**: Uses `Section:` approach (current)
- **Migration Window**: Both approaches supported during transition period

---

**Next Steps:** After migration, run `fmd-lint` to ensure all documentation meets the new requirements, then enjoy the improved organization and intelligent section inference!
