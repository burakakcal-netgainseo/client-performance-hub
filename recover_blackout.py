
import re

try:
    with open('agent_log.txt', 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    matches = []
    for i, line in enumerate(lines):
        if 'blackout' in line.lower() or 'black out' in line.lower():
            matches.append(i)

    with open('recovery_log.txt', 'w', encoding='utf-8') as out:
        out.write(f'Found {len(matches)} matches.\n')
        # Get last 5 matches
        for i in matches[-5:]:
            out.write(f'\n--- Match at line {i} ---\n')
            start = max(0, i-20)
            end = min(len(lines), i+20)
            for j in range(start, end):
                out.write(f'{j}: {lines[j].strip()}\n')

except Exception as e:
    with open('recovery_log.txt', 'w') as out:
        out.write(f'Error: {str(e)}')
