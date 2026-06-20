import json
import yaml

with open('en_raw.json', 'r', encoding='utf-8') as f:
    en = json.load(f)
with open('zh_raw.json', 'r', encoding='utf-8') as f:
    zh = json.load(f)

# we need to match categories
categories = []

for i, c_en in enumerate(en):
    c_zh = zh[i] if i < len(zh) else {'title': '', 'groups': []}

    cat = {
        'title_en': c_en['title'],
        'title_zh': c_zh['title'],
        'groups': []
    }

    for j, g_en in enumerate(c_en['groups']):
        g_zh = c_zh['groups'][j] if j < len(c_zh['groups']) else {'name': '', 'items': [], 'texts': []}

        group = {
            'name_en': g_en['name'],
            'name_zh': g_zh['name'],
            'items': [],
            'texts_en': g_en['texts'],
            'texts_zh': g_zh['texts']
        }

        # Match items by URL or Name
        zh_items_by_url = {item['url']: item for item in g_zh['items']}
        zh_items_by_name = {item['name'].lower(): item for item in g_zh['items']}

        for item_en in g_en['items']:
            url = item_en['url']
            name = item_en['name']

            zh_item = zh_items_by_url.get(url)
            if not zh_item:
                zh_item = zh_items_by_name.get(name.lower())

            item = {
                'name': name,
                'url': url,
                'desc_en': item_en['desc'],
                'desc_zh': zh_item['desc'] if zh_item else ''
            }

            if 'subitems' in item_en:
                item['subitems'] = []
                for sub_en in item_en['subitems']:
                    sub_zh_item = None
                    if zh_item and 'subitems' in zh_item:
                        for sub_zh in zh_item['subitems']:
                            if sub_zh['url'] == sub_en['url'] or sub_zh['name'].lower() == sub_en['name'].lower():
                                sub_zh_item = sub_zh
                                break

                    sub = {
                        'name': sub_en['name'],
                        'url': sub_en['url'],
                        'desc_en': sub_en['desc'],
                        'desc_zh': sub_zh_item['desc'] if sub_zh_item else ''
                    }
                    item['subitems'].append(sub)

            group['items'].append(item)

        cat['groups'].append(group)

    categories.append(cat)

with open('data.yml', 'w', encoding='utf-8') as f:
    yaml.dump(categories, f, allow_unicode=True, sort_keys=False)
