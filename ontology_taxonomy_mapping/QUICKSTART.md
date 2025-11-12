# Quick Start Guide - Fraud Scheme Taxonomy Mapper

##  What You Need

1. Your GFO ontology file (gfo_turtle.ttl)
2. The GAO Product Taxonomy file (.ttl format)
3. Python 3.8+ installed

##  Quick Setup (5 minutes)

### Step 1: Install Dependencies

**Option A - Full installation (recommended for best results):**
```bash
pip install -r requirements.txt
```

**Option B - Lightweight (if you encounter issues):**
```bash
pip install rdflib pandas numpy
```

### Step 2: Update File Paths

Open `fraud_scheme_taxonomy_mapper.py` and update these lines (around line 423):

```python
GFO_ONTOLOGY_PATH = "path/to/your/gfo_turtle.ttl"
TAXONOMY_PATH = "path/to/your/gao_product_taxonomy.ttl"
```

### Step 3: Run

```bash
python fraud_scheme_taxonomy_mapper.py
```

##  What You'll Get

Three CSV files will be created in the `outputs` folder:

1. **federal_fraud_schemes_[timestamp].csv**
   - All fraud schemes from your ontology
   - Use this as your source data

2. **fraud_scheme_taxonomy_mappings_[timestamp].csv**  **MAIN FILE**
   - Each fraud scheme with top 5 suggested taxonomy matches
   - Includes confidence scores
   - Ready for manual review

3. **mapping_summary_[timestamp].csv**
   - Quick overview by scheme
   - Good for initial assessment

##  Reviewing Results

1. Open the **fraud_scheme_taxonomy_mappings** CSV in Excel
2. Sort by `confidence_score` (high to low)
3. Review matches where `confidence_score` >= 0.30
4. Look for patterns to inform your rule-based matching

### Confidence Score Guide:
- **0.50+**: Strong match - likely correct 
- **0.30-0.50**: Good match - verify 
- **0.15-0.30**: Possible match - review carefully 
- **<0.15**: Weak - filtered out by default 

##  Adjusting Settings

### Want More Matches Per Scheme?
Change this line in the script:
```python
top_n=10,  # instead of 5
```

### Want Only High-Confidence Matches?
Change this line:
```python
min_score=0.30,  # instead of 0.15
```

### Want Faster Processing?
Use keyword matching instead of semantic:
```python
matcher = SemanticMatcher(use_transformers=False)
```

##  Troubleshooting

**"Cannot find gfo_turtle.ttl"**
- Make sure the file path is correct
- Use absolute path if needed: `/full/path/to/gfo_turtle.ttl`

**"No matches found"**
- Lower the `min_score` to 0.10
- Increase `top_n` to 10
- Check that taxonomy file loaded correctly

**Script is slow**
- First run downloads model (~80MB) - one time only
- Subsequent runs are much faster

**ModuleNotFoundError**
- Run: `pip install -r requirements.txt`
- Or install missing package: `pip install [package-name]`

##  Next Steps

1. Review the suggested mappings
2. Identify patterns in high-confidence matches
3. Document these as rules for future automated tagging
4. Test rules on a subset of schemes
5. Iterate!

##  Tips

- Start with high confidence threshold (0.30) to focus on best matches
- The broader_term_label shows SKOS hierarchy - use this for context
- Compare match_rank 1 and 2 for each scheme - sometimes both are valid
- Export filtered results: `df[df['confidence_score'] >= 0.40].to_csv('high_confidence.csv')`

---

**Need Help?** See the full README.md for detailed documentation.
