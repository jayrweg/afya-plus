import json

# Test the exact payload being sent
message = "Afyaplus inakuletea huduma zifuatazo,chagua"
sections = [{
    "title": "Matibabu",
    "rows": [
        {"id": "1", "title": "🩺 Daktari jumla (GP)"},
        {"id": "2", "title": "👨‍⚕️ Daktari bingwa"},
        {"id": "3", "title": "🏠 Daktari nyumbani"},
        {"id": "4", "title": "🏢 Afya ya kazi"},
        {"id": "5", "title": "💊 Dawa na madawa"}
    ]
}]

# Format sections for WhatsApp API
section_objects = []
for section in sections[:10]:  # WhatsApp supports max 10 sections
    rows = []
    for row in section.get("rows", [])[:10]:  # Max 10 rows per section
        rows.append({
            "id": row.get("id", ""),
            "title": row.get("title", ""),
            "description": row.get("description", "")
        })
    
    section_objects.append({
        "title": section.get("title", ""),
        "rows": rows
    })

payload = {
    "messaging_product": "whatsapp",
    "to": "255627404843",
    "type": "interactive",
    "interactive": {
        "type": "list",
        "body": {"text": message},
        "action": {
            "button": "Chagua huduma",
            "sections": section_objects
        }
    }
}

print("WhatsApp List Payload:")
print(json.dumps(payload, indent=2, ensure_ascii=False))

# Check for potential issues
print("\n=== Potential Issues ===")
print(f"Message length: {len(message)} chars")
print(f"Number of sections: {len(section_objects)}")
print(f"Number of rows in first section: {len(section_objects[0]['rows']) if section_objects else 0}")
print(f"Button text: '{payload['interactive']['action']['button']}'")
print(f"Button text length: {len(payload['interactive']['action']['button'])}")

# Check row titles for issues
for i, row in enumerate(section_objects[0]['rows']):
    print(f"Row {i+1} title length: {len(row['title'])} chars")
    if len(row['title']) > 20:
        print(f"  ⚠️  Row {i+1} title might be too long")
