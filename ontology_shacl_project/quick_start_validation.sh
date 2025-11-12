#!/bin/bash

# Quick Start Script for SHACL Validation
# This script helps you get started with validating your GAO fraud ontology

echo "=========================================="
echo "GAO Fraud Ontology - SHACL Validation"
echo "Quick Start Script"
echo "=========================================="
echo ""

# Check if pyshacl is installed
if ! python3 -c "import pyshacl" 2>/dev/null; then
    echo "⚠️  pyshacl not installed. Installing now..."
    pip install pyshacl rdflib pandas
    echo "✓ Installation complete"
    echo ""
fi

# Default file paths (update these as needed)
DATA_FILE="gfo_turtle.ttl"
SHAPES_FILE="phase1_foundation_shapes.ttl"

# Check if files exist
if [ ! -f "$DATA_FILE" ]; then
    echo "❌ Error: Data file not found: $DATA_FILE"
    echo "Please update DATA_FILE in this script or place gfo_turtle.ttl in current directory"
    exit 1
fi

if [ ! -f "$SHAPES_FILE" ]; then
    echo "❌ Error: Shapes file not found: $SHAPES_FILE"
    echo "Please update SHAPES_FILE in this script or place phase1_foundation_shapes.ttl in current directory"
    exit 1
fi

echo "✓ Found data file: $DATA_FILE"
echo "✓ Found shapes file: $SHAPES_FILE"
echo ""

# Run validation
echo "Running SHACL validation..."
echo ""

python3 validate_ontology.py \
    --data "$DATA_FILE" \
    --shapes "$SHAPES_FILE" \
    --inference none \
    --output-dir validation_reports

# Capture exit code
VALIDATION_EXIT_CODE=$?

echo ""
echo "=========================================="
if [ $VALIDATION_EXIT_CODE -eq 0 ]; then
    echo "✓ Validation PASSED - No issues found!"
else
    echo "⚠️  Validation found issues"
    echo "   Check validation_reports/ for detailed results"
fi
echo "=========================================="
