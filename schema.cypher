// Create constraints for unique IDs
CREATE CONSTRAINT narrator_id IF NOT EXISTS
FOR (n:Narrator) REQUIRE n.narrator_id IS UNIQUE;

CREATE CONSTRAINT place_id IF NOT EXISTS
FOR (p:Place) REQUIRE p.place_id IS UNIQUE;

CREATE CONSTRAINT hadith_id IF NOT EXISTS
FOR (h:Hadith) REQUIRE h.hadith_id IS UNIQUE;

CREATE CONSTRAINT travel_id IF NOT EXISTS
FOR (t:TravelCity) REQUIRE t.travel_id IS UNIQUE;

// Create indexes for frequent lookups
CREATE INDEX narrator_name IF NOT EXISTS
FOR (n:Narrator) ON (n.full_name);

CREATE INDEX place_name IF NOT EXISTS
FOR (p:Place) ON (p.name);

// Node creation patterns
// Place nodes - Example with literal values
CREATE (p:Place {
    place_id: "MECCA_001",
    name: "Mecca",
    type: "city",
    region: "Hijaz"
});

// Narrator nodes
CREATE (n:Narrator {
    narrator_id: "NAR_001",
    full_name: "Abu Hurayrah",
    aliases: ["Abd al-Rahman ibn Sakhr"],
    birth_year: 603,
    death_year: 681,
    era: "Companion",
    did_travel_for_hadith: true,
    known_tadlis: false,
    scholarly_reliability: "Highly Reliable"
});

// Additional example nodes needed for relationships
CREATE (n:Narrator {
    narrator_id: "NAR_002",
    full_name: "Abdullah ibn Umar",
    aliases: ["Ibn Umar"],
    birth_year: 614,
    death_year: 693,
    era: "Companion",
    did_travel_for_hadith: true,
    known_tadlis: false,
    scholarly_reliability: "Highly Reliable"
});

CREATE (p:Place {
    place_id: "MEDINA_001",
    name: "Medina",
    type: "city",
    region: "Hijaz"
});

// Hadith nodes
CREATE (h:Hadith {
    hadith_id: "HAD_001",
    label: "Sahih",
    topic: "Prayer",
    subtopic: "Fajr Prayer"
});

// TravelCity nodes
CREATE (t:TravelCity {
    travel_id: "TRAV_001",
    year_visited: 650
});

// Relationship patterns
// Narrator relationships - Example with literal values
MATCH (n1:Narrator {narrator_id: "NAR_001"})
MATCH (n2:Narrator {narrator_id: "NAR_002"})
CREATE (n1)-[:NARRATED_FROM {
    hadith_id: "HAD_001",
    year: 650,
    location: "Medina",
    method: "Direct Hearing"
}]->(n2);

// Birth/Death relationships
MATCH (n:Narrator {narrator_id: "NAR_001"})
MATCH (p:Place {place_id: "MECCA_001"})
CREATE (n)-[:BORN_IN {year: 603}]->(p);

MATCH (n:Narrator {narrator_id: "NAR_001"})
MATCH (p:Place {place_id: "MEDINA_001"})
CREATE (n)-[:DIED_IN {year: 681}]->(p);

// Travel relationships
MATCH (n:Narrator {narrator_id: "NAR_001"})
MATCH (t:TravelCity {travel_id: "TRAV_001"})
CREATE (n)-[:TRAVELED_TO {year_visited: 650}]->(t);

// Evaluation relationships
MATCH (n1:Narrator {narrator_id: "NAR_002"})
MATCH (n2:Narrator {narrator_id: "NAR_001"})
CREATE (n1)-[:EVALUATED_BY {
    evaluation: "Trustworthy",
    year: 670,
    context: "General Assessment"
}]->(n2); 