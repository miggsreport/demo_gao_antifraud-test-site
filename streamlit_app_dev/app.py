import streamlit as st
import rdflib
from pathlib import Path
import pandas as pd
import os

# Set page config
st.set_page_config(
    page_title="DEV GAO AFR Test",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Add custom CSS for styling to match AFR site
st.markdown("""
<style>
    /* Header styling - title and badge inline */
    .header-row {
        display: flex;
        align-items: center;
        gap: 15px;
        margin-bottom: 10px;
    }
    .header-title {
        color: #002147;
        font-size: 2rem;
        font-weight: 700;
        margin: 0;
    }
    .dev-badge {
        background-color: #FFD700;
        color: #002147;
        padding: 6px 14px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 0.9rem;
        display: inline-block;
        vertical-align: middle;
    }
    
    /* Section header styling */
    .section-header {
        font-size: 1.3rem;
        font-weight: 600;
        color: #002147;
        margin-bottom: 8px;
    }
    
    /* Tab styling - blue theme with borders */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        margin-top: 5px;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 1.1rem;
        font-weight: 500;
        padding: 10px 16px;
        border: 2px solid #ccc;
        border-radius: 6px 6px 0 0;
        background-color: #f8f8f8;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #e8e8e8;
        border-color: #002147;
    }
    .stTabs [aria-selected="true"] {
        background-color: #fff;
        border-color: #002147;
        border-bottom-color: #fff;
        color: #002147;
    }
    
    /* Button styling to match AFR */
    .stButton > button {
        background-color: #3d6a99;
        color: white;
        border: none;
        padding: 8px 20px;
        border-radius: 4px;
        font-weight: 500;
    }
    .stButton > button:hover {
        background-color: #002147;
        color: white;
    }
    
    /* Success message styling */
    .stSuccess {
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Header with title and DEV badge inline
st.markdown('<div class="header-row"><span class="header-title">The GAO Antifraud Resource</span><span class="dev-badge">TEST SITE</span></div>', unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# TAB CONFIGURATION
# Ordered list of (class_local_name, display_label) tuples
# For AuditProduct, we use rdfs:subClassOf* to include subclasses
# =============================================================================
TAB_CONFIG = [
    ("FederalFraudScheme", "Fraud Scheme Examples"),
    ("FraudEducation", "Fraud Awareness Resources"),
    ("FraudDetection", "Fraud Prevention & Detection Guidance"),
    ("FraudRiskManagementPrinciples", "Fraud Risk Mgmt Principles"),
    ("AuditProduct", "GAO Reports"),
]

# Sidebar for ontology management (collapsed by default via initial_sidebar_state)
with st.sidebar:
    st.header("Ontology Management")
    
    if 'ontology' in st.session_state and st.session_state.ontology:
        st.success("Ontology Loaded")
        st.markdown(f"**File:** {st.session_state.loaded_file}")
        triple_count = len(st.session_state.ontology)
        st.markdown(f"**Triples:** {triple_count:,}")
        st.markdown(f"**Fraud Activities:** {len(st.session_state.fraud_activity_mapping)}")
        
        st.markdown("---")
        st.markdown("**Upload Different Ontology**")
    
    uploaded_file = st.file_uploader(
        "Select file", 
        type=['owl', 'rdf', 'ttl', 'n3', 'jsonld'],
        help="Upload an ontology file",
        label_visibility="collapsed"
    )

# Initialize session state
if 'ontology' not in st.session_state:
    st.session_state.ontology = None
if 'loaded_file' not in st.session_state:
    st.session_state.loaded_file = None
if 'fraud_activity_mapping' not in st.session_state:
    st.session_state.fraud_activity_mapping = {}

@st.cache_resource
def load_ontology_rdflib(file_path):
    try:
        g = rdflib.Graph()
        if file_path.endswith('.ttl'):
            g.parse(file_path, format="turtle")
        elif file_path.endswith('.rdf') or file_path.endswith('.xml'):
            g.parse(file_path, format="xml")
        elif file_path.endswith('.jsonld'):
            g.parse(file_path, format="json-ld")
        else:
            g.parse(file_path)
        return g
    except Exception as e:
        st.error(f"Error loading ontology: {str(e)}")
        return None

def load_fraud_activities(ontology_graph):
    """
    Dynamically query the ontology for direct (top-level) FraudActivity subclasses only.
    Returns a dictionary mapping display labels to class local names.
    """
    sparql_query = """
PREFIX gfo: <https://gaoinnovations.gov/antifraud_resource/howfraudworks/gfo/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?fraudActivity ?fraudActivityLabel
WHERE {
    ?fraudActivity rdfs:subClassOf gfo:FraudActivity .
    ?fraudActivity rdfs:label ?fraudActivityLabel .
}
"""
    try:
        results = list(ontology_graph.query(sparql_query))
        
        fraud_activity_mapping = {}
        for row in results:
            full_uri = str(row.fraudActivity)
            local_name = full_uri.split("/")[-1].split("#")[-1]
            label = str(row.fraudActivityLabel)
            display_label = label.capitalize() if label else local_name
            fraud_activity_mapping[display_label] = local_name
        
        sorted_mapping = dict(sorted(fraud_activity_mapping.items(), key=lambda x: x[0].lower()))
        return sorted_mapping
    
    except Exception as e:
        st.error(f"Error loading fraud activities: {str(e)}")
        return {}


def query_fraud_schemes(ontology_graph, fraud_activity):
    """
    Query for FederalFraudScheme instances related to a specific FraudActivity.
    This is the existing working query - unchanged.
    """
    query = f"""
PREFIX gfo: <https://gaoinnovations.gov/antifraud_resource/howfraudworks/gfo/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX dc: <http://purl.org/dc/elements/1.1/>

SELECT ?individual ?individualName ?description ?fraudNarrative ?isDefinedBy ?objectPropertyName
WHERE {{
    ?individual a gfo:FederalFraudScheme ;
                rdfs:label ?individualName .
    
    OPTIONAL {{ ?individual dc:description ?description . }}
    OPTIONAL {{ ?individual gfo:fraudNarrative ?fraudNarrative . }}
    OPTIONAL {{ ?individual rdfs:isDefinedBy ?isDefinedBy . }}
    
    ?individual a ?restrictionClass .
    ?restrictionClass owl:onProperty ?objectProperty ;
                      owl:someValuesFrom ?relatedClass .
    
    ?relatedClass rdfs:subClassOf* gfo:{fraud_activity} .
    
    BIND(REPLACE(STR(?objectProperty), "^.*/", "") AS ?objectPropertyName)
}}
"""
    return list(ontology_graph.query(query))


def query_resource_instances(ontology_graph, resource_class, fraud_activity):
    """
    Dynamically query for instances of a resource class that address a specific FraudActivity.
    Uses rdfs:subClassOf* to include instances of subclasses (e.g., for AuditProduct).
    
    Parameters:
    - resource_class: The local name of the resource class (e.g., "FraudEducation", "AuditProduct")
    - fraud_activity: The local name of the FraudActivity to filter by
    
    Returns list of query results with individual details.
    """
    query = f"""
PREFIX gfo: <https://gaoinnovations.gov/antifraud_resource/howfraudworks/gfo/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

SELECT DISTINCT ?individual ?individualName ?definition ?website ?isDefinedBy
WHERE {{
    # Find instances that are of this class or any subclass
    ?individual a ?instanceClass .
    ?instanceClass rdfs:subClassOf* gfo:{resource_class} .
    
    ?individual rdfs:label ?individualName .
    
    OPTIONAL {{ ?individual skos:definition ?definition . }}
    OPTIONAL {{ ?individual gfo:hasWebsite ?website . }}
    OPTIONAL {{ ?individual rdfs:isDefinedBy ?isDefinedBy . }}
    
    # Filter by FraudActivity relationship via addresses property
    {{
        # Method 1: Instance has explicit restriction class with addresses property
        ?individual a ?someClass .
        ?someClass owl:onProperty gfo:addresses ;
                   owl:someValuesFrom ?specificFraud .
        
        ?specificFraud rdfs:subClassOf* gfo:{fraud_activity} .
    }}
    UNION
    {{
        # Method 2: Instance's class is a subclass of the FraudActivity
        ?individual a ?resourceSubClass .
        ?resourceSubClass rdfs:subClassOf* gfo:{fraud_activity} .
        
        FILTER(?resourceSubClass != gfo:{resource_class})
    }}
}}
ORDER BY LCASE(STR(?individualName))
"""
    return list(ontology_graph.query(query))


def process_fraud_scheme_results(results):
    """
    Process and deduplicate fraud scheme query results.
    Returns a sorted list of deduplicated scheme dictionaries.
    """
    seen_individuals = {}
    for row in results:
        individual_uri = str(row.individual)
        property_name = str(row.objectPropertyName) if row.objectPropertyName else "unknown"
        
        if individual_uri not in seen_individuals:
            seen_individuals[individual_uri] = {
                'individual': row.individual,
                'individualName': str(row.individualName),
                'description': str(row.description) if row.description else None,
                'fraudNarrative': str(row.fraudNarrative) if row.fraudNarrative else None,
                'isDefinedBy': str(row.isDefinedBy) if row.isDefinedBy else None,
                'objectProperties': set()
            }
        seen_individuals[individual_uri]['objectProperties'].add(property_name)
    
    return sorted(seen_individuals.values(), key=lambda x: x['individualName'].lower())


def display_fraud_schemes(schemes, fraud_activity_label):
    """Display fraud scheme results in expanders."""
    if schemes:
        for i, result in enumerate(schemes):
            scheme_name = result['individualName']
            fraud_description = result['description'] if result['description'] else "No description available"
            fraud_narrative = result['fraudNarrative'] if result['fraudNarrative'] else "No fraud narrative available"
            is_defined_by_url = result['isDefinedBy'] if result['isDefinedBy'] else "No definition source available"
            
            properties_list = sorted(result['objectProperties'])
            properties_display = ", ".join(properties_list)
            
            with st.expander(f"{i+1}. {scheme_name}"):
                st.write(f"**Fraud Description:** {fraud_description}")
                st.write("**Fraud Narrative:**")
                st.text(fraud_narrative)
                st.write(f"**Related to:** {fraud_activity_label}")
                st.write(f"**Linked via:** {properties_display}")
                st.caption(f"Source: {is_defined_by_url}")
    else:
        st.info("No fraud scheme examples found for this fraud activity.")


def display_resource_results(results, fraud_activity_label, empty_message):
    """Display resource query results in expanders."""
    if results:
        for i, row in enumerate(results):
            resource_name = str(row.individualName)
            definition = str(row.definition) if row.definition else "No definition available"
            website = str(row.website) if row.website else ""
            is_defined_by_url = str(row.isDefinedBy) if row.isDefinedBy else "No definition source available"
            
            with st.expander(f"{i+1}. {resource_name}"):
                st.write(f"**Definition:** {definition}")
                if website:
                    st.write(f"**Website:** {website}")
                st.write(f"**Related to:** {fraud_activity_label}")
                st.caption(f"Source: {is_defined_by_url}")
    else:
        st.info(empty_message)


def load_default_ontology():
    script_dir = Path(__file__).parent
    default_ontology_path = script_dir / "gfo_turtle.ttl"
    
    if default_ontology_path.exists():
        try:
            st.session_state.ontology = load_ontology_rdflib(str(default_ontology_path))
            st.session_state.loaded_file = "gfo_turtle.ttl (default)"
            st.session_state.uploaded_file_path = str(default_ontology_path)
            
            if st.session_state.ontology:
                st.session_state.fraud_activity_mapping = load_fraud_activities(st.session_state.ontology)
                return True
        except Exception as e:
            pass
    return False

# Auto-load default ontology
if st.session_state.ontology is None:
    load_default_ontology()

# Handle file upload from sidebar
if uploaded_file is not None and uploaded_file.name != st.session_state.loaded_file:
    temp_path = f"/tmp/{uploaded_file.name}"
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    st.session_state.ontology = load_ontology_rdflib(temp_path)
    st.session_state.loaded_file = uploaded_file.name
    st.session_state.uploaded_file_path = temp_path
    
    if st.session_state.ontology:
        st.session_state.fraud_activity_mapping = load_fraud_activities(st.session_state.ontology)
        st.rerun()

# Main interface
if st.session_state.ontology:
    
    st.markdown('<p class="section-header">Fraud type search</p>', unsafe_allow_html=True)
    
    fraud_activity_mapping = st.session_state.fraud_activity_mapping
    
    if not fraud_activity_mapping:
        st.warning("No fraud activities found in ontology. Please check that the ontology is properly loaded.")
        fraud_activity_mapping = {}
    
    fraud_activity_label = st.selectbox(
        "What type of fraud do you want to combat?",
        options=list(fraud_activity_mapping.keys()),
        help="Choose a fraud type to find all related resources"
    )
    
    fraud_activity = fraud_activity_mapping.get(fraud_activity_label)
    
    if st.button("Search All Resources"):
        if fraud_activity_label and fraud_activity:
            
            # Execute all queries
            try:
                # Query for FederalFraudScheme (existing working query)
                fraud_scheme_results = query_fraud_schemes(st.session_state.ontology, fraud_activity)
                fraud_schemes = process_fraud_scheme_results(fraud_scheme_results)
                
                # Query for each resource class dynamically
                resource_results = {}
                for class_name, display_label in TAB_CONFIG[1:]:  # Skip FederalFraudScheme
                    resource_results[class_name] = query_resource_instances(
                        st.session_state.ontology, 
                        class_name, 
                        fraud_activity
                    )
                
                # Calculate total results
                total_results = len(fraud_schemes) + sum(len(r) for r in resource_results.values())
                
                if total_results > 0:
                    st.success(f"Found {total_results} total resources related to {fraud_activity_label}")
                    
                    # Create tabs with counts in the configured order
                    tab_labels = [
                        f"{TAB_CONFIG[0][1]} ({len(fraud_schemes)})",  # Fraud Scheme Examples
                    ]
                    for class_name, display_label in TAB_CONFIG[1:]:
                        count = len(resource_results[class_name])
                        tab_labels.append(f"{display_label} ({count})")
                    
                    tabs = st.tabs(tab_labels)
                    
                    # Tab 1: Fraud Scheme Examples
                    with tabs[0]:
                        display_fraud_schemes(fraud_schemes, fraud_activity_label)
                    
                    # Remaining tabs: Resource classes
                    for i, (class_name, display_label) in enumerate(TAB_CONFIG[1:], start=1):
                        with tabs[i]:
                            empty_msg = f"No {display_label.lower()} found for this fraud activity."
                            display_resource_results(
                                resource_results[class_name], 
                                fraud_activity_label,
                                empty_msg
                            )
                else:
                    st.info(f"No resources found for {fraud_activity_label}")
                    
            except Exception as e:
                st.error(f"[ERROR] SPARQL query failed: {str(e)}")
                st.info("Make sure your ontology file is properly loaded.")
        else:
            st.warning("Please select a fraud type.")

else:
    st.info("No ontology loaded. Please upload an ontology file using the sidebar.")
    
    st.markdown('<p class="section-header">Getting Started</p>', unsafe_allow_html=True)
    st.markdown("""
    **What this interface provides:**
    
    - **Fraud type search**: Find all types of resources related to specific fraud activities
      - Fraud Scheme Examples
      - Fraud Awareness Resources
      - Fraud Prevention & Detection Guidance
      - Fraud Risk Mgmt Principles
      - GAO Reports
    
    **Supported formats**: OWL, RDF, TTL, N3, JSON-LD
    
    **To begin**: Open the sidebar (arrow at top left) and upload an ontology file.
    """)
