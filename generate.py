import yaml
import os

with open('data/projects.yml', 'r', encoding='utf-8') as f:
    categories = yaml.safe_load(f)

# Sort projects alphabetically in each category
for cat in categories:
    cat['items'].sort(key=lambda x: x['name'].lower())

def render_md(categories, lang='en'):
    lines = []
    if lang == 'en':
        lines.append('_(Please follow [@zigo_101](https://twitter.com/zigo_101) for updates on this page, and all kinds of details and facts in Go)._')
        lines.append('')
        lines.append('----')
        lines.append('')
        lines.append('# A list of Go GUI/graphics/image related projects')
        lines.append('')
        lines.append('<!-- BEGIN AUTOMATED SECTION -->')
        lines.append('')
    else:
        lines.append('_(请关注 [@zigo_101](https://twitter.com/zigo_101)了解此页面的更新以及 Go 编程中的各种详细信息和事实)._')
        lines.append('')
        lines.append('----')
        lines.append('')
        lines.append('# Go GUI/图形/图像相关项目列表')
        lines.append('')
        lines.append('<!-- BEGIN AUTOMATED SECTION -->')
        lines.append('')

    for cat in categories:
        title = cat.get('title_' + lang, cat.get('title_en'))
        if not title:
            title = cat.get('title_en') # fallback
        lines.append(f"### {title}")
        lines.append('')
        for item in cat['items']:
            desc = item.get('desc_' + lang, '')
            if not desc:
                # fall back to english desc if zh is missing
                desc = item.get('desc_en', '')

            # small cleanups
            desc = desc.strip()

            # format as bullet or just standard?
            # looking at original, it was mostly just `[Name](link) desc` with occasional sublists
            # Since we just flattened everything, let's render as standard list with bullets maybe?
            # Or just space separated like original
            lines.append(f"[{item['name']}]({item['link']}) {desc}")
            lines.append('')

    lines.append('<!-- END AUTOMATED SECTION -->')
    lines.append('')
    return '\n'.join(lines)

with open('README.md', 'w', encoding='utf-8') as f:
    f.write(render_md(categories, 'en'))

with open('README.zh-CN.md', 'w', encoding='utf-8') as f:
    f.write(render_md(categories, 'zh'))
