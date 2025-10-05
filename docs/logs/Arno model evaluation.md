Arno model evaluation - 03/10/2025

- GNN
  - The model performance better on shorter names than longer names. When the model is right, it usually outputs shorter names and when it is wrong it is usually when the expected output was longer.
  - Model focusses more on single word prediction, while ground truth are made of identifiers with more than one name
  - precision = 30 precent. So meaning that it is rather spread.
    - Precision > recall: when it predicts, it’s sometimes right, but it misses a lot of correct identifiers.
  - Edit distance is long (6) meaning we need 6 edits to find the ground truth

- Refbert
  - The model has 37.6 percent correctness on ordered predictions. Meaning the order of keywords compared to the ground truth is correct
  - the model unoredered is the same as ordered. Meaning most identifiers are single token ones.
    - this could all imply that the model performs well on single order ones and not on other.
  - For identifier naming, F1 ≈ 0.42 is quite solid, especially if names are short and ambiguous.
  - Equaly precise and complete, meaning a balanced predictor. Still rather spread.
  - So a CER = 77% means that, on average, 77% of characters must be changed (added/removed/substituted) to get from the prediction to the target.
  - On average, you need ~5 edits to turn each predicted name into the gold one.

| Metric                      | **GNN model (TensorFlow)** | **REFBERT (PyTorch)** | **Δ (Improvement)** |
| --------------------------- | -------------------------- | --------------------- | ------------------- |
| **Correct ordered**         | 0.213                      | **0.376**             | **+76%**            |
| **Correct unordered**       | 0.213                      | **0.376**             | **+76%**            |
| **Precision**               | 0.303                      | **0.423**             | **+39%**            |
| **Recall**                  | 0.266                      | **0.419**             | **+57%**            |
| **F1**                      | 0.276                      | **0.418**             | **+51%**            |
| **CER (%)**                 | 93.6                       | **77.1**              | **−17% (better)**   |
| **Edit distance**           | 5.80                       | **4.74**              | **−18% (better)**   |
| **Avg predicted subtokens** | 1.16                       | _(not reported)_      | —                   |
| **Avg expected subtokens**  | 1.47                       | _(not reported)_      | —                   |

Overall Refbert performs better
