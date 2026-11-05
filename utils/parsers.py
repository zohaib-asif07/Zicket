"""
Data Parsing Module
Contains functions for parsing match statistics from raw text
"""

import re
from typing import List, Dict

def parse_match_stats(content: str) -> List[Dict]:
    """
    Parse raw match statistics from Discord message

    Expected format:
```python
    user_id, runs, balls_played, runs_conceded, balls_bowled, wickets, not_out
    user_id, runs, balls_played, runs_conceded, balls_bowled, wickets, not_out
    ...
```

    Where not_out is:
    - 0 = player was dismissed (out)
    - 1 = player was not out at end of innings

    Args:
        content: Message content containing stats in code block

    Returns:
        List of dictionaries containing parsed statistics
        Returns empty list if parsing fails
    """
    # Find all code blocks (```python ... ```)
    pattern = r'```python\n(.*?)```'
    matches = re.findall(pattern, content, re.DOTALL)

    if not matches:
        return []

    # Only process first block
    data_block = matches[0]
    stats = []

    for line in data_block.strip().split('\n'):
        line = line.strip()
        if not line:
            continue

        # Split by comma and clean whitespace
        parts = [p.strip() for p in line.split(',')]
        if len(parts) != 7:  # NOW REQUIRES 7 PARAMETERS
            continue

        try:
            user_id = parts[0]

            # Skip bot entries (ID 101)
            if user_id == '101':
                continue

            runs = int(parts[1])
            balls_played = int(parts[2])
            runs_conceded = int(parts[3])
            balls_bowled = int(parts[4])
            wickets = int(parts[5])
            not_out = int(parts[6])  # 0 = out, 1 = not out

            stats.append({
                'user_id': user_id,
                'runs': runs,
                'balls_played': balls_played,
                'runs_conceded': runs_conceded,
                'balls_bowled': balls_bowled,
                'wickets': wickets,
                'not_out': not_out
            })
        except ValueError:
            # Skip lines that can't be parsed as numbers
            continue

    return stats
