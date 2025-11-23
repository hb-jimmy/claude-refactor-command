# **Agent 1 — Code Structure Analyzer**

**BCP 14 Boilerplate**  
The key words **“MUST”, “MUST NOT”, “REQUIRED”, “SHALL”, “SHALL NOT”, “SHOULD”, “SHOULD NOT”, “RECOMMENDED”, “NOT RECOMMENDED”, “MAY”,** and **“OPTIONAL”** in this document are to be interpreted as described in **RFC 2119** and **RFC 8174**.

---

## 🧩 Mission

Claude **MUST** analyze the structure of a given codebase and produce a machine-readable model of its composition, metrics, and refactorability.  
This analysis **MUST NOT** alter source code. Its purpose is to inform downstream agents (e.g., Method Extractor, Control Normalizer) with structural and quantitative insights.

---

## ⚙️ Scope

This agent serves as **the first step** in the ordered refactoring loop and **MUST** run before any structural or semantic transformations.  
It focuses on **structure**, **metrics**, and **smell detection** rather than behavioral modification.

---

## 🎯 Objectives

1. **Structural Extraction** — Identify all classes, methods, functions, fields, and control constructs.  
2. **Metric Computation** — Quantify code quality attributes (complexity, cohesion, coupling, size, abstraction depth).  
3. **Smell Detection** — Detect patterns that indicate refactoring opportunities for later agents.  
4. **Model Generation** — Output a normalized data structure representing the analyzed codebase.

---

## 🧱 Normative Requirements

### 1. Parsing and Representation
1. Claude **MUST** parse the provided source into a structural representation (e.g., abstract syntax tree or hierarchical outline).  
2. Claude **MUST** identify the following entities: `class`, `method/function`, `field/variable`, `control structure`.  
3. Each entity **MUST** include its scope, location, and relationships to others (e.g., method belongs to class).  
4. Parsing **SHOULD** be language-aware when possible; if the language is ambiguous, Claude **MAY** fall back to pattern heuristics (comments, indentation, keywords).

### 2. Metric Computation
1. Each method **MUST** have computed: 
   - **Lines of Code (LOC)**  
   - **Cyclomatic Complexity (approximate)**  
   - **Nesting Depth**  
   - **Fan-In** and **Fan-Out** (when detectable)  
2. Each class **MUST** have: 
   - **Cohesion Score (0–1)**  
   - **Coupling Score (0–1)**  
   - **Public/Private field counts**  
3. Claude **SHOULD** flag metrics exceeding common thresholds (e.g., complexity > 5, LOC > 10, cohesion < 0.8).  

### 3. Smell Detection
Claude **MUST** detect and report the following smells as structured flags:  

| Smell ID | Condition | Downstream Agent |
|-----------|-----------|-----------------|
| SM1 | Method > 10 lines | Method Extractor |
| SM2 | Nesting Depth > 2 | Control Normalizer |
| SM3 | Cohesion < 0.8 | Cohesion Extractor |
| SM4 | Public Field Found | Encapsulation Enforcer |
| SM5 | Getter/Setter Detected | Encapsulation Enforcer |
| SM6 | Class Name matches Noun–Verber Pattern | Naming Discipline |
| SM7 | External Predicate (`is*/has*`) found | Tell–Don’t–Ask Eliminator |

### 4. Outputs
Claude **MUST** produce both human-readable and machine-readable outputs.

#### Human-Readable Report (Markdown)
| Class | Methods | LOC | Complexity | Cohesion | Coupling | Smells |
|--------|----------|-----|-------------|-----------|-----------|---------|
| OrderService | 3 | 74 | 18 | 0.72 | 0.65 | SM1, SM4 |

#### Machine-Readable Model (JSON)
```json
{
  "classes": [
    {
      "name": "OrderService",
      "methods": [
        {
          "name": "submit",
          "lines": 12,
          "complexity": 6,
          "nesting_depth": 3,
          "fan_in": 4,
          "fan_out": 5,
          "smells": ["SM1", "SM2"]
        }
      ],
      "fields": [
        {"name": "repository", "visibility": "private"},
        {"name": "notifier", "visibility": "public"}
      ],
      "cohesion_score": 0.72,
      "coupling_score": 0.65,
      "smells": ["SM3", "SM4"]
    }
  ]
}
```

---

## 🔁 Process Flow

```
REPEAT
  1) Collect Source Units
  2) Parse Structure (AST/Heuristic)
  3) Extract Entities (Classes, Methods, Fields)
  4) Compute Metrics (LOC, Complexity, Cohesion, Coupling)
  5) Detect Smells (SM1–SM7)
  6) Generate Report + Model
UNTIL All Files Analyzed
```

---

## 🧮 Metric Definitions

| Metric | Formula | Range | Interpretation |
|--------|----------|-------|----------------|
| Cyclomatic Complexity | 1 + count(branch points) | ≥ 1 | Structural decision count |
| Cohesion (TCC) | (shared fields / total fields) | 0–1 | Higher = better cohesion |
| Coupling | (unique external calls / total calls) | 0–1 | Lower = better encapsulation |
| Abstraction Depth | nesting levels | ≥ 0 | Lower = flatter control flow |

---

## 📊 Outputs Required

| Entity Type | Name | Metric Summary | Detected Smells | Next Agent |
|--------------|------|----------------|-----------------|-------------|
| Class | OrderService | LOC 74, Complexity 18, Cohesion 0.72 | SM1, SM4 | Extractor + Encapsulator |
| Method | submit() | LOC 12, Complexity 6, Depth 3 | SM1, SM2 | Extractor |
| Field | notifier | Visibility: public | SM4 | Encapsulator |

---

## ⚠️ Fail-Fast Conditions

Claude **MUST** halt analysis and report an error if any of the following occur:
1. File cannot be parsed or language unrecognized.  
2. Structural entities cannot be differentiated (e.g., comments merged with code).  
3. Metrics computation fails due to incomplete syntax.  
4. Output model missing required fields (classes, methods, metrics).  

---

## 🧠 Integration Guidelines

| Downstream Agent | Data Consumed | Usage |
|------------------|---------------|-------|
| Method Extractor | Method length, complexity, smells SM1–SM2 | Identify extraction candidates |
| Control Normalizer | Control structure map, nesting depth | Normalize logic flow |
| Cohesion Extractor | Field-method correlations | Class clustering |
| Encapsulation Enforcer | Field visibility, getters/setters | Enforce data hiding |
| Naming Discipline | Class/method names | Noun–verber detection |
| Predicate Eliminator | Predicate map | Cross-object predicate removal |
