import re
import json

def parse_md(filename):
    with open(filename, 'r', encoding='utf-8') as f:
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
                'groups': []
            }
            categories.append(current_category)
            current_group = {'name': '', 'items': [], 'texts': []}
            current_category['groups'].append(current_group)
            continue

        if line.endswith('related:') or line.endswith('相关:'):
            current_group = {'name': line, 'items': [], 'texts': []}
            current_category['groups'].append(current_group)
            continue

        m = re.match(r'^(?:[\*\-]\s+)?(?:[\*\-]\s+)?\[([^\]]+)\]\(([^\)]+)\)\s*(.*)$', line)
        if m:
            name, url, desc = m.groups()
            # clean desc
            if desc.startswith('- '): desc = desc[2:]

            # handle sub-items
            is_sub = line.startswith('  *') or line.startswith('  -')

            item = {
                'name': name,
                'url': url,
                'desc': desc.strip()
            }
            if is_sub and current_group['items']:
                if 'subitems' not in current_group['items'][-1]:
                    current_group['items'][-1]['subitems'] = []
                current_group['items'][-1]['subitems'].append(item)
            else:
                current_group['items'].append(item)
        else:
            if current_category and not line.startswith('_') and not line.startswith('#'):
                current_group['texts'].append(line)

    return categories

en_cats = parse_md('README.md')
zh_cats = parse_md('README.zh-CN.md')

# Save them raw to see the structure
with open('en_raw.json', 'w', encoding='utf-8') as f:
    json.dump(en_cats, f, indent=2, ensure_ascii=False)
with open('zh_raw.json', 'w', encoding='utf-8') as f:
    json.dump(zh_cats, f, indent=2, ensure_ascii=False)
