# Selection sort

## Minimum selection
Scan the unsorted suffix to find its minimum, then place it at the next position in the sorted prefix. A changing minimum index during the scan is not itself a swap. After each outer pass, the prefix contains the smallest processed values in final sorted positions.

## Complexity and stability
The standard implementation performs Theta(n^2) comparisons even on sorted input and uses O(1) extra storage. It performs O(n) swaps. The usual distant-swap version is not stable; equal values can change relative order.
