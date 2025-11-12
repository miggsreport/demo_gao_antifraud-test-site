# GAO Fraud Ontology - SHACL Validation Setup

Complete setup for validating your GAO fraud ontology instance data using SHACL (Shapes Constraint Language).

## 📁 Files Created

### Core Files
- **`phase1_foundation_shapes.ttl`** - SHACL shapes for Phase 1 (foundation classes)
- **`validate_ontology.py`** - Python validation script with detailed reporting
- **`shacl_validation.ipynb`** - Jupyter notebook for interactive validation
- **`GraphDB_SHACL_Guide.md`** - Complete guide for GraphDB validation
- **`quick_start_validation.sh`** - Quick start script

### What You Need
- **Your ontology file** (e.g., `gfo_turtle.ttl`)
- **Python 3.7+** with pip installed
- **OR** GraphDB Desktop running

---

## 🚀 Quick Start - Three Options

### Option 1: Command Line (Fastest)

```bash
# Install dependencies
pip install pyshacl rdflib pandas

# Run validation
python validate_ontology.py \
    --data /path/to/gfo_turtle.ttl \
    --shapes phase1_foundation_shapes.ttl \
    --output-dir validation_reports
```

### Option 2: Jupyter Notebook (Interactive)

```bash
# Start Jupyter
jupyter notebook shacl_validation.ipynb

# Follow the notebook instructions
# Update file paths in the configuration cell
# Run all cells
```

### Option 3: GraphDB (Visual)

See **`GraphDB_SHACL_Guide.md`** for complete instructions.

Quick steps:
1. Open GraphDB Workbench (http://localhost:7200)
2. Import `phase1_foundation_shapes.ttl`
3. Enable SHACL validation in repository settings
4. Run validation queries

---

## 📋 Phase 1: Foundation Classes

This initial validation covers the core reference classes that everything else depends on:

✓ **FraudActivity** (35+ fraud types like BeneficiaryFraud, TaxFraud, etc.)  
✓ **FederalAgency** (government agencies)  
✓ **FederalUnit** (sub-organizations)  
✓ **ProgramArea** (program categories)  
✓ **FundingStream** (funding types)  
✓ **RevenueStream** (revenue types)

### What's Validated

**VIOLATIONS (Must Fix):**
- Every instance must have an rdfs:label
- Labels must be proper literals

**WARNINGS (Should Fix):**
- Relationships should point to valid URIs
- Related entities should exist

**INFO (Nice to Have):**
- Preferred labels (skos:prefLabel)
- Definitions (skos:definition)
- Website URIs format

---

## 💻 Docker/Jupyter Setup

### Prerequisites
```bash
# In your Docker container or local environment
pip install pyshacl rdflib pandas
```

### Running in Jupyter

1. **Upload files to Jupyter:**
   - `shacl_validation.ipynb`
   - `validate_ontology.py`
   - `phase1_foundation_shapes.ttl`
   - Your ontology file (`gfo_turtle.ttl`)

2. **Open the notebook:**
   ```
   http://localhost:8888 → shacl_validation.ipynb
   ```

3. **Update file paths** in the configuration cell

4. **Run all cells** to see results

### Running from Command Line

```bash
# Navigate to your work directory
cd /home/claude

# Run validation
python validate_ontology.py \
    --data gfo_turtle.ttl \
    --shapes phase1_foundation_shapes.ttl \
    --inference none
```

---

## 🔍 Understanding Results

### Console Output
```
=================================================
SHACL VALIDATION SUMMARY REPORT
=================================================
Overall conforms: ✗ NO
Total issues found: 147

Issues by Severity:
  🔴 Violation: 52
  ⚠️ Warning: 73
  ℹ️ Info: 22

Top Properties with Issues:
  label: 52
  isPartOf: 31
  hasWebsite: 22
```

### Saved Reports

All reports are saved to `validation_reports/` directory:

1. **`validation_results_TIMESTAMP.csv`** - Complete results
2. **`validation_violations_TIMESTAMP.csv`** - Only violations
3. **`validation_warnings_TIMESTAMP.csv`** - Only warnings
4. **`validation_summary_TIMESTAMP.json`** - Summary statistics
5. **`validation_report_TIMESTAMP.ttl`** - RDF validation report

### CSV Format

| focus_node | focus_node_label | result_path | severity | message | value |
|------------|------------------|-------------|----------|---------|-------|
| gfo:TaxFraud | Tax Fraud | label | Violation | Must have label | N/A |

---

## 🔧 Fixing Issues

### Workflow

1. **Start with Violations** - These are critical
2. **Review the CSV files** - Sort by class or property
3. **Fix in your ontology** - Add missing labels, fix relationships
4. **Re-validate** - Run validation again
5. **Move to Warnings** - Once violations are clean
6. **Finally Info items** - Nice to have improvements

### Common Fixes

**Missing Labels:**
```turtle
gfo:TaxFraud rdfs:label "Tax Fraud"@en .
```

**Invalid Relationships:**
```turtle
# Before (broken)
gfo:SomeUnit gfo:isPartOf "Department of Justice" .

# After (fixed)
gfo:SomeUnit gfo:isPartOf gfo:DepartmentOfJustice .
```

**Website URIs:**
```turtle
gfo:SomeAgency gfo:hasWebsite <https://example.gov> .
```

---

## 📊 Comparing Environments

### When to Use Python/Jupyter

✓ Detailed analysis and reporting  
✓ Batch processing multiple files  
✓ Automated pipelines  
✓ Exporting results to CSV/Excel  
✓ Integration with pandas

### When to Use GraphDB

✓ Quick interactive checks  
✓ Exploring relationships visually  
✓ Automatic validation on updates  
✓ SPARQL-based analysis  
✓ Real-time validation

### Recommendation

**Use both!**
- **GraphDB** for quick checks during ontology editing
- **Python** for detailed reports and systematic cleanup

---

## 🎯 Next Steps

### After Phase 1 is Clean

1. **Create Phase 2 shapes** for content resources:
   - FederalFraudScheme
   - FraudEducation  
   - FraudPreventionAndDetectionGuidance

2. **Create Phase 3 shapes** for supporting data:
   - FraudRiskManagementPrinciples
   - GAOReport instances

3. **Add relationship validation:**
   - Validate `involves` relationships
   - Check `addresses` properties
   - Verify property chains

### Progressive Shape Development

Start simple, add complexity as you clean data:

```turtle
# Version 1: Just check existence
sh:property [
    sh:path rdfs:label ;
    sh:minCount 1 ;
] ;

# Version 2: Add datatype
sh:property [
    sh:path rdfs:label ;
    sh:minCount 1 ;
    sh:datatype xsd:string ;
] ;

# Version 3: Add patterns
sh:property [
    sh:path rdfs:label ;
    sh:minCount 1 ;
    sh:datatype xsd:string ;
    sh:pattern "^[A-Z]" ;  # Must start with capital
] ;
```

---

## 🆘 Troubleshooting

### "Module not found: pyshacl"
```bash
pip install pyshacl rdflib pandas
```

### "File not found" errors
Check file paths in your configuration. Use absolute paths if needed:
```python
DATA_FILE = "/home/claude/gfo_turtle.ttl"
```

### Validation is very slow
- Start with `inference='none'`
- Add inference only if needed for complex property chains
- Consider validating subsets of data

### Too many errors to handle
This is expected! That's why we do incremental validation:
1. Fix one class at a time
2. Start with just Violations
3. Use CSV exports to batch-fix similar issues

### GraphDB not showing validation results
1. Check SHACL validation is enabled in repository settings
2. Verify shapes imported correctly: Query for `?s a sh:NodeShape`
3. Try manual validation query from the GraphDB guide

---

## 📚 Additional Resources

- **SHACL Specification:** https://www.w3.org/TR/shacl/
- **pyshacl Documentation:** https://github.com/RDFLib/pySHACL
- **GraphDB SHACL Guide:** https://graphdb.ontotext.com/documentation/enterprise/shacl-validation.html

---

## 💡 Tips

1. **Version control your shapes** - Track what you're validating over time
2. **Document your validation strategy** - Note what you've cleaned
3. **Automate in CI/CD** - Run validation on ontology updates
4. **Share results with team** - Use CSV exports for collaboration
5. **Celebrate wins** - Each clean class is progress!

---

## 🤝 Support

If you run into issues:
1. Check the troubleshooting section
2. Review the GraphDB guide for GraphDB-specific issues
3. Check pyshacl GitHub issues for Python-specific problems
4. Review your shapes syntax if validation seems wrong

---

## ✅ Success Criteria

You'll know Phase 1 is complete when:
- [ ] All Violation-level issues are fixed
- [ ] Warning-level issues are reviewed and addressed
- [ ] You have clean validation reports for all foundation classes
- [ ] You're ready to move to Phase 2 content validation

Good luck! 🚀
