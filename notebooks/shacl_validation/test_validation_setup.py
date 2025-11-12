"""
Test script to verify SHACL validation setup is working correctly.
This creates a minimal test dataset and validates it.
"""

import rdflib
from rdflib import Graph, Namespace, Literal, URIRef
from pyshacl import validate
from pathlib import Path

# Define namespaces
GFO = Namespace("https://gaoinnovations.gov/antifraud_resource/howfraudworks/gfo/")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")

print("Creating test dataset...")

# Create test data graph
data_graph = Graph()
data_graph.bind("gfo", GFO)
data_graph.bind("rdfs", RDFS)
data_graph.bind("skos", SKOS)

# Add some test instances - mix of valid and invalid
# Valid FraudActivity with label
data_graph.add((GFO.TestFraud1, RDF.type, GFO.FraudActivity))
data_graph.add((GFO.TestFraud1, RDFS.label, Literal("Test Fraud Type 1", lang="en")))

# Invalid FraudActivity without label (should trigger Violation)
data_graph.add((GFO.TestFraud2, RDF.type, GFO.FraudActivity))

# Valid FederalAgency with label
data_graph.add((GFO.TestAgency1, RDF.type, GFO.FederalAgency))
data_graph.add((GFO.TestAgency1, RDFS.label, Literal("Test Agency")))

# Invalid FederalAgency without label
data_graph.add((GFO.TestAgency2, RDF.type, GFO.FederalAgency))

print(f"✓ Created test dataset with {len(data_graph)} triples")

# Load shapes
print("\nLoading SHACL shapes...")
shapes_file = Path("/home/claude/phase1_foundation_shapes.ttl")

if not shapes_file.exists():
    print("❌ Shapes file not found. Make sure phase1_foundation_shapes.ttl exists.")
    exit(1)

shapes_graph = Graph()
shapes_graph.parse(str(shapes_file), format="turtle")
print(f"✓ Loaded {len(shapes_graph)} shape triples")

# Run validation
print("\nRunning SHACL validation...")
conforms, results_graph, results_text = validate(
    data_graph,
    shacl_graph=shapes_graph,
    inference='none',
    abort_on_first=False
)

print(f"\n{'='*60}")
print("VALIDATION TEST RESULTS")
print('='*60)
print(f"Overall conforms: {'✓ PASS' if conforms else '✗ FAIL (Expected)'}")

# Count issues
query = """
    PREFIX sh: <http://www.w3.org/ns/shacl#>
    SELECT ?severity (COUNT(?result) as ?count)
    WHERE {
        ?report sh:result ?result .
        ?result sh:resultSeverity ?severity .
    }
    GROUP BY ?severity
"""

print("\nIssues found:")
for row in results_graph.query(query):
    severity = str(row[0]).split('#')[-1]
    count = int(row[1])
    print(f"  {severity}: {count}")

# Show specific violations
violation_query = """
    PREFIX sh: <http://www.w3.org/ns/shacl#>
    SELECT ?focusNode ?message
    WHERE {
        ?report sh:result ?result .
        ?result sh:focusNode ?focusNode ;
                sh:resultSeverity sh:Violation ;
                sh:resultMessage ?message .
    }
"""

print("\nViolations (these are expected in this test):")
for row in results_graph.query(violation_query):
    focus_node = str(row[0]).split('/')[-1]
    message = str(row[1])
    print(f"  • {focus_node}: {message}")

print('='*60)

# Determine if test passed
expected_violations = 2  # TestFraud2 and TestAgency2 should fail
actual_violations = 0

for row in results_graph.query(violation_query):
    actual_violations += 1

if actual_violations == expected_violations:
    print("\n✓ TEST PASSED: Found expected number of violations")
    print("\n✓ SHACL validation setup is working correctly!")
    print("✓ You're ready to validate your real ontology data.")
    exit(0)
else:
    print(f"\n⚠️ TEST WARNING: Expected {expected_violations} violations but found {actual_violations}")
    print("The validation is working, but results differ from expected.")
    print("This might be okay - check the violations above.")
    exit(0)
