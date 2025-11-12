# Federal Fraud Scheme Instance Data Export

## What You're Getting

The TTL export contains ONLY the instance data (individuals) of Federal Fraud Schemes - NO class definitions, NO property definitions, NO fraud activity relationships.

## Instance Data vs Ontology Structure

### INCLUDED (Instance Data):
```turtle
# Individual fraud scheme instances
gfo:HealthcareBillingScheme_123 a gfo:FederalFraudScheme ;
    rdfs:label "Medicare False Billing Scheme" ;
    dcterms:description "Provider submits inflated claims for services not rendered" ;
    gfo:fraudNarrative "Full narrative text describing the scheme..." .

gfo:StudentLoanScheme_456 a gfo:FederalFraudScheme ;
    rdfs:label "Student Loan Identity Theft" ;
    dcterms:description "Uses stolen identities to obtain student loans" ;
    gfo:fraudNarrative "Detailed description..." .
```

### NOT INCLUDED (Ontology Structure):
```turtle
# Class definitions
gfo:FederalFraudScheme a owl:Class ;
    rdfs:subClassOf gfo:FraudScheme .

# Property definitions  
gfo:involves a owl:ObjectProperty ;
    rdfs:domain gfo:FederalFraudScheme ;
    rdfs:range gfo:FraudActivity .

# Restrictions and axioms
gfo:FederalFraudScheme rdfs:subClassOf [
    a owl:Restriction ;
    owl:onProperty gfo:involves ;
    owl:someValuesFrom gfo:FraudActivity
] .
```

### ALSO NOT INCLUDED (Fraud Activity Relationships):
```turtle
# gfo:involves relationships
gfo:HealthcareBillingScheme_123 gfo:involves gfo:HealthcareFraud .

# Fraud activity references
# Any references to gfo:FraudActivity or its subclasses are excluded
```

## Why This Matters for Your Use Case

You want pure instance data as training examples because:

1. **Each instance = one training example** of how fraud manifests in practice
2. **Instance text fields** (label, description, narrative) are what map to taxonomy terms
3. **Clean data** - no ontology structure noise
4. **No fraud activity bias** - taxonomy mapping based solely on scheme descriptions
5. **Patterns in mappings** will emerge from multiple examples

## What's in Each Instance

Every Federal Fraud Scheme instance will have:

### Always Present:
- rdf:type gfo:FederalFraudScheme
- rdfs:label (name of the scheme)

### Usually Present:
- dcterms:description (short description)
- gfo:fraudNarrative (detailed narrative)

### Never Present:
- gfo:involves (excluded)
- References to gfo:FraudActivity classes (excluded)

## File Structure Example

```turtle
@prefix gfo: <https://gaoinnovations.gov/antifraud_resource/howfraudworks/gfo/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix dcterms: <http://purl.org/dc/terms/> .

gfo:Scheme001 a gfo:FederalFraudScheme ;
    rdfs:label "Healthcare Billing Fraud" ;
    dcterms:description "False claims submitted to Medicare" ;
    gfo:fraudNarrative "Detailed narrative describing the scheme..." .

gfo:Scheme002 a gfo:FederalFraudScheme ;
    rdfs:label "Student Loan Fraud" ;
    dcterms:description "Identity theft to obtain student loans" ;
    gfo:fraudNarrative "Comprehensive description..." .

gfo:Scheme003 a gfo:FederalFraudScheme ;
    rdfs:label "Contract Bid Rigging" ;
    dcterms:description "Collusion among contractors to fix bid prices" ;
    gfo:fraudNarrative "..." .

# ... continues for all N instances in your ontology
```

## CSV Export

The CSV export contains the same data in tabular format:

| gfo_uri | rdfs_label | dc_description | gfo_fraudNarrative |
|---------|------------|----------------|-------------------|
| gfo:Scheme001 | Healthcare Billing Fraud | False claims... | Detailed narrative... |
| gfo:Scheme002 | Student Loan Fraud | Identity theft... | Comprehensive... |
| gfo:Scheme003 | Contract Bid Rigging | Collusion... | ... |

## Using This Data

### Current Purpose: Training Data
1. Each instance is a real-world fraud scheme example
2. Text fields provide rich descriptions for matching
3. You map instances to taxonomy terms
4. Patterns in successful mappings inform rules

### Future Purpose: Feedback Loop
Once mapping patterns are established:
1. New fraud scheme instances are created
2. Automated tagging applies taxonomy terms based on learned rules
3. Manual review validates automated tags
4. Corrections feed back into rule refinement
5. System improves over time

This creates a continuous improvement cycle where instance data serves as both:
- Training input (learn patterns)
- Validation data (test accuracy)
