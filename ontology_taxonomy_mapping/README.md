# Federal Fraud Scheme to GAO Product Taxonomy Mapper

## Overview

This tool maps Federal Fraud Scheme instances from the GAO Fraud Ontology (GFO) to terms in the GAO Product Taxonomy using semantic similarity matching. It's designed to facilitate the semi-automated tagging of fraud schemes with appropriate taxonomy terms for improved searchability and organization.

## What It Does

1. **Exports Federal Fraud Schemes**: Extracts all `FederalFraudScheme` instances from the GFO ontology into both CSV and TTL formats

2. **Loads GAO Product Taxonomy**: Parses the SKOS-based GAO Product Taxonomy and extracts all concepts with their metadata

3. **Semantic Matching**: Uses sentence transformers (or fallback keyword matching) to find the most relevant taxonomy terms for each fraud scheme

4. **Outputs Mappings**: Generates CSV files with suggested mappings ranked by confidence score for manual review

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

**Note**: If you encounter issues with `sentence-transformers` or `torch`, the script will automatically fall back to basic keyword matching. For best results, we recommend installing the full dependencies.

### Quick Install (Lightweight)
If you want to skip the transformer models:
```bash
pip install rdflib pandas numpy
```

## Usage

### Basic Usage

1. **Prepare your files**:
   - Place your GFO ontology file (TTL format) in the working directory
   - Have your GAO Product Taxonomy file accessible

2. **Update file paths** in the script:
   ```python
   GFO_ONTOLOGY_PATH = "path/to/gfo_turtle.ttl"
   TAXONOMY_PATH = "path/to/gao_product_taxonomy.ttl"
   ```

3. **Run the script**:
   ```bash
   python fraud_scheme_taxonomy_mapper.py
   ```

### Configuration Options

You can adjust these parameters in the `main()` function:

```python
matcher.find_matches(
    fraud_schemes_df, 
    taxonomy_df,
    top_n=5,           # Number of matches per scheme (1-10 recommended)
    min_score=0.15     # Minimum confidence (0.0-1.0)
)
```

**Recommended settings by use case**:

- **High Precision** (fewer, more confident matches):
  - `top_n=3`
  - `min_score=0.30`

- **High Recall** (more matches to review):
  - `top_n=10`
  - `min_score=0.10`

- **Balanced** (default):
  - `top_n=5`
  - `min_score=0.15`

## Output Files

The script generates several output files with timestamps:

### 1. `federal_fraud_schemes_YYYYMMDD_HHMMSS.csv`
Contains all fraud scheme data extracted from the ontology:
- `gfo_uri`: The fraud scheme's URI
- `rdfs_label`: The scheme's label
- `dc_description`: Description
- `gfo_fraudNarrative`: Detailed narrative
- `fraud_activity_uri`: Associated fraud activity class URI
- `fraud_activity_label`: Associated fraud activity label

### 2. `federal_fraud_schemes_YYYYMMDD_HHMMSS.ttl`
TTL export of just the federal fraud scheme data for further processing or import

### 3. `fraud_scheme_taxonomy_mappings_YYYYMMDD_HHMMSS.csv`
**Main output file** with suggested mappings:

**Fraud Scheme Columns**:
- `scheme_uri`: GFO URI
- `scheme_label`: rdfs:label
- `scheme_description`: dc:description
- `scheme_narrative`: gfo:fraudNarrative
- `fraud_activity`: Related fraud activity type

**Taxonomy Columns**:
- `taxonomy_uri`: Matched taxonomy concept URI
- `taxonomy_prefLabel`: skos:prefLabel
- `taxonomy_topConceptOf`: skos:topConceptOf
- `taxonomy_genericId`: Generic ID from taxonomy
- `broader_term_uri`: URI of broader term (BT)
- `broader_term_label`: Label of broader term

**Match Quality Metrics**:
- `match_rank`: Ranking (1 = best match)
- `confidence_score`: 0.0-1.0 (higher = better)
- `matching_method`: Method used for matching

### 4. `mapping_summary_YYYYMMDD_HHMMSS.csv`
Summary view grouped by fraud scheme showing top matches

## Interpreting Results

### Confidence Scores

- **0.50+**: Very strong match - likely correct
- **0.30-0.50**: Good match - review recommended
- **0.15-0.30**: Possible match - manual review needed
- **<0.15**: Weak match - filtered out by default

### Recommended Workflow

1. **Sort by confidence score** (highest first)
2. **Review top matches** (rank 1) for each scheme
3. **Validate semantically**: Does the taxonomy term accurately describe the fraud scheme?
4. **Check broader terms**: Are the BT relationships appropriate?
5. **Flag for rules**: Document patterns in high-confidence matches for rule-based tagging

### Example Interpretation

```csv
scheme_label,taxonomy_prefLabel,confidence_score,broader_term_label,match_rank
"Healthcare billing fraud","healthcare fraud",0.87,"fraud",1
"Healthcare billing fraud","medical billing",0.54,"healthcare",2
```

**Analysis**: 
- First match (0.87) is very strong and semantically correct
- Second match (0.54) is also relevant but less specific
- Broader term "fraud" confirms this is in the fraud taxonomy section

## Advanced Usage

### Filtering Results

Post-process the mappings CSV to focus on specific subsets:

```python
import pandas as pd

# Load mappings
df = pd.read_csv('fraud_scheme_taxonomy_mappings_20250127_123456.csv')

# Keep only top match per scheme
top_matches = df[df['match_rank'] == 1]

# Filter by confidence
high_confidence = df[df['confidence_score'] >= 0.30]

# Filter by fraud activity type
healthcare_schemes = df[df['fraud_activity'].str.contains('healthcare', case=False)]
```

### Customizing the Matching Logic

To adjust how matching works, modify the `SemanticMatcher` class:

```python
def calculate_similarity(self, text1: str, text2: str) -> float:
    # Add custom logic here
    # Example: Boost scores for exact keyword matches
    if any(word in text2 for word in ['fraud', 'billing', 'claim']):
        base_score = self.calculate_similarity(text1, text2)
        return min(1.0, base_score * 1.2)  # 20% boost
```

## Developing Rule-Based Matching

Use the results from this script to inform rule development:

1. **Analyze high-confidence matches**: Look for patterns
   - What keywords appear consistently?
   - Are certain fraud activities always mapped to certain taxonomy terms?

2. **Create rules**: Document as if-then logic
   ```
   IF scheme contains "healthcare" AND "billing" 
   THEN tag with "healthcare fraud" AND "medical billing"
   ```

3. **Test rules**: Apply to a subset and compare with semantic matches

4. **Iterate**: Refine rules based on discrepancies

## Troubleshooting

### "Cannot find module 'sentence_transformers'"
The script will automatically fall back to keyword matching. For better results, install:
```bash
pip install sentence-transformers
```

### "Memory error when encoding"
Reduce batch size or use keyword matching mode:
```python
matcher = SemanticMatcher(use_transformers=False)
```

### "No matches found above threshold"
- Lower `min_score` parameter
- Increase `top_n` parameter
- Check that taxonomy file loaded correctly

### Script is very slow
- First run downloads the transformer model (~80MB) - this is one-time
- Subsequent runs are much faster
- For large datasets, consider processing in batches

## Technical Details

### Matching Algorithm

**With sentence-transformers** (recommended):
1. Encodes all taxonomy terms into 384-dimensional semantic vectors
2. For each fraud scheme, creates a semantic vector from combined text
3. Calculates cosine similarity between scheme and all taxonomy vectors
4. Returns top N matches above threshold

**Without sentence-transformers** (fallback):
1. Tokenizes text into word sets
2. Calculates Jaccard similarity (intersection/union)
3. Returns matches based on keyword overlap

### Text Fields Used for Matching

**Fraud Schemes**:
- rdfs:label
- dc:description  
- gfo:fraudNarrative
- fraud activity label

**Taxonomy Terms**:
- skos:prefLabel
- broader term labels

### Performance

Typical performance on a modern laptop:
- 100 fraud schemes × 1,000 taxonomy terms
- With transformers: ~2-3 minutes (first run), ~30 seconds (subsequent)
- Without transformers: ~10-15 seconds

## Future Enhancements

Potential improvements to consider:

1. **Multi-language support**: Handle non-English terms
2. **Weighting**: Give more importance to certain fields (e.g., descriptions > narratives)
3. **Negative keywords**: Exclude matches based on certain terms
4. **Hierarchical matching**: Consider taxonomy hierarchy in scoring
5. **Interactive mode**: Review and approve matches in real-time
6. **API integration**: Pull live data from VocBench or GraphDB

## Contact & Support

For questions or issues with this script, contact the GAO Antifraud Resource team.

## License

This script is developed for internal use by the U.S. Government Accountability Office.
