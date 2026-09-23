# Bubble sort

## Adjacent comparisons and invariant
Compare neighboring elements and swap when they are out of order. In a left-to-right ascending pass, the largest element in the unsorted region reaches its right boundary. After each completed pass, that suffix is settled. Intermediate comparisons do not mean the entire array is sorted.

## Complexity and early exit
Standard bubble sort takes O(n^2) time and O(1) extra storage. A swap flag enables early exit after a complete pass with no swaps, making already sorted input O(n). Without that optimization, do not claim linear best-case time. Swapping only strictly out-of-order neighbors preserves stability.
