# Google Drive YAML Front Matter Format

## Overview

The CMS Automation system supports structured metadata in Google Drive documents using **YAML front matter** format. This allows you to define article metadata (title, SEO keywords, tags, categories, etc.) directly in your Google Docs before importing them into the system.

## Format Structure

YAML front matter must be placed at the **beginning** of the document, enclosed between triple dashes (`---`):

```yaml
---
title: Your Article Title
meta_description: SEO meta description (150-160 characters)
seo_keywords:
  - primary keyword
  - secondary keyword
tags:
  - Tag 1
  - Tag 2
  - Tag 3
categories:
  - Category 1
author: Author Name
---

Your article content starts here...
```

## Field Descriptions

### Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `title` | String | Article headline (max 500 chars) | `"Essential Oil Diffuser Benefits"` |

### Optional Fields

| Field | Type | Description | Best Practices |
|-------|------|-------------|----------------|
| `meta_description` | String | SEO meta description | 150-160 characters, includes primary keyword |
| `seo_keywords` | List | Keywords for search engine optimization | 1-3 core keywords for Yoast/Rank Math |
| `tags` | List | WordPress post tags for internal navigation | 3-6 natural categories (e.g., "Aromatherapy", "Home Fragrance") |
| `categories` | List | WordPress hierarchical categories | 1-3 top-level categories (e.g., "Health & Wellness") |
| `author` | String | Article author name | Full name or author ID |

## SEO Keywords vs Tags

It's important to understand the distinction between `seo_keywords` and `tags`:

### SEO Keywords (`seo_keywords`)
- **Purpose**: Search engine optimization (external)
- **Target Audience**: Google, Bing, other search engines
- **Count**: 1-3 highly focused keywords
- **Implementation**: Set via Yoast SEO or Rank Math plugins
- **Example**: `["essential oil diffuser", "aromatherapy benefits"]`

### Tags (`tags`)
- **Purpose**: Internal navigation and content organization
- **Target Audience**: Website visitors browsing content
- **Count**: 3-6 natural, descriptive categories
- **Implementation**: WordPress native taxonomy system
- **Example**: `["Aromatherapy", "Home Fragrance", "Wellness Tips", "DIY Projects"]`

## Complete Example

```yaml
---
title: "10 Surprising Benefits of Using an Essential Oil Diffuser"
meta_description: "Discover the top benefits of essential oil diffusers, from aromatherapy to air purification. Learn how to choose the best diffuser for your home."
seo_keywords:
  - essential oil diffuser
  - aromatherapy benefits
  - home air purification
tags:
  - Aromatherapy
  - Home Fragrance
  - Wellness Tips
  - Air Quality
  - DIY Projects
categories:
  - Health & Wellness
  - Home & Garden
author: Sarah Johnson
---

# 10 Surprising Benefits of Using an Essential Oil Diffuser

Essential oil diffusers have become increasingly popular in recent years, and for good reason...

[Article content continues here]
```

## Parsing Behavior

### Successful YAML Parsing
When YAML front matter is detected and successfully parsed:
- All metadata fields are extracted and stored in the system
- The article body (content after `---`) is stored separately
- Logs: `google_drive_yaml_parsed` event with field counts

### Fallback to Plain Text
If YAML parsing fails or no YAML front matter is present:
- First line becomes the title (max 500 chars)
- Remaining content becomes the body
- All optional fields default to empty/null:
  - `meta_description`: `null`
  - `seo_keywords`: `[]`
  - `tags`: `[]`
  - `categories`: `[]`
  - `author`: `null`

### Error Handling
- **Invalid YAML syntax**: Falls back to plain text parsing, logs warning
- **Missing required fields**: Uses default values (`title: "Untitled Document"`)
- **Non-list values**: Automatically converts to single-item lists

## Best Practices

### 1. Title
- Keep under 60 characters for optimal SEO
- Make it descriptive and include primary keyword
- Use title case or sentence case consistently

### 2. Meta Description
- **Length**: 150-160 characters (Google's display limit)
- Include primary keyword naturally
- Make it compelling to increase click-through rates
- Avoid keyword stuffing

### 3. SEO Keywords
- **Quantity**: 1-3 keywords maximum
- Focus on high-value, relevant keywords
- Avoid over-optimization
- Use keywords that match search intent

### 4. Tags
- **Quantity**: 3-6 tags per article
- Use natural, descriptive phrases
- Think about how users browse your site
- Examples:
  - Good: "Aromatherapy", "Home Fragrance", "Wellness Tips"
  - Bad: "essential-oil", "oil", "diffuser" (too generic/SEO-focused)

### 5. Categories
- **Quantity**: 1-3 categories
- Use your site's existing category structure
- Choose the most relevant parent category
- Don't create new categories for every article

### 6. YAML Syntax
- Use **spaces** for indentation (not tabs)
- Use **2 spaces** per indentation level
- Always use list format (`-`) for arrays
- Quote strings containing special characters:
  - Colons: `title: "How To: Essential Oils"`
  - Apostrophes: `title: "Sarah's Guide to Aromatherapy"`
  - Numbers: `title: "10 Benefits of Aromatherapy"`

## Validation

The system performs the following validation:

1. **Title length**: Truncated to 500 characters if longer
2. **List fields**: Non-list values automatically converted to single-item lists
3. **Empty documents**: Assigned `"Untitled Document"` as title
4. **Metadata preservation**: All parsed fields stored in worklist item metadata

## Testing Your YAML

Before uploading to Google Drive, test your YAML syntax using online validators:
- [YAML Lint](http://www.yamllint.com/)
- [Online YAML Parser](https://yaml-online-parser.appspot.com/)

## Troubleshooting

### Problem: YAML not being parsed

**Possible causes**:
1. Missing opening `---` delimiter
2. Missing closing `---` delimiter
3. Extra spaces/characters before opening `---`
4. Using tabs instead of spaces for indentation

**Solution**: Ensure your document starts exactly with:
```yaml
---
title: Your Title
---
```

### Problem: Lists not being recognized

**Incorrect**:
```yaml
tags: Aromatherapy, Home Fragrance, Wellness
```

**Correct**:
```yaml
tags:
  - Aromatherapy
  - Home Fragrance
  - Wellness
```

### Problem: Special characters causing errors

**Incorrect**:
```yaml
title: How To: Use Diffusers
```

**Correct**:
```yaml
title: "How To: Use Diffusers"
```

## Migration from Plain Text

If you have existing Google Docs without YAML front matter:
1. Documents will continue to work with plain text parsing
2. No action required unless you want to add structured metadata
3. To upgrade: Add YAML front matter at the top of the document
4. Re-sync the document to update metadata

## Related Documentation

- [WordPress SEO Keywords vs Tags](../../../screenshots/WordPress SEO Keywords and Tags.pdf)
- [Google Drive Integration](./google_drive_integration.md)
- [Worklist Workflow](./worklist_workflow.md)
- [Publishing API](../api-spec.yaml)

---

**Last Updated**: 2025-10-31
**Version**: 1.0
