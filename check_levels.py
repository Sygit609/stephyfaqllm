#!/usr/bin/env python3
import requests
import json

COURSE_ID = "233efed3-6f20-4f9c-a15a-1b3ee17118dd"

response = requests.get(f"http://localhost:8001/api/admin/courses/{COURSE_ID}/tree")
data = response.json()['course']

def find_module1(node):
    if 'Module-1-Craft-Offers' in node.get('name', ''):
        return node
    for child in node.get('children', []):
        result = find_module1(child)
        if result:
            return result
    return None

module1 = find_module1(data)
if module1:
    print(f'Module 1: level={module1.get("hierarchy_level")}, type={module1.get("type")}')
    print('\nChildren:')
    for child in module1.get('children', []):
        print(f'  {child["name"]}: level={child.get("hierarchy_level")}, type={child.get("type")}')
