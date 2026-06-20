import re
import json

def parse_readme(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()

    categories = []
    current_category = None
    current_group = None

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('### '):
            current_category = {
                'title': line[4:].strip(),
                'projects': []
            }
            categories.append(current_category)
            continue

        # Parse project
        # could be: [Name](url) description
        # or: * [Name](url) description
        # or: Group related:

        if line.endswith('related:'):
            current_group = line
            continue

        m = re.match(r'^(?:[\*\-]\s+)?(?:[\*\-]\s+)?\[([^\]]+)\]\(([^\)]+)\)\s*(.*)$', line)
        if m:
            name, url, desc = m.groups()
            project = {
                'name': name,
                'url': url,
                'desc': desc
            }
            if current_group:
                project['group'] = current_group
            if current_category:
                current_category['projects'].append(project)
        else:
            # Maybe text like "The standard Go [image]..."
            if current_category and not line.startswith('_') and not line.startswith('#'):
                current_category['projects'].append({'text': line})

    return categories

en = parse_readme('README.md')
zh = parse_readme('README.zh-CN.md')

print(json.dumps(en, indent=2))
