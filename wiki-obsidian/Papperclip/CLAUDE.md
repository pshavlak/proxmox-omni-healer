# Papperclip LLM Wiki

This wiki follows the Karpathy LLM Wiki pattern. The LLM maintains this wiki incrementally.

## Directory Structure

```
Papperclip/
├── CLAUDE.md       # This file — schema and conventions
├── raw/            # Raw source documents (immutable, LLM reads only)
└── wiki/           # LLM-maintained markdown files
    ├── index.md    # Content catalog — every page listed with link and summary
    └── log.md      # Chronological activity log
```

## Naming Conventions

- Wiki page filenames: kebab-case, `.md` extension
- Each page starts with `# Title` (h1 matching filename)
- Use `[[wikilinks]]` for cross-references between wiki pages
- Use `[source](</raw/filename>)` to reference raw sources
- Add YAML frontmatter with `tags:`, `created:`, `updated:` where useful

## Ingestion Workflow

When a new source is added to `raw/`:
1. Read the source document
2. Discuss key takeaways with the user
3. Write a summary page in `wiki/`
4. Create or update entity/concept pages
5. Add cross-references between related pages
6. Update `wiki/index.md` — add new pages to catalog
7. Append entry to `wiki/log.md` with `## [YYYY-MM-DD] ingest | Title` format

## Query Workflow

When the user asks a question:
1. Read `wiki/index.md` to find relevant pages
2. Read relevant pages
3. Synthesize answer with `[wikilinks]` citations
4. If the answer adds lasting value — file it as a new wiki page and update index+log

## Maintenance / Lint

Periodically (or on request):
- Check for broken `[[wikilinks]]` and orphan pages
- Flag contradictions between pages
- Suggest new pages for concepts mentioned but not yet written
- Update `wiki/index.md` if any pages are missing from it
- Check `wiki/log.md` is parseable with `grep "^## \[" log.md`

## Git

- This vault is a git repo. Commit after meaningful changes.
- Standard commit message format.

## User Preferences

- Краткие ответы, минимум текста, фокус на действиях
- Избегать длинных объяснений
