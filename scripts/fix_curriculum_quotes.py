import glob
import re

for p in sorted(glob.glob('/Users/nileshchakraborty/workspace/model-creator/curriculum/*.py')):
    if p.endswith('__init__.py') or p.endswith('verifier.py'):
        continue
    with open(p, 'r') as f:
        lines = f.readlines()

    fixed_lines = []
    in_r_block = False
    for line in lines:
        if re.match(r'^\s*r[_\w]*\s*=\s*r?\"\"\"', line):
            in_r_block = True
            fixed_lines.append(line)
        elif in_r_block and line.strip().endswith('```"""'):
            in_r_block = False
            fixed_lines.append(line)
        elif in_r_block:
            # Replace unescaped triple quotes with escaped triple quotes
            # Handle both raw \"\"\" and unescaped """
            clean = line.replace('\\"\\"\\"', '"""')
            fixed_lines.append(clean.replace('"""', '\\"\\"\\"'))
        else:
            fixed_lines.append(line)

    with open(p, 'w') as f:
        f.writelines(fixed_lines)

print("Check syntax:")
for p in sorted(glob.glob('/Users/nileshchakraborty/workspace/model-creator/curriculum/*.py')):
    try:
        with open(p) as f:
            compile(f.read(), p, 'exec')
        print(f'{p}: VALID SYNTAX')
    except SyntaxError as e:
        print(f'{p}: SYNTAX ERROR line {e.lineno}: {e.msg}')
