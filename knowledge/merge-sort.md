# Merge sort

## Divide and merge
Split the input into smaller ranges, sort each range recursively, then merge two sorted ranges by choosing the smaller front value. During a merge, the output prefix is sorted and consists of the smallest elements consumed so far. A recursive call returning does not imply all other ranges have finished.

## Complexity and stability
A standard array merge sort takes Theta(n log n) time and O(n) auxiliary array storage, plus recursive call frames. Taking the left item first on ties preserves stability. Exact intermediate buffers and indices depend on the implementation and must come from the execution state.
