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
            
            if name.endswith('.md'):
                file_path = urllib.parse.quote(name)
                old_title = name.split('.md')[0]
                url = f'https://N0el4kLs.github.io/posts/{urllib.parse.quote(old_title.lower().replace("(","").replace(")",""))}'
                title = f'第 {old_title.split("-")[0]} 期 - {old_title.split("-")[1]}'
                readme_md = f'* [{title}]({url})\n'
                num = int(old_title.split('-')[0])

                readme_file.write(readme_md)