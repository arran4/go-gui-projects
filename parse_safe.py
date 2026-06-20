import re
import yaml
import os

def parse_md(filename, is_zh=False):
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    categories = []
    current_category = None

    # We want to keep track of the category title
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

        # Match projects: maybe lists like "* [Name](URL) Description"
        # or "[Name](URL) Description"
        m = re.search(r'\[([^\]]+)\]\(([^\)]+)\)\s*(.*)', line)
        if m and current_category is not None:
            name, url, desc = m.groups()

            # Sub-items might have leading text, but regex handles it mostly.

            current_category['items'].append({
                'name': name,
                'url': url,
                'desc': desc.strip()
            })

    return categories

en_cats = parse_md('README.md')
zh_cats = parse_md('README.zh-CN.md', True)

# Build zh dictionary by URL
zh_dict = {}
for cat in zh_cats:
    for item in cat['items']:
        zh_dict[item['url']] = item['desc']

zh_title_dict = {
    'native GUI and utility bindings': '本机 GUI 和实用程序绑定',
    'HTML based GUI': '基于 HTML 的 GUI',
    'custom GUI': '自定义 GUI',
    '3D graphics and computing API bindings': '3D 图形和计算 API 绑定',
    '2D vector graphics and computing APIs': '2D矢量图形和计算API',
    'font processing related': '字体处理相关',
    'CAD related': 'CAD 相关',
    'game development related': 'game development related', # matching zh README
    'image processing related': '图像处理相关',
    'terminal UI': '终端界面'
}

unified = []
for cat in en_cats:
    cat_zh_title = zh_title_dict.get(cat['title'], cat['title'])

    u_cat = {
        'title_en': cat['title'],
        'title_zh': cat_zh_title,
        'items': []
    }

    for item in cat['items']:
        zh_desc = zh_dict.get(item['url'], '')

        # In EN file we might have markdown list prefix
        # in ZH file we might have the same

        # Remove list markers from desc
        desc_en = item['desc']
        if desc_en.startswith('- '): desc_en = desc_en[2:]
        if desc_en.startswith('is '): desc_en = desc_en[3:]

        if zh_desc.startswith('- '): zh_desc = zh_desc[2:]
        if zh_desc.startswith('是 '): zh_desc = zh_desc[2:]

        u_cat['items'].append({
            'name': item['name'],
            'url': item['url'],
            'desc_en': desc_en.strip(),
            'desc_zh': zh_desc.strip()
        })

    unified.append(u_cat)

os.makedirs('meta', exist_ok=True)
with open('meta/projects.yml', 'w', encoding='utf-8') as f:
    yaml.dump(unified, f, allow_unicode=True, sort_keys=False)
