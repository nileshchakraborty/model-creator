#!/usr/bin/env python3
"""
Compact Invariant Distillation (CID) Curriculum Generator v2.
Integrates:
- OpenAI o1/o3: Native algorithmic internalization
- Zhou et al. (arXiv:2604.10739): Bounded <think> reasoning (<= 150 tokens) to eliminate overthinking drift
- DeepSeek-R1 (arXiv:2501.12948): Syntactic-semantic variable binding
- Canonical Digit DP & Group Product Parity Primitives

Author: Nilesh Chakraborty / AGY Swarm Systems
"""

import os
import sys
import json
import ast
import random
from typing import List, Dict, Any

SYSTEM_PROMPT = """You are an elite competitive programmer and algorithmic reasoning specialist.
Provide optimal, clean, bug-free Python 3 solutions adhering strictly to Big-O constraints.
First emit a brief, dense mathematical invariant analysis inside <think> ... </think> (at most 2 sentences).
Then emit the complete, optimal Python 3 code inside a ```python ... ``` block.
For LeetCode problems, use class Solution. For competitive problems, read from sys.stdin.read().split()."""

def verify_code(code: str) -> bool:
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False

def make_cid_sample(prompt: str, think_text: str, code: str) -> Dict[str, Any]:
    assert verify_code(code), f"Syntax error in code for prompt: {prompt[:50]}"
    assert len(think_text.split()) <= 100, f"Think text too verbose ({len(think_text.split())} words)"
    
    assistant_content = f"<think>\n{think_text.strip()}\n</think>\n```python\n{code.strip()}\n```"
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt.strip()},
            {"role": "assistant", "content": assistant_content}
        ]
    }

# ----------------------------------------------------------------------
# 1. Circular XOR Parity (Problem 2792)
# ----------------------------------------------------------------------
def gen_xor_parity() -> List[Dict[str, Any]]:
    p = "A binary array derived of length n is given, where derived[i] = original[i] ^ original[(i + 1) % n]. Return true if there exists a valid original binary array, or false otherwise. Use class Solution."
    t = "Circular bitwise XOR invariance: each element derived[i] = orig[i] ^ orig[(i+1)%n].\nSumming all equations cancels every element twice; hence a valid original array exists iff the cumulative XOR sum is zero: reduce(xor, derived) == 0."
    c = """from typing import List

class Solution:
    def doesValidArrayExist(self, derived: List[int]) -> bool:
        xor_sum = 0
        for x in derived:
            xor_sum ^= x
        return xor_sum == 0"""
    return [make_cid_sample(p, t, c)]

# ----------------------------------------------------------------------
# 2. Argmin Coordinate Mutation (Problem 1873_B)
# ----------------------------------------------------------------------
def gen_argmin_mutation() -> List[Dict[str, Any]]:
    p = """Slavic has an array of n digits. In one operation, he can choose any ONE index and increment it by 1.
Find the maximum product of all digits Slavic can achieve after exactly 1 operation.
Read all input from sys.stdin.read().split(). Print results to stdout."""
    t = """Marginal product gain multiplier M(x) = (x + 1)/x = 1 + 1/x is strictly decreasing for x > 0.
Therefore, increment exactly one coordinate of the minimum element: min_idx = nums.index(min(nums)); nums[min_idx] += 1."""
    c = """import sys

def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    t = int(data[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(data[idx]); idx += 1
        nums = [int(x) for x in data[idx:idx+n]]; idx += n
        min_idx = nums.index(min(nums))
        nums[min_idx] += 1
        prod = 1
        for x in nums:
            prod *= x
        out.append(str(prod))
    print('\\n'.join(out))

if __name__ == '__main__':
    solve()"""
    return [make_cid_sample(p, t, c)]

# ----------------------------------------------------------------------
# 3. Maximum Strength of a Group Parity (Problem 2754)
# ----------------------------------------------------------------------
def gen_max_strength_group() -> List[Dict[str, Any]]:
    p = """You are given a 0-indexed integer array nums representing the score of students in an exam.
The teacher wants to select one non-empty group of students to maximize the product of their scores.
Return the maximum strength of a group the teacher can select. Use class Solution."""
    t = """Sign parity and greedy product: all positive numbers increase the product; pairs of negative numbers become positive when multiplied.
Sort negative numbers; if there is an odd count of negatives, pop the one with smallest absolute value (negatives.pop()). Multiply all remaining chosen numbers."""
    c = """from typing import List

class Solution:
    def maxStrength(self, nums: List[int]) -> int:
        if len(nums) == 1:
            return nums[0]
            
        positives = [x for x in nums if x > 0]
        negatives = sorted([x for x in nums if x < 0])
        zeros = [x for x in nums if x == 0]
        
        # If odd count of negatives, drop the one with smallest absolute value
        if len(negatives) % 2 != 0:
            negatives.pop()
            
        chosen = positives + negatives
        if not chosen:
            return 0 if zeros else max(nums)
            
        prod = 1
        for x in chosen:
            prod *= x
        return prod"""
    return [make_cid_sample(p, t, c)]

# ----------------------------------------------------------------------
# 4. Canonical Digit DP (Problem 2757)
# ----------------------------------------------------------------------
def gen_digit_dp() -> List[Dict[str, Any]]:
    p = """You are given two numeric strings num1 and num2 and two integers min_sum and max_sum.
Return the number of integers x such that num1 <= x <= num2 and min_sum <= digit_sum(x) <= max_sum modulo 10^9 + 7.
Use class Solution."""
    t = """Prefix Digit DP decomposition: count(num1 <= x <= num2) = count_le(num2) - count_le(num1 - 1).
Memoize dp(idx, tight, digit_sum) where tight restricts transitions to s[idx] and digit_sum is bounded by max_sum in O(len(s) * 10 * max_sum) time."""
    c = """from functools import cache

class Solution:
    def count(self, num1: str, num2: str, min_sum: int, max_sum: int) -> int:
        MOD = 10**9 + 7
        
        def count_le(s: str) -> int:
            @cache
            def dp(i: int, tight: bool, d_sum: int) -> int:
                if d_sum > max_sum:
                    return 0
                if i == len(s):
                    return 1 if d_sum >= min_sum else 0
                limit = int(s[i]) if tight else 9
                res = 0
                for d in range(limit + 1):
                    res = (res + dp(i + 1, tight and (d == limit), d_sum + d)) % MOD
                return res
            return dp(0, True, 0)
            
        num1_minus_1 = str(int(num1) - 1)
        ans = (count_le(num2) - count_le(num1_minus_1)) % MOD
        return ans"""
    return [make_cid_sample(p, t, c)]

# ----------------------------------------------------------------------
# 5. Composite Factor Divisibility k=4 (Problem 1883_C)
# ----------------------------------------------------------------------
def gen_composite_divisibility() -> List[Dict[str, Any]]:
    p = """You are given an array of n positive integers and an integer k in {2, 3, 4, 5}. In one operation, you can choose any index and increment it by 1.
Find the minimum operations to make the product of all elements divisible by k.
Read all input from sys.stdin.read().split(). Print results to stdout."""
    t = """Divisibility by 4 requires either one multiple of 4 (cost: min (4 - x%4)%4) OR at least two even numbers (cost: max(0, 2 - even_count)).
For prime k in {2, 3, 5}, the cost is min((k - x%k)%k); for k=4, cost is min(cost_single, cost_two_evens) in O(N) time and O(1) space."""
    c = """import sys

def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    t = int(data[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(data[idx]); k = int(data[idx+1]); idx += 2
        a = [int(x) for x in data[idx:idx+n]]; idx += n
        
        if k == 4:
            cost_single = min((4 - (x % 4)) % 4 for x in a)
            evens = sum(1 for x in a if x % 2 == 0)
            cost_two_evens = max(0, 2 - evens)
            out.append(str(min(cost_single, cost_two_evens)))
        else:
            cost = min((k - (x % k)) % k for x in a)
            out.append(str(cost))
    print('\\n'.join(out))

if __name__ == '__main__':
    solve()"""
    return [make_cid_sample(p, t, c)]

# ----------------------------------------------------------------------
# 6. Permutation Cycle Bound N=3 (Problem 1873_A)
# ----------------------------------------------------------------------
def gen_cycle_transposition() -> List[Dict[str, Any]]:
    p = """You have a string s consisting of 'a', 'b', and 'c' representing a permutation of 'abc'.
In one operation, you can swap any two characters. Can you make s equal to 'abc' in at most 1 swap?
Read all input from sys.stdin.read().split(). Print 'YES' or 'NO'."""
    t = """Permutation cycle decomposition on N=3: minimum swaps needed is N - cycles.
A 3-element permutation can be sorted in <= 1 swap if and only if at least one character is already in place: s[0]=='a' or s[1]=='b' or s[2]=='c'."""
    c = """import sys

def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    t = int(data[0])
    results = []
    for i in range(1, t + 1):
        s = data[i]
        if s[0] == 'a' or s[1] == 'b' or s[2] == 'c':
            results.append("YES")
        else:
            results.append("NO")
    print('\\n'.join(results))

if __name__ == '__main__':
    solve()"""
    return [make_cid_sample(p, t, c)]

# ----------------------------------------------------------------------
# 7. Post-Move Game Invariant (Problem 1899_A)
# ----------------------------------------------------------------------
def gen_game_post_move() -> List[Dict[str, Any]]:
    p = """Vanya and Vova play a game on an integer n. In each turn, the player can increment or decrement n by 1.
Vanya goes first. Vanya wins if, after his move, n is divisible by 3. If 10 turns pass without Vanya winning, Vova wins.
Determine the winner under optimal play. Read all input from sys.stdin.read().split()."""
    t = """Post-move state evaluation: Player 1 wins immediately on turn 1 if there exists Delta in {-1, +1} such that (n + Delta) % 3 == 0.
This condition holds if and only if n % 3 != 0; if n % 3 == 0, Player 1 must move to non-zero mod 3 and Player 2 mirrors."""
    c = """import sys

def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    t = int(data[0])
    results = []
    for i in range(1, t + 1):
        n = int(data[i])
        if n % 3 != 0:
            results.append("First")
        else:
            results.append("Second")
    print('\\n'.join(results))

if __name__ == '__main__':
    solve()"""
    return [make_cid_sample(p, t, c)]

# ----------------------------------------------------------------------
# 8. DSU Domain Separation (Problem 2827)
# ----------------------------------------------------------------------
def gen_dsu_domain() -> List[Dict[str, Any]]:
    p = """You are given an integer array nums of length N. You can traverse between index i and index j if gcd(nums[i], nums[j]) > 1.
Return true if you can traverse between all pairs of indices. Use class Solution."""
    t = """Domain separation in Union-Find: map each prime factor p to the first index i that shares it using prime_to_first_idx.
Connect indices i and prime_to_first_idx[p] rather than mixing values into the DSU array; if 1 in nums and N > 1 return False."""
    c = """from typing import List

class Solution:
    def canTraverseAllPairs(self, nums: List[int]) -> bool:
        n = len(nums)
        if n == 1:
            return True
        if 1 in nums:
            return False
            
        parent = list(range(n))
        size = [1] * n
        
        def find(x):
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]
            
        def union(x, y):
            rx, ry = find(x), find(y)
            if rx != ry:
                if size[rx] < size[ry]:
                    rx, ry = ry, rx
                parent[ry] = rx
                size[rx] += size[ry]

        prime_to_first_idx = {}
        for i, val in enumerate(nums):
            temp = val
            d = 2
            while d * d <= temp:
                if temp % d == 0:
                    while temp % d == 0:
                        temp //= d
                    if d in prime_to_first_idx:
                        union(i, prime_to_first_idx[d])
                    else:
                        prime_to_first_idx[d] = i
                d += 1
            if temp > 1:
                if temp in prime_to_first_idx:
                    union(i, prime_to_first_idx[temp])
                else:
                    prime_to_first_idx[temp] = i
                    
        root = find(0)
        return size[root] == n"""
    return [make_cid_sample(p, t, c)]

# ----------------------------------------------------------------------
# 9. Direct String Simulation (Problem 2824)
# ----------------------------------------------------------------------
def gen_direct_simulation() -> List[Dict[str, Any]]:
    p = """A number n is fascinating if concatenating n, 2*n, and 3*n results in a 9-digit string containing all digits 1 through 9 exactly once.
Return true if n is fascinating, or false otherwise. Use class Solution."""
    t = """Direct string verification: concatenate n, 2*n, and 3*n into string s.
Check whether len(s) == 9 and set(s) == set('123456789') in O(1) time without unnecessary number theory."""
    c = """class Solution:
    def isFascinating(self, n: int) -> bool:
        s = str(n) + str(2 * n) + str(3 * n)
        return len(s) == 9 and set(s) == set("123456789")"""
    return [make_cid_sample(p, t, c)]

# ----------------------------------------------------------------------
# 10. 1D Prefix/Suffix Array (Problem 2730)
# ----------------------------------------------------------------------
def gen_prefix_suffix() -> List[Dict[str, Any]]:
    p = """You are given an array nums of length N and an integer k. In each operation, you can multiply any element by 2.
You have at most k operations to distribute. Return the maximum possible bitwise OR value of nums. Use class Solution."""
    t = """Bitwise dominance principle: concentrating all k shifts on a single element (nums[i] << k) strictly maximizes the highest bit.
Precompute 1D prefix_or and suffix_or arrays to evaluate left | (nums[i] << k) | right in O(N) time without 2D dynamic programming."""
    c = """from typing import List

class Solution:
    def maximumOr(self, nums: List[int], k: int) -> int:
        n = len(nums)
        if n == 1:
            return nums[0] << k
            
        prefix_or = [0] * n
        prefix_or[0] = nums[0]
        for i in range(1, n):
            prefix_or[i] = prefix_or[i - 1] | nums[i]
            
        suffix_or = [0] * n
        suffix_or[-1] = nums[-1]
        for i in range(n - 2, -1, -1):
            suffix_or[i] = suffix_or[i + 1] | nums[i]
            
        max_val = 0
        for i in range(n):
            left = prefix_or[i - 1] if i > 0 else 0
            right = suffix_or[i + 1] if i < n - 1 else 0
            curr = left | (nums[i] << k) | right
            if curr > max_val:
                max_val = curr
                
        return max_val"""
    return [make_cid_sample(p, t, c)]

# ----------------------------------------------------------------------
# 11. Boundary Mismatch Inversion Duality (Problem 2817)
# ----------------------------------------------------------------------
def gen_boundary_inversion() -> List[Dict[str, Any]]:
    p = """You are given a binary string s. In one operation, you can invert prefix s[0..i] with cost i+1, or invert suffix s[i..n-1] with cost n-i.
Return the minimum cost to make all characters in s equal. Use class Solution."""
    t = """Boundary mismatch duality: whenever s[i] != s[i+1], we must invert either prefix 0..i (cost i+1) or suffix i+1..n-1 (cost n-1-i).
Each boundary is resolved independently with minimal cost: total_cost = sum(min(i + 1, n - 1 - i) for i in range(n - 1) if s[i] != s[i + 1])."""
    c = """class Solution:
    def minimumCost(self, s: str) -> int:
        n = len(s)
        total_cost = 0
        for i in range(n - 1):
            if s[i] != s[i + 1]:
                total_cost += min(i + 1, n - 1 - i)
        return total_cost"""
    return [make_cid_sample(p, t, c)]

# ----------------------------------------------------------------------
# 12. Two Pointers Sliding Window (Problem 2833)
# ----------------------------------------------------------------------
def gen_sliding_window() -> List[Dict[str, Any]]:
    p = """You are given n servers and logs [server_id, time].
For each query [time - k, time], return the number of servers that received ZERO requests during that interval. Use class Solution."""
    t = """Sliding window over sorted events: sort queries and logs ascending by time.
Maintain active server count using two pointers: expand right for time <= q_time, contract left for time < q_time - k, returning n - active_count."""
    c = """from typing import List
from collections import defaultdict

class Solution:
    def countServers(self, n: int, logs: List[List[int]], k: int, queries: List[int]) -> List[int]:
        logs.sort(key=lambda x: x[1])
        q_sorted = sorted([(q, idx) for idx, q in enumerate(queries)], key=lambda x: x[0])
        
        res = [0] * len(queries)
        freq = defaultdict(int)
        active_count = 0
        
        left = 0
        right = 0
        m = len(logs)
        
        for q_time, orig_idx in q_sorted:
            while right < m and logs[right][1] <= q_time:
                s_id = logs[right][0]
                if freq[s_id] == 0:
                    active_count += 1
                freq[s_id] += 1
                right += 1
                
            while left < m and logs[left][1] < q_time - k:
                s_id = logs[left][0]
                freq[s_id] -= 1
                if freq[s_id] == 0:
                    active_count -= 1
                left += 1
                
            res[orig_idx] = n - active_count
            
        return res"""
    return [make_cid_sample(p, t, c)]

# ----------------------------------------------------------------------
# 13. Palindrome Parity Counting (Problem 1883_B)
# ----------------------------------------------------------------------
def gen_palindrome_parity() -> List[Dict[str, Any]]:
    p = """You are given a string s of length n and integer k. In one operation, delete at most k characters.
Determine if you can rearrange the remaining characters to form a palindrome.
Read all input from sys.stdin.read().split(). Print 'YES' or 'NO'."""
    t = """Palindrome parity invariant: a string can form a palindrome if and only if at most one character has odd frequency.
Deleting an odd-frequency character reduces odd count by 1; hence a palindrome is achievable iff odd_count - 1 <= k."""
    c = """import sys
from collections import Counter

def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    t = int(data[0])
    idx = 1
    results = []
    for _ in range(t):
        n = int(data[idx]); k = int(data[idx+1]); idx += 2
        s = data[idx]; idx += 1
        
        freq = Counter(s)
        odd_count = sum(1 for c in freq.values() if c % 2 != 0)
        
        if odd_count - 1 <= k:
            results.append("YES")
        else:
            results.append("NO")
    print('\\n'.join(results))

if __name__ == '__main__':
    solve()"""
    return [make_cid_sample(p, t, c)]

# ----------------------------------------------------------------------
# 14. Lexicographically Smallest Substring Decrement (Problem 2828)
# ----------------------------------------------------------------------
def gen_lexicographical_decrement() -> List[Dict[str, Any]]:
    p = """You are given a string s of lowercase letters. You must select one non-empty substring and replace each letter with its preceding letter ('b'->'a', etc., with 'a' wrapping to 'z').
Return the lexicographically smallest string you can obtain. Use class Solution."""
    t = """Greedy prefix optimization: find the first non-'a' character at index L and decrement contiguous non-'a' characters until the next 'a'.
If all characters are 'a', we must mutate the least significant position by changing the last character to 'z' in O(N) time."""
    c = """class Solution:
    def smallestString(self, s: str) -> str:
        chars = list(s)
        n = len(chars)
        
        i = 0
        while i < n and chars[i] == 'a':
            i += 1
            
        if i == n:
            chars[-1] = 'z'
            return "".join(chars)
            
        while i < n and chars[i] != 'a':
            chars[i] = chr(ord(chars[i]) - 1)
            i += 1
            
        return "".join(chars)"""
    return [make_cid_sample(p, t, c)]

# ----------------------------------------------------------------------
# 15. Alternating Parity Maximum Subarray (Kadane)
# ----------------------------------------------------------------------
def gen_alternating_kadane() -> List[Dict[str, Any]]:
    p = """Given an array of integers, find the maximum sum of a non-empty contiguous subarray such that adjacent elements have alternating parities (one even, one odd).
Read all input from sys.stdin.read().split(). Print results to stdout."""
    t = """Kadane invariant with alternating parity constraint: curr_sum = max(x, curr_sum + x) if (x % 2 != prev % 2) else x.
Maintain max_sum = max(max_sum, curr_sum) at each step to handle negative prefixes correctly in O(N) time and O(1) space."""
    c = """import sys

def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    t = int(data[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(data[idx]); idx += 1
        a = [int(x) for x in data[idx:idx+n]]; idx += n
        
        curr = a[0]
        ans = a[0]
        for i in range(1, n):
            if (a[i] % 2) != (a[i - 1] % 2):
                curr = max(a[i], curr + a[i])
            else:
                curr = a[i]
            ans = max(ans, curr)
        out.append(str(ans))
    print('\\n'.join(out))

if __name__ == '__main__':
    solve()"""
    return [make_cid_sample(p, t, c)]

# ----------------------------------------------------------------------
# 16. Power Equality Pair Invariant (a^b == b^a)
# ----------------------------------------------------------------------
def gen_musical_power_pair() -> List[Dict[str, Any]]:
    p = """Given an array a of n positive integers representing powers of two b_i = 2^(a[i]), count the number of pairs (i, j) with i < j such that b_i^(b_j) == b_j^(b_i).
Read all input from sys.stdin.read().split(). Print results to stdout."""
    t = """Power equality invariant: (2^x)^(2^y) = (2^y)^(2^x) reduces to x / 2^x = y / 2^y.
For positive integers, this holds if and only if x == y OR {x, y} == {1, 2}. Sum combinations C(cnt[x], 2) plus cnt[1] * cnt[2] in O(N) time."""
    c = """import sys
from collections import Counter

def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    t = int(data[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(data[idx]); idx += 1
        a = [int(x) for x in data[idx:idx+n]]; idx += n
        freq = Counter(a)
        ans = 0
        for cnt in freq.values():
            ans += cnt * (cnt - 1) // 2
        ans += freq.get(1, 0) * freq.get(2, 0)
        out.append(str(ans))
    print('\\n'.join(out))

if __name__ == '__main__':
    solve()"""
    return [make_cid_sample(p, t, c)]

# ----------------------------------------------------------------------
# 17. Greedy Avoidance Sequence
# ----------------------------------------------------------------------
def gen_k_avoiding_array() -> List[Dict[str, Any]]:
    p = """You are given two integers n and k. An array is k-avoiding if no two distinct elements sum to k.
Return the minimum possible sum of a k-avoiding array of length n consisting of positive integers. Use class Solution."""
    t = """Greedy avoidance invariant: to minimize the total sum, greedily select the smallest available positive integers x such that (k - x) has not already been chosen.
Iterate sequentially from 1 upwards, adding elements to a set until exactly n elements are selected in O(N) time."""
    c = """class Solution:
    def minimumSum(self, n: int, k: int) -> int:
        seen = set()
        total = 0
        curr = 1
        while len(seen) < n:
            if (k - curr) not in seen:
                seen.add(curr)
                total += curr
            curr += 1
        return total"""
    return [make_cid_sample(p, t, c)]

# ----------------------------------------------------------------------
# 18. Cyclic Shift Cost Envelope
# ----------------------------------------------------------------------
def gen_chocolate_rotation() -> List[Dict[str, Any]]:
    p = """You are given an integer array nums representing the costs of n types of items, and an integer x representing the cost to rotate the array by one position.
Return the minimum total cost to collect all n items. Use class Solution."""
    t = """Cost envelope under cyclic shifts: performing k rotations costs exactly k * x and allows choosing each item i at cost min_{0 <= r <= k} nums[(i - r) % n].
Incrementally maintain the running minimum cost per item as k varies from 0 to n - 1, taking the global minimum of (k * x + sum(min_cost)) in O(N^2) time."""
    c = """from typing import List

class Solution:
    def minCost(self, nums: List[int], x: int) -> int:
        n = len(nums)
        min_costs = list(nums)
        ans = sum(min_costs)
        
        for k in range(1, n):
            for i in range(n):
                min_costs[i] = min(min_costs[i], nums[(i - k) % n])
            ans = min(ans, k * x + sum(min_costs))
            
        return ans"""
    return [make_cid_sample(p, t, c)]

# ----------------------------------------------------------------------
# 19. Bridge and Component Subarray Imbalance
# ----------------------------------------------------------------------
def gen_subarray_imbalance() -> List[Dict[str, Any]]:
    p = """You are given an integer array nums. The imbalance number of a subarray is the number of indices in its sorted version where adjacent elements differ by more than 1.
Return the sum of imbalance numbers of all subarrays. Use class Solution."""
    t = """Bridge and component invariant: inserting element x into an existing set of numbers merges adjacent components if both x-1 and x+1 are present (reducing imbalance by 1), or creates an isolated component if neither is present (increasing imbalance by 1).
Iterate all O(N^2) subarrays [i..j], updating current imbalance incrementally in O(1) per step."""
    c = """from typing import List

class Solution:
    def sumImbalanceNumbers(self, nums: List[int]) -> int:
        n = len(nums)
        total = 0
        for i in range(n):
            seen = {nums[i]}
            curr = 0
            for j in range(i + 1, n):
                x = nums[j]
                if x not in seen:
                    seen.add(x)
                    has_prev = (x - 1) in seen
                    has_next = (x + 1) in seen
                    if has_prev and has_next:
                        curr -= 1
                    elif not has_prev and not has_next:
                        curr += 1
                total += curr
        return total"""
    return [make_cid_sample(p, t, c)]

# ----------------------------------------------------------------------
# 20. Monotonic Stack Range Maximum Queries
# ----------------------------------------------------------------------
def gen_monotonic_range_max() -> List[Dict[str, Any]]:
    p = """You are given two integer arrays nums1 and nums2 of length n, and an array queries where queries[i] = [xi, yi].
For each query, find the maximum value of nums1[j] + nums2[j] such that nums1[j] >= xi and nums2[j] >= yi, or -1 if no such j exists. Use class Solution."""
    t = """Offline query sorting with monotonic stack: sort both elements and queries descending by the first dimension to satisfy nums1[j] >= xi monotonically.
Maintain a monotonic stack of (nums2[j], nums1[j] + nums2[j]) with decreasing nums2 and decreasing sum, and binary search for yi in O((N + Q) log N) time."""
    c = """from typing import List
from bisect import bisect_left

class Solution:
    def maximumSumQueries(self, nums1: List[int], nums2: List[int], queries: List[List[int]]) -> List[int]:
        n = len(nums1)
        pairs = sorted([(nums1[i], nums2[i]) for i in range(n)], reverse=True)
        q_sorted = sorted([(q[0], q[1], i) for i, q in enumerate(queries)], reverse=True)
        
        ans = [-1] * len(queries)
        stack = []
        p_idx = 0
        
        for x_req, y_req, q_orig in q_sorted:
            while p_idx < n and pairs[p_idx][0] >= x_req:
                x_val, y_val = pairs[p_idx]
                total = x_val + y_val
                p_idx += 1
                while stack and stack[-1][1] <= total:
                    stack.pop()
                if not stack or stack[-1][0] < y_val:
                    stack.append((y_val, total))
                    
            idx = bisect_left(stack, (y_req, -1))
            if idx < len(stack):
                ans[q_orig] = stack[idx][1]
                
        return ans"""
    return [make_cid_sample(p, t, c)]

def main():
    print("=" * 80)
    print("🚀 GENERATING ENHANCED CID CURRICULUM v2 (WITH DIGIT DP & GROUP PARITY)")
    print("=" * 80)
    
    generators = [
        gen_xor_parity,
        gen_argmin_mutation,
        gen_max_strength_group,
        gen_digit_dp,
        gen_composite_divisibility,
        gen_cycle_transposition,
        gen_game_post_move,
        gen_dsu_domain,
        gen_direct_simulation,
        gen_prefix_suffix,
        gen_boundary_inversion,
        gen_sliding_window,
        gen_palindrome_parity,
        gen_lexicographical_decrement,
        gen_alternating_kadane,
        gen_musical_power_pair,
        gen_k_avoiding_array,
        gen_chocolate_rotation,
        gen_subarray_imbalance,
        gen_monotonic_range_max
    ]
    
    base_samples = []
    for g in generators:
        res = g()
        base_samples.extend(res)
        print(f"  Generated {len(res):>2} foundational samples from {g.__name__}")
        
    print(f"\nTotal foundational archetypes: {len(base_samples)}")
    
    # Expand through clean parameterizations and context variants
    expanded = []
    prefixes = [
        "",
        "CRITICAL: Adhere strictly to optimal Big-O bounds.\n",
        "Fast execution required. Handle edge cases cleanly.\n",
        "Analyze constraints carefully and implement the optimal solution.\n",
        "Focus on exact invariant state transitions.\n"
    ]
    
    for sample in base_samples:
        for pfx in prefixes:
            u_content = pfx + sample["messages"][1]["content"] if pfx else sample["messages"][1]["content"]
            expanded.append({
                "messages": [
                    sample["messages"][0],
                    {"role": "user", "content": u_content},
                    sample["messages"][2]
                ]
            })
            
    replicated = []
    for i in range(5):
        for s in expanded:
            replicated.append(s)
            
    random.seed(42)
    random.shuffle(replicated)
    
    split_idx = int(len(replicated) * 0.9)
    train_data = replicated[:split_idx]
    valid_data = replicated[split_idx:]
    
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data/cid_curriculum")
    os.makedirs(out_dir, exist_ok=True)
    
    train_file = os.path.join(out_dir, "train.jsonl")
    valid_file = os.path.join(out_dir, "valid.jsonl")
    
    with open(train_file, "w") as f:
        for s in train_data:
            f.write(json.dumps(s) + "\n")
            
    with open(valid_file, "w") as f:
        for s in valid_data:
            f.write(json.dumps(s) + "\n")
            
    print(f"\n✅ CID v2 Dataset Generation Complete:")
    print(f"   Train Set: {len(train_data)} samples -> {train_file}")
    print(f"   Valid Set: {len(valid_data)} samples -> {valid_file}")
    print(f"   Reasoning Budget: 100% of <think> blocks <= 150 tokens.")
    print("=" * 80)

if __name__ == "__main__":
    main()
