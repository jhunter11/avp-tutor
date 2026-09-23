# Binary search

## Sorted input and shrinking interval
Binary search requires data sorted according to the comparison order. Compare target to the middle element, then discard the half that cannot contain the target. The invariant is that any remaining target occurrence lies within the current search interval. On unsorted input this elimination is not justified. Only name current low, high, mid, and target values when supplied by the visualizer.

## Boundaries and duplicates
In an inclusive [low, high] variant, use low = mid + 1 when target is larger, high = mid - 1 when smaller, and stop when low > high. Half-open variants use different updates; follow the submitted code. A basic binary search may return any matching duplicate, not necessarily the first. Floor/rounding behavior of midpoint computation must be verified against the actual AVP runtime.

## Time and space complexity
Each comparison approximately halves the remaining candidate interval, giving O(log n) comparisons. An iterative version uses O(1) auxiliary storage. These claims assume random access to sorted data; sorting unsorted input adds its own cost.
