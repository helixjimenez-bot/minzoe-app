
with open('solicitudes_minzoe.py', encoding='utf-8') as f:
    lines = f.readlines()

# The for loop is at line 6701 (0-indexed: 6700), indent=20
# Body starts at line 6709 (0-indexed: 6708)
# We need to add 4 spaces to all body lines until we exit the for body
# Body ends when we see a line at indent <= 20 that is NOT blank

result = []
in_for_body = False
for_indent = 20  # spaces

for i, line in enumerate(lines):
    lineno = i + 1
    stripped = line.rstrip('\n').lstrip()
    current_indent = len(line.rstrip('\n')) - len(stripped) if stripped else 0

    # Mark start of for body (line after the for statement)
    if lineno == 6702 and not in_for_body:
        in_for_body = True

    if in_for_body:
        if stripped == '':
            result.append(line)
            continue
        # Check if we've exited the for body
        # Exit when indent <= for_indent and it's a real statement (not for body)
        if current_indent <= for_indent and stripped:
            # But first check if this is actually a continuation of the outer for
            # The outer for (sed loop) is at indent=16, so anything at indent 20 or less
            # that is NOT a continuation of the inner for should stop
            # The inner for body should be at indent 24
            # Lines at 20 that belong to outer for loop structure should stop the inner for
            if current_indent <= for_indent:
                in_for_body = False
                result.append(line)
                continue
        # Add 4 spaces to bring to correct indent (24)
        result.append('    ' + line)
        continue

    result.append(line)

with open('solicitudes_minzoe.py', 'w', encoding='utf-8') as f:
    f.writelines(result)

import ast
try:
    src = open('solicitudes_minzoe.py', encoding='utf-8').read()
    ast.parse(src)
    print("OK - sintaxis correcta")
except SyntaxError as e:
    print(f"Error linea {e.lineno}: {e.msg}")
    src_lines = src.splitlines()
    for j in range(max(0,e.lineno-3), min(len(src_lines), e.lineno+2)):
        print(f"  {j+1}: {src_lines[j]}")
