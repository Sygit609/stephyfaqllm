#!/usr/bin/env python3
import requests
import json

COURSE_ID = "233efed3-6f20-4f9c-a15a-1b3ee17118dd"

response = requests.get(f"http://localhost:8001/api/admin/courses/{COURSE_ID}/tree")
data = response.json()['course']

def print_tree(node, indent=0):
    prefix = '  ' * indent
    node_type = node.get('type', 'unknown')
    children_count = len(node.get('children', []))
    print(f'{prefix}- {node["name"]} (type={node_type}, children={children_count})')
    for child in node.get('children', []):
        if child.get('type') != 'segment':
            print_tree(child, indent + 1)

print_tree(data)
