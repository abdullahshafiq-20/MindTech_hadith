// Create a narrator with all relationships
MERGE (n:Narrator {
    narrator_id: 'N001',
    full_name: 'Abu Hurayrah',
    aliases: ['Abd al-Rahman ibn Sakhr', 'Abu Hirr'],
    birth_year: 603,
    death_year: 681,
    era: 'Companion',
    did_travel_for_hadith: true,
    known_tadlis: false,
    scholarly_reliability: ['Thiqa', 'Highly Reliable']
})

// Create birthplace
MERGE (bp:Place {place_id: 'P001', name: 'Makkah', type: 'City'})
CREATE (n)-[:BORN_IN {year: 603}]->(bp)

// Create death place
MERGE (dp:Place {place_id: 'P002', name: 'Madinah', type: 'City'})
CREATE (n)-[:DIED_IN {year: 681}]->(dp)

// Create travel history
MERGE (t:TravelCity {travel_id: 'T001', year_visited: 610})
CREATE (n)-[:TRAVELED_TO {year_visited: 610}]->(t)

// Create hadith relationship
MERGE (h:Hadith {
    hadith_id: 'H001',
    label: 'Sahih',
    topic: 'Faith',
    subtopic: 'Intentions & Sincerity'
})
CREATE (n)-[:REPORTED_HADITH]->(h); 