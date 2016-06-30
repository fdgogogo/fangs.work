#!/usr/bin/env python
import yaml
import pyaml
import sys

if __name__ == "__main__":
    tag_slug = raw_input('Tag slug: ').decode(sys.stdin.encoding)
    tag_name = raw_input('Tag name: ').decode(sys.stdin.encoding)
    with open('_data/tags.yaml', 'r+') as f:
        data = yaml.load(f)
        f.seek(0)
        data[tag_slug] = {"slug": tag_slug, "name": tag_name}
        f.write(pyaml.dump(data).encode('utf8'))

    with open('tags/%s.md' % tag_slug, 'w') as f:
        f.write('---\n')
        f.write('layout: blog_by_tag\n')
        f.write('tag: %s\n' % tag_slug)
        f.write('permalink: /tags/%s/\n' % tag_slug)
        f.write('---\n')
