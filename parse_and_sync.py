import re
import yaml

def parse_md(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    categories = []
    current_category = None

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('### '):
            current_category = {
                'title': line[4:].strip(),
                'items': []
            }
            categories.append(current_category)
            continue

        # Try to parse [Name](Link) Description
        # We might have sub-items like "* [Name](Link) Description" or just text.
        m = re.search(r'\[(.*?)\]\((.*?)\)\s*(.*)', line)
        if m and current_category is not None:
            name, link, desc = m.groups()
            # Clean up desc
            if desc.startswith('is '):
                desc = desc
            elif desc.startswith('- '):
                desc = desc[2:]

            # Check depth by looking at leading spaces/stars in the original line
            # Actually, let's keep it flat for the metadata and let the template render them as a simple list.
            current_category['items'].append({
                'name': name,
                'link': link,
                'desc': desc.strip()
            })
        elif current_category is not None and not line.startswith('_') and not line.startswith('#'):
            # Just some text, maybe we ignore or keep it?
            pass

    return categories

en_data = parse_md('README.md')
zh_data = parse_md('README.zh-CN.md')

# Build a lookup for zh descriptions by link
zh_lookup = {}
for cat in zh_data:
    for item in cat['items']:
        zh_lookup[item['link']] = item['desc']

# Create unified data
unified = []
for cat in en_data:
    # Need to translate category titles
    # Let's find matching zh category
    cat_zh_title = cat['title']
    for zcat in zh_data:
        # crude match, we can manually fix the titles later
        pass

    u_cat = {
        'title_en': cat['title'],
        'title_zh': '', # Will fill manually or from lookup
        'items': []
    }
    for item in cat['items']:
        desc_zh = zh_lookup.get(item['link'], '')
        u_cat['items'].append({
            'name': item['name'],
            'link': item['link'],
            'desc_en': item['desc'],
            'desc_zh': desc_zh
        })
    unified.append(u_cat)

with open('projects.yml', 'w', encoding='utf-8') as f:
    yaml.dump(unified, f, allow_unicode=True, sort_keys=False)
