"""
SHACL Validation Script for GAO Fraud Ontology
Validates instance data against SHACL shapes and produces detailed reports.

Usage:
    python validate_ontology.py --data gfo_turtle.ttl --shapes phase1_foundation_shapes.ttl
    
Or in Jupyter:
    %run validate_ontology.py --data gfo_turtle.ttl --shapes phase1_foundation_shapes.ttl
"""

import argparse
from pathlib import Path
from collections import Counter, defaultdict
import pandas as pd
from datetime import datetime
from pyshacl import validate
import rdflib
from rdflib import Namespace

# Define namespaces
GFO = Namespace("https://gaoinnovations.gov/antifraud_resource/howfraudworks/gfo/")
SH = Namespace("http://www.w3.org/ns/shacl#")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")


class SHACLValidator:
    """Handles SHACL validation and reporting for GAO fraud ontology."""
    
    def __init__(self, data_file, shapes_file, output_dir="validation_reports"):
        self.data_file = Path(data_file)
        self.shapes_file = Path(shapes_file)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.data_graph = None
        self.shapes_graph = None
        self.results_graph = None
        self.conforms = None
        self.results_text = None
        
    def load_graphs(self):
        """Load data and shapes graphs."""
        print("Loading data graph...")
        self.data_graph = rdflib.Graph()
        self.data_graph.parse(str(self.data_file), format="turtle")
        print(f"  ✓ Loaded {len(self.data_graph)} triples from data file")
        
        print("Loading shapes graph...")
        self.shapes_graph = rdflib.Graph()
        self.shapes_graph.parse(str(self.shapes_file), format="turtle")
        print(f"  ✓ Loaded {len(self.shapes_graph)} triples from shapes file")
        
    def run_validation(self, inference='none'):
        """
        Run SHACL validation.
        
        Args:
            inference: 'none', 'rdfs', or 'owlrl'
        """
        print(f"\nRunning SHACL validation (inference={inference})...")
        
        self.conforms, self.results_graph, self.results_text = validate(
            self.data_graph,
            shacl_graph=self.shapes_graph,
            inference=inference,
            abort_on_first=False,
            meta_shacl=False,
            advanced=True,
            allow_warnings=True
        )
        
        print(f"  ✓ Validation complete")
        print(f"  Overall conforms: {self.conforms}")
        
    def get_validation_results(self):
        """Extract detailed validation results from results graph."""
        query = """
            PREFIX sh: <http://www.w3.org/ns/shacl#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            
            SELECT ?focusNode ?focusNodeLabel ?resultPath ?severity ?message ?value ?sourceShape
            WHERE {
                ?report a sh:ValidationReport ;
                        sh:result ?result .
                
                ?result sh:focusNode ?focusNode ;
                        sh:resultSeverity ?severity ;
                        sh:resultMessage ?message .
                
                OPTIONAL { ?result sh:resultPath ?resultPath }
                OPTIONAL { ?result sh:value ?value }
                OPTIONAL { ?result sh:sourceShape ?sourceShape }
                OPTIONAL { ?focusNode rdfs:label ?focusNodeLabel }
            }
            ORDER BY ?severity ?focusNode
        """
        
        results = []
        for row in self.results_graph.query(query):
            results.append({
                'focus_node': str(row.focusNode),
                'focus_node_label': str(row.focusNodeLabel) if row.focusNodeLabel else "N/A",
                'result_path': str(row.resultPath).split('#')[-1].split('/')[-1] if row.resultPath else "N/A",
                'severity': str(row.severity).split('#')[-1],
                'message': str(row.message),
                'value': str(row.value) if row.value else "N/A",
                'source_shape': str(row.sourceShape).split('#')[-1].split('/')[-1] if row.sourceShape else "N/A"
            })
        
        return results
    
    def generate_summary(self, results):
        """Generate summary statistics."""
        if not results:
            return {
                'total_issues': 0,
                'by_severity': {},
                'by_class': {},
                'by_property': {}
            }
        
        df = pd.DataFrame(results)
        
        # Extract class name from focus node URI
        df['class_name'] = df['focus_node'].str.split('/').str[-1]
        
        summary = {
            'total_issues': len(results),
            'by_severity': df['severity'].value_counts().to_dict(),
            'by_property': df['result_path'].value_counts().head(10).to_dict(),
            'by_class': df['class_name'].value_counts().head(10).to_dict()
        }
        
        return summary
    
    def print_summary_report(self, results, summary):
        """Print a formatted summary report to console."""
        print("\n" + "="*80)
        print("SHACL VALIDATION SUMMARY REPORT")
        print("="*80)
        print(f"Data file: {self.data_file}")
        print(f"Shapes file: {self.shapes_file}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Overall conforms: {'✓ YES' if self.conforms else '✗ NO'}")
        print("="*80)
        
        if summary['total_issues'] == 0:
            print("\n✓ All validation checks passed! No issues found.")
            return
        
        print(f"\nTotal issues found: {summary['total_issues']}")
        
        # By severity
        print("\n" + "-"*80)
        print("Issues by Severity:")
        print("-"*80)
        for severity, count in sorted(summary['by_severity'].items()):
            icon = "🔴" if severity == "Violation" else "⚠️" if severity == "Warning" else "ℹ️"
            print(f"  {icon} {severity}: {count}")
        
        # By property
        print("\n" + "-"*80)
        print("Top 10 Properties with Issues:")
        print("-"*80)
        for prop, count in summary['by_property'].items():
            print(f"  {prop}: {count}")
        
        # By class
        print("\n" + "-"*80)
        print("Top 10 Classes with Issues:")
        print("-"*80)
        for class_name, count in summary['by_class'].items():
            print(f"  {class_name}: {count}")
        
        # Sample violations
        print("\n" + "-"*80)
        print("Sample Issues (first 10 violations):")
        print("-"*80)
        
        df = pd.DataFrame(results)
        violations = df[df['severity'] == 'Violation'].head(10)
        
        for idx, row in violations.iterrows():
            print(f"\n  {idx+1}. {row['focus_node_label']} ({row['class_name']})")
            print(f"     Property: {row['result_path']}")
            print(f"     Message: {row['message']}")
            if row['value'] != "N/A":
                print(f"     Value: {row['value']}")
        
        print("\n" + "="*80)
        print(f"Detailed results saved to: {self.output_dir}/")
        print("="*80 + "\n")
    
    def save_detailed_report(self, results, summary):
        """Save detailed reports to files."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save full results as CSV
        if results:
            df = pd.DataFrame(results)
            csv_file = self.output_dir / f"validation_results_{timestamp}.csv"
            df.to_csv(csv_file, index=False)
            print(f"✓ Saved detailed results to: {csv_file}")
            
            # Save by severity
            for severity in ['Violation', 'Warning', 'Info']:
                severity_df = df[df['severity'] == severity]
                if not severity_df.empty:
                    severity_file = self.output_dir / f"validation_{severity.lower()}s_{timestamp}.csv"
                    severity_df.to_csv(severity_file, index=False)
                    print(f"✓ Saved {severity}s to: {severity_file}")
        
        # Save summary as JSON
        import json
        summary_file = self.output_dir / f"validation_summary_{timestamp}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"✓ Saved summary to: {summary_file}")
        
        # Save RDF validation report
        rdf_file = self.output_dir / f"validation_report_{timestamp}.ttl"
        self.results_graph.serialize(rdf_file, format='turtle')
        print(f"✓ Saved RDF validation report to: {rdf_file}")
    
    def get_instance_counts_by_class(self):
        """Count instances of each class being validated."""
        shapes_query = """
            PREFIX sh: <http://www.w3.org/ns/shacl#>
            SELECT DISTINCT ?targetClass
            WHERE {
                ?shape sh:targetClass ?targetClass .
            }
        """
        
        print("\n" + "-"*80)
        print("Instance Counts for Validated Classes:")
        print("-"*80)
        
        for row in self.shapes_graph.query(shapes_query):
            target_class = row.targetClass
            class_name = str(target_class).split('/')[-1]
            
            # Count instances in data graph
            count_query = f"""
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                SELECT (COUNT(DISTINCT ?instance) as ?count)
                WHERE {{
                    ?instance rdf:type <{target_class}> .
                }}
            """
            
            count_result = list(self.data_graph.query(count_query))
            count = int(count_result[0][0]) if count_result else 0
            
            print(f"  {class_name}: {count} instances")
        
        print("-"*80)
    
    def run_full_validation(self, inference='none', save_reports=True):
        """Run complete validation workflow."""
        print("\n" + "="*80)
        print("GAO FRAUD ONTOLOGY - SHACL VALIDATION")
        print("="*80 + "\n")
        
        # Load graphs
        self.load_graphs()
        
        # Show instance counts
        self.get_instance_counts_by_class()
        
        # Run validation
        self.run_validation(inference=inference)
        
        # Get results
        results = self.get_validation_results()
        summary = self.generate_summary(results)
        
        # Print summary
        self.print_summary_report(results, summary)
        
        # Save reports
        if save_reports:
            self.save_detailed_report(results, summary)
        
        return self.conforms, results, summary


def main():
    parser = argparse.ArgumentParser(
        description='Validate GAO fraud ontology against SHACL shapes'
    )
    parser.add_argument(
        '--data',
        required=True,
        help='Path to ontology data file (TTL format)'
    )
    parser.add_argument(
        '--shapes',
        required=True,
        help='Path to SHACL shapes file (TTL format)'
    )
    parser.add_argument(
        '--inference',
        default='none',
        choices=['none', 'rdfs', 'owlrl'],
        help='Type of inference to apply before validation'
    )
    parser.add_argument(
        '--output-dir',
        default='validation_reports',
        help='Directory for output reports'
    )
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Do not save detailed reports (console output only)'
    )
    
    args = parser.parse_args()
    
    # Run validation
    validator = SHACLValidator(
        data_file=args.data,
        shapes_file=args.shapes,
        output_dir=args.output_dir
    )
    
    conforms, results, summary = validator.run_full_validation(
        inference=args.inference,
        save_reports=not args.no_save
    )
    
    # Exit code: 0 if conforms, 1 if doesn't conform
    import sys
    sys.exit(0 if conforms else 1)


if __name__ == "__main__":
    main()
