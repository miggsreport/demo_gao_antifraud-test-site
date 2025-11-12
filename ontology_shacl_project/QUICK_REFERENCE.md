# SHACL Validation Toolkit - Quick Reference Card

## 🎯 What You Have

Complete SHACL validation system for GAO fraud ontology - ready to use!

**Package:** `shacl_validation_package.tar.gz` (18 KB)
**Location:** `/home/claude/`

---

## 📦 9 Files Created

### Core Tools (4)
1. `phase1_foundation_shapes.ttl` - Validation rules
2. `validate_ontology.py` - Python validator
3. `shacl_validation.ipynb` - Jupyter notebook
4. `test_validation_setup.py` - Setup tester

### Documentation (4)
5. `README_SHACL_Validation.md` - Main guide
6. `GraphDB_SHACL_Guide.md` - GraphDB setup
7. `DEPLOYMENT_GUIDE.md` - Installation
8. `PACKAGE_SUMMARY.md` - Overview

### Utilities (1)
9. `quick_start_validation.sh` - Quick start script

---

## ⚡ 30-Second Quick Start

```bash
# 1. Install
pip install pyshacl rdflib pandas --break-system-packages

# 2. Test
python test_validation_setup.py

# 3. Validate
python validate_ontology.py --data YOUR_DATA.ttl --shapes phase1_foundation_shapes.ttl
```

---

## 🎓 Choose Your Method

### Python (Recommended for Reports)
```bash
python validate_ontology.py --data gfo_turtle.ttl --shapes phase1_foundation_shapes.ttl
```
**Output:** CSV reports, JSON summary, console statistics

### Jupyter (Recommended for Exploration)
```bash
jupyter notebook shacl_validation.ipynb
```
**Output:** Interactive analysis, visual filtering, exports

### GraphDB (Recommended for Quick Checks)
See: `GraphDB_SHACL_Guide.md`
**Output:** SPARQL queries, visual interface, auto-validation

---

## 📊 What's Validated (Phase 1)

| Class | Instance Count | Rules |
|-------|---------------|-------|
| FraudActivity | 35+ | Label, definition |
| FederalAgency | Many | Label, relationships |
| FederalUnit | Many | Label, isPartOf |
| ProgramArea | Many | Label, prefLabel |
| FundingStream | Many | Label hierarchy |
| RevenueStream | Many | Label hierarchy |

**Total Validation Points:** ~20 rules across 3 severity levels

---

## 🚦 Severity Levels

🔴 **Violation** - MUST FIX  
⚠️ **Warning** - SHOULD FIX  
ℹ️ **Info** - NICE TO HAVE

---

## 📁 Output Files

After validation, find in `validation_reports/`:

```
validation_reports/
├── validation_results_TIMESTAMP.csv        # All issues
├── validation_violations_TIMESTAMP.csv     # Critical only
├── validation_warnings_TIMESTAMP.csv       # Warnings only
├── validation_summary_TIMESTAMP.json       # Statistics
└── validation_report_TIMESTAMP.ttl         # RDF report
```

---

## 🔄 Workflow

1. **Validate** → Get baseline
2. **Export** → Violations to CSV
3. **Fix** → In Protégé/VocBench
4. **Re-validate** → Confirm fixes
5. **Repeat** → Until clean

---

## 💡 First Time Tips

✓ Expect 50-200+ issues first time (normal!)
✓ Fix violations first, then warnings
✓ Work on one class at a time
✓ Use CSV exports for batch fixes
✓ Re-validate frequently
✓ Track progress with timestamps

---

## 🆘 Quick Troubleshooting

**Can't find pyshacl?**
```bash
pip install pyshacl rdflib pandas --break-system-packages
```

**File not found?**
Use absolute paths: `/home/claude/file.ttl`

**Too many errors?**
Normal! Start with one class at a time

**Slow validation?**
Use: `--inference none`

---

## 📞 Next Steps

1. Read: `README_SHACL_Validation.md`
2. Pick: Python OR GraphDB OR Jupyter
3. Test: `python test_validation_setup.py`
4. Run: First validation on real data
5. Fix: Start with violations
6. Win: Clean foundation classes!

---

## 📚 Documentation Map

**New to SHACL?**
→ Start with `README_SHACL_Validation.md`

**Using GraphDB?**
→ Read `GraphDB_SHACL_Guide.md`

**Installing?**
→ See `DEPLOYMENT_GUIDE.md`

**Quick overview?**
→ Read `PACKAGE_SUMMARY.md`

**Need examples?**
→ Open `shacl_validation.ipynb`

---

## ✅ Success Checklist

Phase 1 Complete When:
- [ ] Zero violations for FraudActivity
- [ ] Zero violations for FederalAgency
- [ ] Zero violations for FederalUnit
- [ ] Zero violations for ProgramArea
- [ ] Zero violations for FundingStream
- [ ] Zero violations for RevenueStream

**Then:** Create Phase 2 shapes for content classes!

---

## 🎉 You're Ready!

All files created. All documentation written. All methods supported.

**Choose your approach and start validating!**

Questions? Check the docs. Issues? See troubleshooting.

**Good luck! 🚀**

---

*Package created: November 11, 2025*
*Total size: ~65 KB source + 18 KB compressed*
*Python 3.7+ required for script methods*
*GraphDB Desktop required for GraphDB method*
