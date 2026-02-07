# Test button title character limits (WhatsApp: max 20 chars)

buttons_en = [
    {"id": "1", "title": "Chat - TZS 3,000"},
    {"id": "2", "title": "Video - TZS 5,000"}
]

buttons_sw = [
    {"id": "1", "title": "Chat - TZS 3,000"},
    {"id": "2", "title": "Video - TZS 5,000"}
]

buttons_spec_en = [
    {"id": "1", "title": "Chat - TZS 25,000"},
    {"id": "2", "title": "Video - TZS 30,000"}
]

buttons_spec_sw = [
    {"id": "1", "title": "Chat - TZS 25,000"},
    {"id": "2", "title": "Video - TZS 30,000"}
]

print("=== BUTTON CHARACTER LIMIT TEST ===")
print("WhatsApp button limit: 20 characters")

def test_buttons(buttons, name):
    print(f"\n{name}:")
    for i, btn in enumerate(buttons, 1):
        title_len = len(btn['title'])
        status = "✅" if title_len <= 20 else "❌"
        print(f"  Button {i}: '{btn['title']}' ({title_len} chars) {status}")

test_buttons(buttons_en, "GP Buttons EN")
test_buttons(buttons_sw, "GP Buttons SW")
test_buttons(buttons_spec_en, "Specialist Buttons EN")
test_buttons(buttons_spec_sw, "Specialist Buttons SW")

# Test shorter versions if needed
short_buttons_en = [
    {"id": "1", "title": "Chat - TZS 3,000"},
    {"id": "2", "title": "Video - TZS 5,000"}
]

short_buttons_sw = [
    {"id": "1", "title": "Chat - TZS 3,000"},
    {"id": "2", "title": "Video - TZS 5,000"}
]

print(f"\n=== SHORTER VERSIONS ===")
test_buttons(short_buttons_en, "Short GP Buttons EN")
test_buttons(short_buttons_sw, "Short GP Buttons SW")
