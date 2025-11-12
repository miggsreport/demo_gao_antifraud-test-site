"""
RDF Ontology Mapping & Gap Analysis Tool - FIXED VERSION
Compares labels between fraud ontology (rdfs:label/skos:prefLabel) 
and GAO Product Taxonomy (skos:prefLabel) with fuzzy matching
"""

import rdflib
from rdflib import Graph, Namespace, RDF, RDFS, OWL
from rdflib.namespace import SKOS
import pandas as pd
from difflib import SequenceMatcher
from collections import defaultdict
import re

# Configuration
SIMILARITY_THRESHOLD = 0.75
TOP_N_MATCHES = 5

def normalize_label(label):
    """Normalize labels for better matching"""
    if not label:
        return ""
    normalized = str(label).lower().strip()
    normalized = re.sub(r'[^\w\s]', '', normalized)
    normalized = re.sub(r'\s+', ' ', normalized)
    return normalized

def calculate_similarity(str1, str2):
    """Calculate similarity ratio between two strings"""
    return SequenceMatcher(None, normalize_label(str1), normalize_label(str2)).ratio()

def extract_fraud_concepts(graph, fraud_ns):
    """Extract concepts from fraud ontology with labels and hierarchy"""
    concepts = {}
    
    for subj in graph.subjects(RDF.type, OWL.Class):
        if str(subj).startswith(str(fraud_ns)):
            labels = set()
            parent_classes = []
            
            # Get rdfs:label
            for label in graph.objects(subj, RDFS.label):
                labels.add(str(label))
            
            # Get skos:prefLabel
            for label in graph.objects(subj, SKOS.prefLabel):
                labels.add(str(label))
            
            # Get parent classes
            for parent in graph.objects(subj, RDFS.subClassOf):
                if isinstance(parent, rdflib.term.URIRef):
                    parent_classes.append(str(parent))
            
            if labels:
                concepts[str(subj)] = {
                    'labels': list(labels),
                    'parents': parent_classes,
                    'primary_label': list(labels)[0]
                }
    
    return concepts

def extract_gao_concepts(graph):
    """Extract concepts from GAO taxonomy with skos:prefLabel"""
    concepts = {}
    
    for subj in graph.subjects(RDF.type, SKOS.Concept):
        labels = []
        
        for label in graph.objects(subj, SKOS.prefLabel):
            labels.append(str(label))
        
        related = [str(r) for r in graph.objects(subj, SKOS.related)]
        broader = [str(b) for b in graph.objects(subj, SKOS.broader)]
        narrower = [str(n) for n in graph.objects(subj, SKOS.narrower)]
        
        if labels:
            concepts[str(subj)] = {
                'labels': labels,
                'primary_label': labels[0],
                'related': related,
                'broader': broader,
                'narrower': narrower
            }
    
    return concepts

def find_matches(fraud_concepts, gao_concepts, threshold=SIMILARITY_THRESHOLD, top_n=TOP_N_MATCHES):
    """Find fuzzy matches between fraud and GAO concepts"""
    mappings = []
    
    for fraud_uri, fraud_data in fraud_concepts.items():
        matches = []
        
        for fraud_label in fraud_data['labels']:
            for gao_uri, gao_data in gao_concepts.items():
                for gao_label in gao_data['labels']:
                    similarity = calculate_similarity(fraud_label, gao_label)
                    
                    if similarity >= threshold:
                        matches.append({
                            'gao_uri': gao_uri,
                            'gao_label': gao_label,
                            'similarity': similarity,
                            'fraud_label_used': fraud_label
                        })
        
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        top_matches = matches[:top_n]
        
        if top_matches:
            for match in top_matches:
                mappings.append({
                    'fraud_uri': fraud_uri,
                    'fraud_label': fraud_data['primary_label'],
                    'fraud_label_matched': match['fraud_label_used'],
                    'gao_uri': match['gao_uri'],
                    'gao_label': match['gao_label'],
                    'similarity_score': round(match['similarity'], 3),
                    'fraud_parents': '; '.join(fraud_data['parents'][:3])
                })
    
    return mappings

def identify_gaps(fraud_concepts, gao_concepts, mappings_df):
    """
    Identify concepts without mappings in both directions
    FIX: Properly handles empty DataFrames and ensures all unmapped concepts are captured
    """
    
    # Get mapped URIs - fixed to handle empty DataFrame properly
    if mappings_df is not None and len(mappings_df) > 0:
        mapped_fraud = set(mappings_df['fraud_uri'].tolist())
        mapped_gao = set(mappings_df['gao_uri'].tolist())
        print(f"Debug: Found {len(mapped_fraud)} mapped fraud URIs, {len(mapped_gao)} mapped GAO URIs")
    else:
        mapped_fraud = set()
        mapped_gao = set()
        print("Debug: No mappings found, all concepts will be marked as unmapped")
    
    # Fraud concepts without GAO matches
    unmapped_fraud = []
    for uri, data in fraud_concepts.items():
        if uri not in mapped_fraud:
            unmapped_fraud.append({
                'uri': uri,
                'label': data['primary_label'],
                'all_labels': '; '.join(data['labels']),
                'parents': '; '.join(data['parents'][:3]) if data['parents'] else 'None'
            })
    
    print(f"Debug: Identified {len(unmapped_fraud)} unmapped fraud concepts")
    
    # GAO concepts without fraud matches
    unmapped_gao = []
    for uri, data in gao_concepts.items():
        if uri not in mapped_gao:
            unmapped_gao.append({
                'uri': uri,
                'label': data['primary_label'],
                'all_labels': '; '.join(data['labels']),
                'broader': '; '.join(data.get('broader', [])) if data.get('broader') else 'None'
            })
    
    print(f"Debug: Identified {len(unmapped_gao)} unmapped GAO concepts")
    
    return unmapped_fraud, unmapped_gao

def main(fraud_file, gao_file, output_prefix='ontology_mapping'):
    """Main execution function"""
    
    print("="*60)
    print("RDF ONTOLOGY MAPPING & GAP ANALYSIS")
    print("="*60)
    
    print(f"\nLoading fraud ontology from: {fraud_file}")
    fraud_graph = Graph()
    fraud_graph.parse(fraud_file, format='turtle')
    print(f"✓ Loaded {len(fraud_graph)} triples")
    
    print(f"\nLoading GAO taxonomy from: {gao_file}")
    gao_graph = Graph()
    gao_graph.parse(gao_file, format='turtle')
    print(f"✓ Loaded {len(gao_graph)} triples")
    
    # Detect fraud namespace
    fraud_ns = None
    for ns_prefix, ns_uri in fraud_graph.namespaces():
        if 'gfo' in ns_prefix or 'fraud' in str(ns_uri).lower():
            fraud_ns = Namespace(ns_uri)
            break
    
    if not fraud_ns:
        ns_counts = defaultdict(int)
        for subj in fraud_graph.subjects(RDF.type, OWL.Class):
            ns = str(subj).rsplit('/', 1)[0] + '/'
            ns_counts[ns] += 1
        fraud_ns = Namespace(max(ns_counts, key=ns_counts.get))
    
    print(f"✓ Fraud namespace: {fraud_ns}")
    
    print("\nExtracting fraud concepts...")
    fraud_concepts = extract_fraud_concepts(fraud_graph, fraud_ns)
    print(f"✓ Found {len(fraud_concepts)} fraud concepts with labels")
    
    print("\nExtracting GAO concepts...")
    gao_concepts = extract_gao_concepts(gao_graph)
    print(f"✓ Found {len(gao_concepts)} GAO concepts with labels")
    
    if len(fraud_concepts) == 0:
        print("⚠ WARNING: No fraud concepts extracted! Check namespace detection.")
    if len(gao_concepts) == 0:
        print("⚠ WARNING: No GAO concepts extracted! Check if file contains SKOS concepts.")
    
    print(f"\nFinding fuzzy matches (threshold={SIMILARITY_THRESHOLD}, top_n={TOP_N_MATCHES})...")
    mappings = find_matches(fraud_concepts, gao_concepts, SIMILARITY_THRESHOLD, TOP_N_MATCHES)
    
    if mappings:
        mappings_df = pd.DataFrame(mappings)
        print(f"✓ Found {len(mappings)} candidate mappings")
    else:
        mappings_df = pd.DataFrame()
        print("⚠ No mappings found above similarity threshold")
    
    print("\nIdentifying coverage gaps...")
    unmapped_fraud, unmapped_gao = identify_gaps(fraud_concepts, gao_concepts, mappings_df)
    
    # Save results with error handling
    print("\n" + "="*60)
    print("SAVING RESULTS")
    print("="*60)
    
    try:
        if not mappings_df.empty:
            filename = f'{output_prefix}_mappings.csv'
            mappings_df.to_csv(filename, index=False)
            print(f"✓ Mappings: {filename} ({len(mappings_df)} rows)")
        else:
            print("⚠ No mappings to save (threshold may be too high)")
        
        if unmapped_fraud:
            filename = f'{output_prefix}_gaps_fraud.csv'
            pd.DataFrame(unmapped_fraud).to_csv(filename, index=False)
            print(f"✓ Fraud gaps: {filename} ({len(unmapped_fraud)} concepts)")
        else:
            print("⚠ No unmapped fraud concepts (all matched or no concepts extracted)")
        
        if unmapped_gao:
            filename = f'{output_prefix}_gaps_gao.csv'
            pd.DataFrame(unmapped_gao).to_csv(filename, index=False)
            print(f"✓ GAO gaps: {filename} ({len(unmapped_gao)} concepts)")
        else:
            print("⚠ No unmapped GAO concepts (all matched or no concepts extracted)")
            
    except Exception as e:
        print(f"✗ Error saving files: {e}")
        raise
    
    # Summary statistics
    print("\n" + "="*60)
    print("SUMMARY STATISTICS")
    print("="*60)
    print(f"Total fraud concepts:       {len(fraud_concepts)}")
    print(f"Total GAO concepts:         {len(gao_concepts)}")
    print(f"Mappings found:             {len(mappings)}")
    
    if not mappings_df.empty:
        print(f"Fraud concepts mapped:      {len(set(mappings_df['fraud_uri']))}")
        print(f"GAO concepts mapped:        {len(set(mappings_df['gao_uri']))}")
        print(f"Avg similarity score:       {mappings_df['similarity_score'].mean():.3f}")
        print(f"Median similarity score:    {mappings_df['similarity_score'].median():.3f}")
    else:
        print(f"Fraud concepts mapped:      0")
        print(f"GAO concepts mapped:        0")
    
    print(f"Unmapped fraud concepts:    {len(unmapped_fraud)}")
    print(f"Unmapped GAO concepts:      {len(unmapped_gao)}")
    
    # Coverage percentages
    if len(fraud_concepts) > 0:
        fraud_coverage = (len(set(mappings_df['fraud_uri']) if not mappings_df.empty else [])) / len(fraud_concepts) * 100
        print(f"Fraud coverage:             {fraud_coverage:.1f}%")
    if len(gao_concepts) > 0:
        gao_coverage = (len(set(mappings_df['gao_uri']) if not mappings_df.empty else [])) / len(gao_concepts) * 100
        print(f"GAO coverage:               {gao_coverage:.1f}%")
    
    print("="*60)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python ontology_mapper.py <fraud_ontology.ttl> <gao_taxonomy.ttl> [output_prefix]")
        print("\nConfiguration:")
        print(f"  Similarity threshold: {SIMILARITY_THRESHOLD}")
        print(f"  Top matches per concept: {TOP_N_MATCHES}")
        print("\nOutput files:")
        print("  {prefix}_mappings.csv - Matched concepts with similarity scores")
        print("  {prefix}_gaps_fraud.csv - Fraud concepts without GAO matches")
        print("  {prefix}_gaps_gao.csv - GAO concepts without fraud matches")
        sys.exit(1)
    
    fraud_file = sys.argv[1]
    gao_file = sys.argv[2]
    output_prefix = sys.argv[3] if len(sys.argv) > 3 else 'ontology_mapping'
    
    main(fraud_file, gao_file, output_prefix)