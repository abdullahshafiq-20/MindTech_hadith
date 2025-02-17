// Find all narrators who studied under a specific teacher
MATCH (student:Narrator)-[r:NARRATED_FROM]->(teacher:Narrator {full_name: 'Imam Malik'})
RETURN student.full_name, r.year, r.location;

// Find the travel history of a narrator
MATCH (n:Narrator {narrator_id: 'N001'})-[r:TRAVELED_TO]->(t:TravelCity)
RETURN n.full_name, t.year_visited;

// Find all scholarly evaluations of a narrator
MATCH (n:Narrator)-[r:EVALUATED_BY]->(evaluator:Narrator)
WHERE n.narrator_id = 'N001'
RETURN evaluator.full_name, r.evaluation, r.year;

// Find complete isnad chain for a hadith
MATCH path = (n:Narrator)-[:NARRATED_FROM*]->(original:Narrator)
WHERE n.narrator_id = 'N001'
RETURN path; 