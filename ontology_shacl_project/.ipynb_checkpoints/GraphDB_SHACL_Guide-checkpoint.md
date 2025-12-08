# SHACL Validation in GraphDB - Step-by-Step Guide

## Overview
GraphDB has built-in SHACL validation support. This guide shows you how to validate your GAO fraud ontology using GraphDB Desktop.

## Prerequisites
- GraphDB Desktop running (typically at http://localhost:7200)
- Your ontology already loaded in a repository
- SHACL shapes file (phase1_foundation_shapes.ttl)

---

## Method 1: Using GraphDB Workbench (GUI) - RECOMMENDED FOR BEGINNERS

### Step 1: Access Your Repository
1. Open GraphDB Workbench: http://localhost:7200
2. Select your repository from the repository list (e.g., "gao-fraud-ontology")

### Step 2: Import SHACL Shapes
1. Click **Import** in the left sidebar
2. Click **Upload RDF files**
3. Select your `phase1_foundation_shapes.ttl` file
4. **Important Settings:**
   - Named graph: Leave blank or use `http://example.org/shapes` (optional)
   - Base URI: Can leave default
   - Context: Default is fine
5. Click **Import**

The shapes are now loaded into your repository alongside your data.

### Step 3: Enable SHACL Validation
1. Click **Setup** in the left sidebar
2. Click **Repositories**
3. Find your repository and click **Edit**
4. Scroll down to **SHACL validation**
5. Set **Validation enabled** to **true**
6. Click **Save**

### Step 4: Run Validation
GraphDB validates automatically when enabled, but you can trigger it manually:

1. Go to **SPARQL** tab in the left sidebar
2. Run this query to see validation results:

```sparql
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?focusNode ?focusNodeLabel ?severity ?message ?path
WHERE {
    ?report a sh:ValidationReport ;
            sh:result ?result .
    
    ?result sh:focusNode ?focusNode ;
            sh:resultSeverity ?severity ;
            sh:resultMessage ?message .
    
    OPTIONAL { ?result sh:resultPath ?path }
    OPTIONAL { ?focusNode rdfs:label ?focusNodeLabel }
}
ORDER BY ?severity ?focusNode
LIMIT 100
```

### Step 5: Analyze Results

**Count issues by severity:**
```sparql
PREFIX sh: <http://www.w3.org/ns/shacl#>

SELECT ?severity (COUNT(?result) as ?count)
WHERE {
    ?report a sh:ValidationReport ;
            sh:result ?result .
    ?result sh:resultSeverity ?severity .
}
GROUP BY ?severity
ORDER BY ?severity
```

**Get violations only:**
```sparql
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?focusNode ?focusNodeLabel ?message ?path
WHERE {
    ?report a sh:ValidationReport ;
            sh:result ?result .
    
    ?result sh:focusNode ?focusNode ;
            sh:resultSeverity sh:Violation ;
            sh:resultMessage ?message .
    
    OPTIONAL { ?result sh:resultPath ?path }
    OPTIONAL { ?focusNode rdfs:label ?focusNodeLabel }
}
ORDER BY ?focusNode
```

**Count issues by class:**
```sparql
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?class (COUNT(?result) as ?issueCount)
WHERE {
    ?report a sh:ValidationReport ;
            sh:result ?result .
    
    ?result sh:focusNode ?focusNode .
    ?focusNode rdf:type ?class .
}
GROUP BY ?class
ORDER BY DESC(?issueCount)
```

### Step 6: Export Results
To export validation results to a file:

1. Run the validation query
2. Click **Download as** button above results
3. Choose format (CSV recommended for analysis)
4. Save file

---

## Method 2: Using SPARQL UPDATE (Advanced)

You can also run validation programmatically using SPARQL UPDATE:

### Load Shapes Programmatically
```sparql
# Insert shapes from file - GraphDB specific syntax
LOAD <file:///path/to/phase1_foundation_shapes.ttl>
```

### Trigger Validation via SPARQL
GraphDB validates automatically, but you can query the validation report at any time using the queries above.

---

## Method 3: Using GraphDB REST API (For Automation)

You can automate validation using GraphDB's REST API.

### Upload Shapes via cURL:
```bash
curl -X POST \
  http://localhost:7200/repositories/YOUR_REPO/statements \
  -H 'Content-Type: application/x-turtle' \
  -d @phase1_foundation_shapes.ttl
```

### Run Validation Query via cURL:
```bash
curl -X POST \
  http://localhost:7200/repositories/YOUR_REPO \
  -H 'Accept: application/sparql-results+json' \
  -H 'Content-Type: application/sparql-query' \
  -d 'PREFIX sh: <http://www.w3.org/ns/shacl#>
      SELECT * WHERE {
          ?report a sh:ValidationReport ;
                  sh:result ?result .
          ?result sh:focusNode ?focusNode ;
                  sh:resultMessage ?message .
      }'
```

---

## Useful SPARQL Queries for Analysis

### Get Summary Statistics
```sparql
PREFIX sh: <http://www.w3.org/ns/shacl#>

SELECT 
    (COUNT(DISTINCT ?result) as ?totalIssues)
    (COUNT(DISTINCT ?violation) as ?violations)
    (COUNT(DISTINCT ?warning) as ?warnings)
    (COUNT(DISTINCT ?info) as ?infoItems)
WHERE {
    ?report a sh:ValidationReport ;
            sh:result ?result .
    
    OPTIONAL {
        ?result sh:resultSeverity sh:Violation .
        BIND(?result as ?violation)
    }
    OPTIONAL {
        ?result sh:resultSeverity sh:Warning .
        BIND(?result as ?warning)
    }
    OPTIONAL {
        ?result sh:resultSeverity sh:Info .
        BIND(?result as ?info)
    }
}
```

### Find All Missing Labels
```sparql
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?focusNode ?focusNodeType
WHERE {
    ?report a sh:ValidationReport ;
            sh:result ?result .
    
    ?result sh:focusNode ?focusNode ;
            sh:resultPath rdfs:label ;
            sh:resultSeverity sh:Violation .
    
    ?focusNode a ?focusNodeType .
}
ORDER BY ?focusNodeType ?focusNode
```

### Get Detailed Report for One Instance
```sparql
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX gfo: <https://gaoinnovations.gov/antifraud_resource/howfraudworks/gfo/>

SELECT ?path ?severity ?message ?value
WHERE {
    ?report a sh:ValidationReport ;
            sh:result ?result .
    
    ?result sh:focusNode gfo:YourSpecificInstance ;
            sh:resultPath ?path ;
            sh:resultSeverity ?severity ;
            sh:resultMessage ?message .
    
    OPTIONAL { ?result sh:value ?value }
}
```

---

## Troubleshooting

### Problem: No validation results appear
**Solutions:**
1. Check that SHACL validation is enabled in repository settings
2. Verify shapes were imported correctly: Query for `?s a sh:NodeShape`
3. Try refreshing the repository or restarting GraphDB

### Problem: Too many results to view
**Solutions:**
1. Use LIMIT clause in queries: `LIMIT 100`
2. Export to CSV for analysis in Excel/Python
3. Filter by severity first (Violations only)

### Problem: Validation is slow
**Solutions:**
1. GraphDB validates on updates - consider disabling during bulk data loads
2. Use more specific shapes (target fewer classes at once)
3. Increase GraphDB memory allocation in settings

### Problem: Need to remove shapes
**To remove all shapes:**
```sparql
PREFIX sh: <http://www.w3.org/ns/shacl#>

DELETE {
    ?shape ?p ?o .
    ?s ?p2 ?shape .
}
WHERE {
    ?shape a sh:NodeShape .
    ?shape ?p ?o .
    OPTIONAL { ?s ?p2 ?shape }
}
```

---

## Best Practices

1. **Test shapes on small dataset first** - validate shapes work as expected
2. **Use named graphs for shapes** - easier to manage and remove
3. **Disable validation during bulk imports** - enable after data is loaded
4. **Export results regularly** - save validation reports for comparison
5. **Fix violations first** - then warnings, then info items
6. **Re-validate after fixes** - ensure changes resolve issues

---

## Integration with Your Workflow

### Option A: Keep Shapes in Repository
- Shapes stay with your data
- Validation happens automatically
- Good for ongoing data quality

### Option B: Load Shapes Temporarily
- Load shapes for validation
- Run validation queries
- Remove shapes when done
- Good for periodic checks

### Option C: Separate Validation Repository
- Create dedicated validation repository
- Copy data for validation
- Keep production clean
- Good for testing new shapes

---

## Next Steps After Phase 1

Once Phase 1 foundation classes are clean:

1. Create Phase 2 shapes for content resources:
   - FederalFraudScheme
   - FraudEducation
   - FraudPreventionAndDetectionGuidance

2. Create Phase 3 shapes for supporting data:
   - FraudRiskManagementPrinciples
   - GAOReport
   - Other resource types

3. Add relationship validation:
   - Check `involves` relationships are valid
   - Verify `addresses` links to appropriate classes
   - Validate property chains

---

## Comparison: GraphDB vs Python

### GraphDB Pros:
- ✓ Built-in, no additional libraries
- ✓ Automatic validation on data changes
- ✓ Visual query interface
- ✓ Good for interactive exploration

### GraphDB Cons:
- ✗ Less control over reporting format
- ✗ Harder to automate in pipelines
- ✗ Query-based analysis can be tedious

### Python/pyshacl Pros:
- ✓ Rich reporting and visualization
- ✓ Easy to automate
- ✓ Integration with pandas for analysis
- ✓ Version control friendly

### Python/pyshacl Cons:
- ✗ Requires Python environment
- ✗ Manual execution needed
- ✗ Not integrated with data updates

**Recommendation:** Use GraphDB for quick checks and interactive work, Python for detailed analysis and automation.
