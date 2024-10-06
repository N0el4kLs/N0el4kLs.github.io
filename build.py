import os
import re
import urllib.parse

# This script comes from https://github.com/N0el4kLs/weekly/blob/main/build.py

# def fetch_ci_time(file_path):
#     url = f"https://api.github.com/repos/tw93/weekly/commits?path={file_path}&page=1&per_page=1"
#     response = httpx.get(url)
#     ci_time = response.json()[0]["commit"]["committer"]["date"].split("T")[0]
#     return ci_time

if __name__ == "__main__":
    with open('README.md', 'w') as readme_file:
        header = "# My blog \n\n > This blog theme comes from [astro-paper](https://github.com/satnaing/astro-paper). \n\n"
        header += "Here is the places where I share my learnings and thoughts. Hope you enjoy it! \n\n"
        readme_file.write(header)

        for root, dirs, filenames in os.walk('./src/content/blog'):
            filenames = sorted(filenames, key=lambda x: float(re.findall(r"(\d+)-", x)[0]), reverse=True)

        for index, name in enumerate(filenames):
            need_removed_remarks = ['(', ')', '"', ',', ':']
            
            if name.endswith('.md'):
                file_path = urllib.parse.quote(name)
                old_title = name.split('.md')[0]
                fixed_title_url = old_title.lower()
                for remark in need_removed_remarks:
                    fixed_title_url = fixed_title_url.replace(remark,"")
                fixed_title_url = fixed_title_url.replace(" ","-")
                
                url = f'https://N0el4kLs.github.io/posts/{urllib.parse.quote(fixed_title_url)}'
                title = f'第 {old_title.split("-")[0]} 期 - {old_title.split("-")[1]}'
                readme_md = f'* [{title}]({url})\n'
                num = int(old_title.split('-')[0])

                readme_file.write(readme_md)