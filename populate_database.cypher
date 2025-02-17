// First create Places
MERGE (makkah:Place {
    place_id: 'P001',
    name: 'Makkah',
    type: 'City',
    region: 'Hijaz'
});

MERGE (madinah:Place {
    place_id: 'P002',
    name: 'Madinah',
    type: 'City',
    region: 'Hijaz'
});

MERGE (egypt:Place {
    place_id: 'P004',
    name: 'Egypt',
    type: 'Country',
    region: 'North Africa'
});

// Create Narrators
MERGE (abu_hurayrah:Narrator {
    narrator_id: 'N001',
    full_name: 'Abu Hurayrah',
    aliases: ['Abd al-Rahman ibn Sakhr', 'Abu Hirr'],
    birth_year: 603,
    death_year: 681,
    era: 'Companion',
    did_travel_for_hadith: true,
    known_tadlis: false,
    scholarly_reliability: ['Thiqa', 'Highly Reliable']
});

MERGE (imam_malik:Narrator {
    narrator_id: 'N002',
    full_name: 'Imam Malik',
    aliases: ['Malik ibn Anas'],
    birth_year: 711,
    death_year: 795,
    era: 'Tabi\' al-Tabi\'in',
    did_travel_for_hadith: true,
    known_tadlis: false,
    scholarly_reliability: ['Thiqa', 'Highly Reliable']
});

// Create Hadiths
MERGE (hadith1:Hadith {
    hadith_id: 'H001',
    label: 'Sahih',
    topic: 'Faith',
    subtopic: 'Intentions & Sincerity'
});

MERGE (hadith2:Hadith {
    hadith_id: 'H002',
    label: 'Hasan',
    topic: 'Purification',
    subtopic: 'Ritual Cleanliness'
});

// Create TravelCity records
MERGE (travel1:TravelCity {
    travel_id: 'T001',
    year_visited: 610
});

MERGE (travel2:TravelCity {
    travel_id: 'T003',
    year_visited: 770
});

// Create Birth/Death Relationships
MATCH (n:Narrator {narrator_id: 'N001'})
MATCH (p:Place {place_id: 'P001'})
MERGE (n)-[:BORN_IN {year: 603}]->(p);

MATCH (n:Narrator {narrator_id: 'N001'})
MATCH (p:Place {place_id: 'P002'})
MERGE (n)-[:DIED_IN {year: 681}]->(p);

MATCH (n:Narrator {narrator_id: 'N002'})
MATCH (p:Place {place_id: 'P002'})
MERGE (n)-[:BORN_IN {year: 711}]->(p);

MATCH (n:Narrator {narrator_id: 'N002'})
MATCH (p:Place {place_id: 'P002'})
MERGE (n)-[:DIED_IN {year: 795}]->(p);

// Create Travel Relationships
MATCH (n:Narrator {narrator_id: 'N001'})
MATCH (t:TravelCity {travel_id: 'T001'})
MERGE (n)-[:TRAVELED_TO {year_visited: 610}]->(t);

MATCH (n:Narrator {narrator_id: 'N002'})
MATCH (t:TravelCity {travel_id: 'T003'})
MERGE (n)-[:TRAVELED_TO {year_visited: 770}]->(t);

// Create Narration Relationships
MATCH (n1:Narrator {narrator_id: 'N001'})
MATCH (n2:Narrator {narrator_id: 'N002'})
MERGE (n1)-[:NARRATED_FROM {
    hadith_id: 'H001',
    year: 650,
    location: 'P002',
    method: 'direct'
}]->(n2);

// Create Evaluation Relationships
MATCH (n1:Narrator {narrator_id: 'N001'})
MATCH (n2:Narrator {narrator_id: 'N002'})
MERGE (n1)-[:EVALUATED_BY {
    evaluation: 'Trustworthy',
    year: 650,
    context: 'General evaluation'
}]->(n2);

// Create Primary Location Relationships
MATCH (n:Narrator {narrator_id: 'N001'})
MATCH (p:Place {place_id: 'P002'})
MERGE (n)-[:PRIMARY_LOCATION]->(p);

MATCH (n:Narrator {narrator_id: 'N002'})
MATCH (p:Place {place_id: 'P002'})
MERGE (n)-[:PRIMARY_LOCATION]->(p);

MATCH (n:Narrator {narrator_id: 'N002'})
MATCH (p:Place {place_id: 'P004'})
MERGE (n)-[:PRIMARY_LOCATION]->(p);

// Create Hadith Reporting Relationships
MATCH (n:Narrator {narrator_id: 'N001'})
MATCH (h:Hadith {hadith_id: 'H001'})
MERGE (n)-[:REPORTED_HADITH]->(h);

MATCH (n:Narrator {narrator_id: 'N002'})
MATCH (h:Hadith {hadith_id: 'H002'})
MERGE (n)-[:REPORTED_HADITH]->(h); 