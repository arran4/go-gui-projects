import re
import yaml

def extract_projects(filename, is_zh=False):
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

        # Match projects: [Name](URL) Description
        m = re.search(r'\[([^\]]+)\]\(([^\)]+)\)\s*(.*)', line)
        if m and current_category is not None:
            name, url, desc = m.groups()

            # Clean up desc
            if desc.startswith('- '): desc = desc[2:]
            elif desc.startswith('is '): desc = desc[3:]
            elif desc.startswith('are '): desc = desc[4:]
            elif desc.startswith('是 '): desc = desc[2:]

            # handle 'old name: MacDriver' etc.

            # Sub-items might have leading text, but regex handles it mostly.
            # Exceptions like "The standard Go [image](url) packages."
            # We can check if name is "image" and URL is "https://golang.org/pkg/image/"

            current_category['items'].append({
                'name': name,
                'url': url,
                'desc': desc.strip()
            })

    return categories

en_cats = extract_projects('README.md')
zh_cats = extract_projects('README.zh-CN.md', True)

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
    'game development related': '游戏开发相关',
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
        # Try to find zh desc
        zh_desc = zh_dict.get(item['url'], '')
        if not zh_desc:
            # Maybe URL had a trailing slash or something
            for k, v in zh_dict.items():
                if k.strip('/') == item['url'].strip('/'):
                    zh_desc = v
                    break

        u_cat['items'].append({
            'name': item['name'],
            'url': item['url'],
            'desc_en': item['desc'],
            'desc_zh': zh_desc
        })

    unified.append(u_cat)

with open('data.yml', 'w', encoding='utf-8') as f:
    yaml.dump(unified, f, allow_unicode=True, sort_keys=False)
