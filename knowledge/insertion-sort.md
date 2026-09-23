# Insertion sort

## Saved key and shifting
Insertion sort saves collection[i] in key before shifting larger elements right. The assignment collection[j + 1] = collection[j] copies a value; it is not a swap. The array may temporarily contain duplicates and appear to lose key, but key remains in a separate variable. After shifting, collection[j + 1] = key fills the insertion position. Refer to the supplied snapshot to name actual values. In the demo, highlighted statements have already executed.

## Sorted prefix invariant
At the start of outer iteration i, indices 0 through i-1 form a sorted prefix containing those processed elements. During shifting, key is held separately and there is a conceptual hole, so do not claim the entire prefix remains a permutation of its original values at every intermediate assignment. After insertion, indices 0 through i are sorted. Repeat until the prefix covers the array.

## Stability and boundaries
Shifting only when collection[j] > key leaves equal elements in their original relative order: this implementation is stable. Using >= can change stability. Stop at j < 0 or when the left value is no larger than key. The demo checks j >= 0 before array access. Empty and single-element arrays need no insertions; duplicates and negative numbers are valid.

## Time and space complexity
For this in-place insertion-sort implementation, already sorted input takes Theta(n) comparisons because each inner scan stops immediately. Reverse-sorted input causes 1+2+...+(n-1) shifts, giving Theta(n^2) time. Average time is Theta(n^2) under the usual random-permutation assumption. Extra algorithm storage is O(1); the visualizer's stored snapshots use additional memory and are not part of that algorithm-space claim.
