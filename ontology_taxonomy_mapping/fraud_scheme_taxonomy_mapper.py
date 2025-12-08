#!/usr/bin/env python3
"""
Federal Fraud Scheme to GAO Product Taxonomy Mapper

This script:
1. Exports Federal Fraud Schemes from the GFO ontology
2. Loads the GAO Product Taxonomy
3. Maps fraud schemes to taxonomy terms using keyword-based semantic matching
4. Outputs results with confidence scores for manual review

Author: Generated for GAO Antifraud Resource project
Date: 2025
"""

import rdflib
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, SKOS, DCTERMS, OWL
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import re
from typing import List, Dict, Tuple, Set
import warnings
warnings.filterwarnings('ignore')

# Try to import sentence transformers for better semantic matching
try:
    from sentence_transformers import SentenceTransformer, util
    SENTENCE_TRANSFORMERS_AVAILABLE = True
    print(" Using sentence-transformers for semantic similarity")
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print(" sentence-transformers not available. Using basic keyword matching.")
    print("  Install with: pip install sentence-transformers")

# Define namespaces
GFO = Namespace("https://gaoinnovations.gov/antifraud_resource/howfraudworks/gfo/")
GAO_PT = Namespace("https://poolparty.clstaxonomy.com/GAOProductTaxonomyMain/")
GAO_ONTO = Namespace("https://poolparty.clstaxonomy.com/GAO-Products-Ontology/")


class FraudSchemeExporter:
    """Handles extraction of Federal Fraud Scheme data from the GFO ontology"""
    
    def __init__(self, ontology_path: str):
        """
        Initialize the exporter with the path to the GFO ontology file
        
        Args:
            ontology_path: Path to the GFO ontology file (TTL format)
        """
        self.g = Graph()
        print(f"\n Loading GFO ontology from: {ontology_path}")
        
        # Bind namespaces
        self.g.bind("gfo", GFO)
        self.g.bind("rdfs", RDFS)
        self.g.bind("dcterms", DCTERMS)
        self.g.bind("skos", SKOS)
        
        # Parse the ontology
        self.g.parse(ontology_path, format="turtle")
        print(f"   Loaded {len(self.g)} triples")
        
    def extract_fraud_schemes(self) -> pd.DataFrame:
        """
        Extract all Federal Fraud Scheme instances from the ontology
        
        Returns:
            DataFrame with fraud scheme information
        """
        print("\nExtracting Federal Fraud Schemes...")
        
        query = """
        PREFIX gfo: <https://gaoinnovations.gov/antifraud_resource/howfraudworks/gfo/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX dcterms: <http://purl.org/dc/terms/>
        
        SELECT DISTINCT ?scheme ?label ?description ?narrative
        WHERE {
            # Get all instances of FederalFraudScheme
            ?scheme a gfo:FederalFraudScheme .
            
            # Required: label
            ?scheme rdfs:label ?label .
            
            # Optional: description
            OPTIONAL { ?scheme dcterms:description ?description . }
            
            # Optional: fraud narrative
            OPTIONAL { ?scheme gfo:fraudNarrative ?narrative . }
        }
        ORDER BY ?label
        """
        
        results = list(self.g.query(query))
        print(f"   Found {len(results)} fraud scheme records")
        
        # Process results into a DataFrame
        data = []
        for row in results:
            data.append({
                'gfo_uri': str(row.scheme),
                'rdfs_label': str(row.label) if row.label else '',
                'dc_description': str(row.description) if row.description else '',
                'gfo_fraudNarrative': str(row.narrative) if row.narrative else ''
            })
        
        df = pd.DataFrame(data)
        
        # Create a combined text field for matching
        df['combined_text'] = (
            df['rdfs_label'] + ' ' + 
            df['dc_description'] + ' ' + 
            df['gfo_fraudNarrative']
        ).str.lower()
        
        return df
        
        # Create a combined text field for matching
        df['combined_text'] = (
            df['rdfs_label'] + ' ' + 
            df['dc_description'] + ' ' + 
            df['gfo_fraudNarrative'] + ' ' +
            df['fraud_activity_label']
        ).str.lower()
        
        return df
    
    def export_to_csv(self, df: pd.DataFrame, output_path: str):
        """Export fraud schemes to CSV"""
        print(f"\n Exporting fraud schemes to CSV: {output_path}")
        df.to_csv(output_path, index=False)
        print(f"   Exported {len(df)} schemes")
    
    def export_to_ttl(self, output_path: str):
        """
        Export ONLY Federal Fraud Scheme instance data to a TTL file.
        This exports individual fraud scheme instances (not class definitions,
        property definitions, or ontology structure).
        Excludes gfo:involves and fraud activity relationships.
        """
        print(f"\nExporting fraud scheme instances to TTL: {output_path}")
        
        # Create a new graph with only fraud scheme instance data
        fraud_graph = Graph()
        fraud_graph.bind("gfo", GFO)
        fraud_graph.bind("rdfs", RDFS)
        fraud_graph.bind("dcterms", DCTERMS)
        fraud_graph.bind("skos", SKOS)
        
        # Query for ONLY instance data (individuals), not class/property definitions
        # Explicitly exclude gfo:involves and fraud activity information
        query = """
        PREFIX gfo: <https://gaoinnovations.gov/antifraud_resource/howfraudworks/gfo/>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        
        CONSTRUCT {
            ?scheme ?p ?o .
            ?o ?p2 ?o2 .
        }
        WHERE {
            # Get only instances (individuals) of FederalFraudScheme
            ?scheme a gfo:FederalFraudScheme .
            
            # Exclude cases where the scheme itself is a class
            FILTER NOT EXISTS { ?scheme a owl:Class }
            
            # Get all properties of the instance
            ?scheme ?p ?o .
            
            # EXCLUDE gfo:involves property
            FILTER(?p != gfo:involves)
            
            # EXCLUDE any references to FraudActivity
            FILTER NOT EXISTS {
                ?o rdf:type/rdfs:subClassOf* gfo:FraudActivity .
            }
            
            # Include blank node details if they exist
            OPTIONAL {
                ?o ?p2 ?o2 .
                FILTER(isBlank(?o))
            }
        }
        """
        
        fraud_graph = self.g.query(query).graph
        fraud_graph.serialize(destination=output_path, format='turtle')
        
        # Count actual instances (not total triples)
        instance_count = len(list(fraud_graph.subjects(RDF.type, GFO.FederalFraudScheme)))
        print(f"   Exported {instance_count} fraud scheme instances")
        print(f"   Total triples: {len(fraud_graph)}")
        print(f"   (Excluding gfo:involves and fraud activity relationships)")


class TaxonomyLoader:
    """Handles loading and parsing of the GAO Product Taxonomy"""
    
    def __init__(self, taxonomy_path: str):
        """
        Initialize the taxonomy loader
        
        Args:
            taxonomy_path: Path to the GAO Product Taxonomy TTL file
        """
        self.g = Graph()
        print(f"\n Loading GAO Product Taxonomy from: {taxonomy_path}")
        
        # Bind namespaces
        self.g.bind("skos", SKOS)
        self.g.bind("dcterms", DCTERMS)
        self.g.bind("gao_pt", GAO_PT)
        self.g.bind("gao_onto", GAO_ONTO)
        
        # Parse the taxonomy
        self.g.parse(taxonomy_path, format="turtle")
        print(f"   Loaded {len(self.g)} triples")
    
    def extract_taxonomy_terms(self) -> pd.DataFrame:
        """
        Extract all taxonomy concepts with their metadata
        
        Returns:
            DataFrame with taxonomy term information
        """
        print("\n Extracting taxonomy terms...")
        
        query = """
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX gao_onto: <https://poolparty.clstaxonomy.com/GAO-Products-Ontology/>
        
        SELECT DISTINCT ?concept ?prefLabel ?topConceptOf ?genericId ?broaderConcept ?broaderLabel
        WHERE {
            ?concept a skos:Concept .
            ?concept skos:prefLabel ?prefLabel .
            
            OPTIONAL { ?concept skos:topConceptOf ?topConceptOf . }
            OPTIONAL { ?concept gao_onto:Generic-ID ?genericId . }
            
            # Try to find broader terms
            OPTIONAL {
                ?concept gao_onto:isNonPTOf ?broaderConcept .
                ?broaderConcept skos:prefLabel ?broaderLabel .
            }
        }
        ORDER BY ?prefLabel
        """
        
        results = list(self.g.query(query))
        print(f"   Found {len(results)} taxonomy terms")
        
        data = []
        for row in results:
            data.append({
                'taxonomy_uri': str(row.concept),
                'skos_prefLabel': str(row.prefLabel),
                'skos_topConceptOf': str(row.topConceptOf) if row.topConceptOf else '',
                'generic_id': str(row.genericId) if row.genericId else '',
                'broader_term_uri': str(row.broaderConcept) if row.broaderConcept else '',
                'broader_term_label': str(row.broaderLabel) if row.broaderLabel else ''
            })
        
        df = pd.DataFrame(data)
        
        # Create searchable text
        df['search_text'] = (
            df['skos_prefLabel'] + ' ' + 
            df['broader_term_label']
        ).str.lower()
        
        return df


class SemanticMatcher:
    """Handles semantic matching between fraud schemes and taxonomy terms"""
    
    def __init__(self, use_transformers: bool = SENTENCE_TRANSFORMERS_AVAILABLE):
        """
        Initialize the matcher
        
        Args:
            use_transformers: Whether to use sentence transformers for semantic matching
        """
        self.use_transformers = use_transformers
        
        if self.use_transformers:
            print("\n Loading semantic similarity model...")
            # Use a lightweight but effective model
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            print("   Model loaded successfully")
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity between two text strings
        
        Args:
            text1: First text string
            text2: Second text string
            
        Returns:
            Similarity score between 0 and 1
        """
        if self.use_transformers:
            # Use sentence transformer embeddings
            embeddings = self.model.encode([text1, text2])
            similarity = util.cos_sim(embeddings[0], embeddings[1]).item()
            return max(0.0, min(1.0, similarity))
        else:
            # Fallback to simple keyword overlap
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            
            if not words1 or not words2:
                return 0.0
            
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            return len(intersection) / len(union) if union else 0.0
    
    def find_matches(
        self, 
        fraud_schemes: pd.DataFrame, 
        taxonomy: pd.DataFrame,
        top_n: int = 5,
        min_score: float = 0.15
    ) -> pd.DataFrame:
        """
        Find the best taxonomy matches for each fraud scheme
        
        Args:
            fraud_schemes: DataFrame of fraud schemes
            taxonomy: DataFrame of taxonomy terms
            top_n: Number of top matches to return per scheme
            min_score: Minimum similarity score to include
            
        Returns:
            DataFrame with matches and confidence scores
        """
        print(f"\n Finding taxonomy matches for {len(fraud_schemes)} fraud schemes...")
        print(f"   Searching across {len(taxonomy)} taxonomy terms")
        print(f"   Returning top {top_n} matches with score >= {min_score}")
        
        if self.use_transformers:
            print("\n   Encoding taxonomy terms...")
            taxonomy_embeddings = self.model.encode(
                taxonomy['search_text'].tolist(), 
                show_progress_bar=True
            )
        
        all_matches = []
        
        for idx, scheme_row in fraud_schemes.iterrows():
            if (idx + 1) % 10 == 0:
                print(f"   Processing scheme {idx + 1}/{len(fraud_schemes)}...")
            
            scheme_text = scheme_row['combined_text']
            
            if self.use_transformers:
                # Encode the scheme text
                scheme_embedding = self.model.encode([scheme_text])[0]
                
                # Calculate similarities with all taxonomy terms
                similarities = util.cos_sim(scheme_embedding, taxonomy_embeddings)[0].numpy()
            else:
                # Calculate similarities using keyword overlap
                similarities = np.array([
                    self.calculate_similarity(scheme_text, tax_text)
                    for tax_text in taxonomy['search_text']
                ])
            
            # Get top N matches above threshold
            top_indices = np.argsort(similarities)[::-1][:top_n]
            
            for rank, tax_idx in enumerate(top_indices, 1):
                score = float(similarities[tax_idx])
                
                if score >= min_score:
                    match = {
                        # Fraud scheme info
                        'scheme_uri': scheme_row['gfo_uri'],
                        'scheme_label': scheme_row['rdfs_label'],
                        'scheme_description': scheme_row['dc_description'],
                        'scheme_narrative': scheme_row['gfo_fraudNarrative'],
                        
                        # Taxonomy match info
                        'taxonomy_uri': taxonomy.iloc[tax_idx]['taxonomy_uri'],
                        'taxonomy_prefLabel': taxonomy.iloc[tax_idx]['skos_prefLabel'],
                        'taxonomy_topConceptOf': taxonomy.iloc[tax_idx]['skos_topConceptOf'],
                        'taxonomy_genericId': taxonomy.iloc[tax_idx]['generic_id'],
                        'broader_term_uri': taxonomy.iloc[tax_idx]['broader_term_uri'],
                        'broader_term_label': taxonomy.iloc[tax_idx]['broader_term_label'],
                        
                        # Match quality metrics
                        'match_rank': rank,
                        'confidence_score': round(score, 4),
                        'matching_method': 'semantic_transformer' if self.use_transformers else 'keyword_overlap'
                    }
                    
                    all_matches.append(match)
        
        matches_df = pd.DataFrame(all_matches)
        
        if len(matches_df) > 0:
            print(f"\n    Found {len(matches_df)} total matches")
            print(f"   Average confidence: {matches_df['confidence_score'].mean():.3f}")
            print(f"   Score range: {matches_df['confidence_score'].min():.3f} - {matches_df['confidence_score'].max():.3f}")
        else:
            print("\n    No matches found above threshold")
        
        return matches_df


def main():
    """Main execution function"""
    
    print("=" * 80)
    print("Federal Fraud Scheme → GAO Product Taxonomy Mapper")
    print("=" * 80)
    
    # Configuration
    C:\Projects\gao-ontology\ontology_taxonomy_mapping\pp_scheme_maingaoproducttaxonomy_gaoproducttaxonomy.ttl = "gfo_turtle.ttl"  # Adjust path as needed
    TAXONOMY_PATH = "/mnt/user-data/uploads/1761595961204_pasted-content-1761595961204.txt"  # The uploaded taxonomy
    OUTPUT_DIR = Path("/mnt/user-data/outputs")
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Step 1: Export Federal Fraud Schemes
    print("\n" + "=" * 80)
    print("STEP 1: Extract Federal Fraud Schemes")
    print("=" * 80)
    
    exporter = FraudSchemeExporter(GFO_ONTOLOGY_PATH)
    fraud_schemes_df = exporter.extract_fraud_schemes()
    
    # Export to CSV
    schemes_csv = OUTPUT_DIR / f"federal_fraud_schemes_{timestamp}.csv"
    exporter.export_to_csv(fraud_schemes_df, str(schemes_csv))
    
    # Export to TTL
    schemes_ttl = OUTPUT_DIR / f"federal_fraud_schemes_{timestamp}.ttl"
    exporter.export_to_ttl(str(schemes_ttl))
    
    # Step 2: Load GAO Product Taxonomy
    print("\n" + "=" * 80)
    print("STEP 2: Load GAO Product Taxonomy")
    print("=" * 80)
    
    taxonomy_loader = TaxonomyLoader(TAXONOMY_PATH)
    taxonomy_df = taxonomy_loader.extract_taxonomy_terms()
    
    # Step 3: Perform Semantic Matching
    print("\n" + "=" * 80)
    print("STEP 3: Match Fraud Schemes to Taxonomy")
    print("=" * 80)
    
    matcher = SemanticMatcher()
    matches_df = matcher.find_matches(
        fraud_schemes_df, 
        taxonomy_df,
        top_n=5,  # Return top 5 matches per scheme
        min_score=0.15  # Minimum confidence threshold
    )
    
    # Step 4: Export Results
    print("\n" + "=" * 80)
    print("STEP 4: Export Results")
    print("=" * 80)
    
    if len(matches_df) > 0:
        # Main output: mappings with suggested matches
        mappings_csv = OUTPUT_DIR / f"fraud_scheme_taxonomy_mappings_{timestamp}.csv"
        matches_df.to_csv(mappings_csv, index=False)
        print(f"\n Saved mappings to: {mappings_csv}")
        
        # Create a summary by fraud scheme
        summary = matches_df.groupby('scheme_label').agg({
            'taxonomy_prefLabel': lambda x: ' | '.join(x.head(3)),
            'confidence_score': 'max',
            'match_rank': 'count'
        }).rename(columns={'match_rank': 'num_matches'})
        
        summary_csv = OUTPUT_DIR / f"mapping_summary_{timestamp}.csv"
        summary.to_csv(summary_csv)
        print(f" Saved summary to: {summary_csv}")
        
        # Create a human-readable report
        print("\n" + "=" * 80)
        print("SAMPLE MAPPINGS (Top 3 schemes by confidence)")
        print("=" * 80)
        
        top_schemes = matches_df.nlargest(3, 'confidence_score')
        for _, row in top_schemes.iterrows():
            print(f"\n Fraud Scheme: {row['scheme_label']}")
            print(f"   Matched to: {row['taxonomy_prefLabel']}")
            print(f"   Confidence: {row['confidence_score']:.3f}")
            print(f"   Broader Term: {row['broader_term_label']}")
    
    print("\n" + "=" * 80)
    print(" PROCESSING COMPLETE")
    print("=" * 80)
    print(f"\nOutput files saved to: {OUTPUT_DIR}")
    print("\nNext steps:")
    print("1. Review the mappings CSV and adjust confidence thresholds as needed")
    print("2. Manually verify high-confidence matches")
    print("3. Flag uncertain matches for expert review")
    print("4. Use approved mappings to develop rule-based matching")


if __name__ == "__main__":
    main()
